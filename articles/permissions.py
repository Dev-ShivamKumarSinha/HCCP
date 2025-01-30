from rest_framework.permissions import BasePermission

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='Admin').exists()

class IsAuthorOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        # Admins or the article's author have full access
        return obj.author == request.user or request.user.groups.filter(name='Admin').exists()

class IsCollaborator(BasePermission):
    def has_object_permission(self, request, view, obj):
        # Collaborators can only view or suggest changes
        return obj.collaborators.filter(id=request.user.id).exists()
