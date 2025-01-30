from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Article

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

class ArticleSerializer(serializers.ModelSerializer):
    author = serializers.ReadOnlyField(source='author.username')
    collaborators = serializers.SlugRelatedField(
        many=True,
        slug_field='username',
        queryset=User.objects.all(), 
        required=False
    )

    class Meta:
        model = Article
        fields = ['id', 'title', 'body', 'tags', 'author', 'collaborators', 'created_at', 'updated_at']
        read_only_fields = ['author', 'created_at', 'updated_at']
