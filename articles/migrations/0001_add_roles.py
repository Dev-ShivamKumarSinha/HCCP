# Generated by Django 4.2.18 on 2025-01-28 16:30

from django.db import migrations
from django.contrib.auth.models import User

def create_admin_user(self, schema_editor):
    User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='adminpassword'
    )

class Migration(migrations.Migration):
    
    dependencies = [
    ]

    operations = [
        migrations.RunPython(create_admin_user)
    ]
