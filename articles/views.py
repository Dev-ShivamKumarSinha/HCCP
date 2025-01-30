from django.shortcuts import render
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError, NotFound
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import RegisterSerializer, ArticleSerializer
from .models import Article, ArticleVersion, UserActivityLog
from django.contrib.auth.models import User
from django.core.cache import cache
from .permissions import IsAuthorOrAdmin, IsAdmin
from django.utils import timezone
from datetime import timedelta
from .services.queries import get_latest_article_version, get_user_activity_logs, get_user_edit_counts, get_article_history

# Create your views here.
# Register User
class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data = request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"detail": "User registered successfully!"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Login User
class LoginView(TokenObtainPairView):
    pass

# Create Article
class ArticleCreateView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]

    # Apply 'manage_collaborators' throttle for adding/removing collaborators.
    def get_throttle_scope(self):
        return "create_article"
    
    def post(self, request):
        try:
            serializer = ArticleSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(author=request.user)  # Automatically set the author
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# View or Edit Article
class ArticleDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAuthorOrAdmin]
    throttle_classes = [ScopedRateThrottle]

    # Dynamically assign the throttle scope based on HTTP method
    def get_throttle_scope(self):
        if self.request.method == "GET":
            return "view_article"  # Throttle scope for GET requests
        elif self.request.method == "PUT":
            return "edit_article"  # Throttle scope for PUT requests
        elif self.request.method == "DELETE":
            return "delete_article"  # Throttle scope for PUT requests
        return None  # Default behavior for other methods

    def get(self, request, pk):
        cache_key = f"article_{pk}"
        cached_article = cache.get(cache_key)

        if cached_article:
            return Response(cached_article)  # Return from cache
        try:
            article = Article.objects.get(pk=pk)
            
            # If the article is soft-deleted, check rollback period
            if article.is_deleted:
                if article.deleted_at is None:
                    raise NotFound({"error": "Article deleted_at timestamp missing. Possible data inconsistency."})

                rollback_deadline = article.deleted_at + timedelta(hours=24)
                
                if timezone.now() > rollback_deadline:
                    # Rollback period expired, permanently delete the article
                    article.delete()
                    raise NotFound({"error": "Article has been permanently deleted."})
                else:
                    # Rollback period still active, inform user
                    return Response({
                        "message": "This article has been deleted but can be rolled back within 24 hours.",
                        "rollback_deadline": rollback_deadline.strftime("%Y-%m-%d %H:%M:%S")
                    })

            # If the article is not deleted, return the article details
            self.check_object_permissions(request, article)

            serializer = ArticleSerializer(article)
            latest_version = get_latest_article_version(pk)
            response_data = serializer.data
            response_data["latest_version"] = latest_version

            cache.set(cache_key, response_data, timeout=3600)  # Cache for 1 hour

            return Response(response_data)

        except Article.DoesNotExist:
            raise NotFound({"error": "Article not found or has been permanently deleted."})

    def put(self, request, pk):
        try:
            article = Article.objects.get(pk=pk)
            self.check_object_permissions(request, article)
            serializer = ArticleSerializer(article, data=request.data, partial=True)
            if serializer.is_valid():
                # Create a new article version before updating
                latest_version_number = ArticleVersion.objects.filter(article=article).count() + 1

                ArticleVersion.objects.create(
                    article=article,
                    version_number=latest_version_number,
                    body=article.body,  # Store the current body before update
                    updated_by=request.user
                )

                serializer.save()
                 # Log the user activity
                UserActivityLog.objects.create(user=request.user, action="edit", article=article)

                # Invalidate cache
                cache.delete(f"article_{pk}")  # Delete cached article details
                cache.delete(f"article_history_{pk}")  # Delete cached article history

                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Article.DoesNotExist:
            return Response({"error": "Article not found"}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        try:
            article = Article.objects.get(pk=pk)
            self.check_object_permissions(request, article)
            if article.is_deleted:
                return Response({"error": "Article is already deleted."}, status=400)

            article.is_deleted = True
            article.deleted_at = timezone.now()  # Record the deletion timestamp
            article.save()

            # Log the delete action
            UserActivityLog.objects.create(user=request.user, action="delete", article=article)

            # Invalidate cache
            cache.delete(f"article_{pk}")  # Delete cached article details
            cache.delete(f"article_history_{pk}")  # Delete cached article history

            return Response({"detail": "Article marked as deleted. You can roll back within 24 hours."}, status=204)
        except Article.DoesNotExist:
            return Response({"error": "Article not found"}, status=status.HTTP_404_NOT_FOUND)

# Manage Collaborators for article
class CollaboratorManagementView(APIView):
    permission_classes = [IsAuthenticated, IsAuthorOrAdmin]
    throttle_classes = [ScopedRateThrottle]

    # Apply 'manage_collaborators' throttle for adding/removing collaborators.# 
    def get_throttle_scope(self):
        return "manage_collaborators"

    
    # Add or remove collaborators for a specific article.  
    def post(self, request, pk):
        try:
            article = Article.objects.get(pk=pk)
            self.check_object_permissions(request, article)
            
            collaborator_username = request.data.get("collaborator")
            action = request.data.get("action")  # "add" or "remove"

            if not collaborator_username:
                raise ValidationError({"error": "Collaborator username is required."})

            collaborator = User.objects.get(username=collaborator_username)

            if action == "add":
                if collaborator in article.collaborators.all():
                    return Response({"detail": f"User '{collaborator_username}' is already a collaborator."}, status=400)
                article.collaborators.add(collaborator)
                return Response({"detail": f"User '{collaborator_username}' added as a collaborator."}, status=200)

            elif action == "remove":
                if collaborator not in article.collaborators.all():
                    return Response({"detail": f"User '{collaborator_username}' is not a collaborator."}, status=400)
                article.collaborators.remove(collaborator)
                return Response({"detail": f"User '{collaborator_username}' removed as a collaborator."}, status=200)

            else:
                return Response({"error": "Invalid action. Use 'add' or 'remove'."}, status=400)

        except Article.DoesNotExist:
            return Response({"error": "Article not found."}, status=404)
        except User.DoesNotExist:
            return Response({"error": "Collaborator user not found."}, status=404)

# Rollback Article after soft delete      
class RollbackArticleView(APIView):
    permission_classes = [IsAuthenticated, IsAuthorOrAdmin]
    throttle_classes = [ScopedRateThrottle]

    # Apply 'rollback_article' throttle.
    def get_throttle_scope(self):
        return "rollback_article"

    def post(self, request, pk):
        try:
            article = Article.objects.get(pk=pk)
            self.check_object_permissions(request, article)

            if not article.is_deleted:
                return Response({"error": "Article is not deleted."}, status=400)

            # Check if rollback period has expired
            time_since_deletion = timezone.now() - article.deleted_at
            if time_since_deletion > timedelta(hours=24):
                return Response({"error": "Rollback period has expired."}, status=400)

            # Restore the article
            article.is_deleted = False
            article.deleted_at = None
            article.save()

            # Log rollback
            UserActivityLog.objects.create(user=request.user, action="rollback", article=article)

            # Invalidate cache
            cache.delete(f"article_{pk}")  # Delete cached article details
            cache.delete(f"article_history_{pk}")  # Delete cached article history

            return Response({"detail": "Article successfully restored."}, status=200)

        except Article.DoesNotExist:
            return Response({"error": "Article not found."}, status=404)
        
# List soft deleted article to author and admin
class ListSoftDeletedArticlesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # If user is an admin, show all soft-deleted articles
            if request.user.groups.filter(name="Admin").exists():
                articles = Article.objects.filter(is_deleted=True)
            else:
                # Regular users only see their own deleted articles
                articles = Article.objects.filter(is_deleted=True, author=request.user)

            serializer = ArticleSerializer(articles, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# List article version history
class ArticleHistoryView(APIView):
    permission_classes = [IsAuthenticated]  # Any authenticated user can view history

    def get(self, request, pk):
        try:
            history = get_article_history(pk)
            return Response({"history": history})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# List user activity logs
class UserActivityLogView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]  # Restrict to 'Admin' group

    def get(self, request):
        try:
            logs = get_user_activity_logs()
            return Response(logs)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# List user edit analytics
class UserEditAnalyticsView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]  # Restrict to Admin group

    def get(self, request, pk):
        try:
            cache_key = f"article_history_{pk}"
            cached_history = cache.get(cache_key)

            if cached_history:
                return Response({"history": cached_history})

            history = get_article_history(pk)
            cache.set(cache_key, history, timeout=3600)  # Cache for 1 hour

            return Response({"history": history})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)