from django.contrib import admin
from .models import Article, ArticleVersion, UserActivityLog

# Register your models here.
admin.site.register(Article)
admin.site.register(ArticleVersion)
admin.site.register(UserActivityLog)