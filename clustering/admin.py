from django.contrib import admin
from django.contrib.auth.models import User

User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@example.com', 'admin')
# Register your models here.
