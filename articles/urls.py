from django.urls import path
from .views import RegisterView, LoginView, ArticleCreateView, ArticleDetailView, CollaboratorManagementView, RollbackArticleView, ListSoftDeletedArticlesView, UserActivityLogView, UserEditAnalyticsView, ArticleHistoryView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('articles/', ArticleCreateView.as_view(), name='create-article'),
    path('articles/<int:pk>', ArticleDetailView.as_view(), name='article-detail'),
    path('articles/<int:pk>/rollback', RollbackArticleView.as_view(), name='article-rollback'),
    path('articles/<int:pk>/collaborators', CollaboratorManagementView.as_view(), name='manage-collaborators'), 
    path('articles/deleted', ListSoftDeletedArticlesView.as_view(), name='soft-deleted-article'),
    path('articles/<int:pk>/history/', ArticleHistoryView.as_view(), name='article-history'),
    path('analytics/user-activity', UserActivityLogView.as_view(), name='user-activity'),
    path('analytics/user-edits', UserEditAnalyticsView.as_view(), name='user-edit-analytics'),
]