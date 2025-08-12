# ===== authentication/admin.py =====
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """
    Admin configuration for CustomUser model
    """
    list_display = ['email', 'username', 'first_name', 'last_name', 'is_verified', 'download_count', 'date_joined']
    list_filter = ['is_verified', 'is_staff', 'is_active', 'date_joined', 'last_download']
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering = ['-date_joined']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('bio', 'avatar', 'date_of_birth', 'is_verified')
        }),
        ('API Usage', {
            'fields': ('download_count', 'last_download'),
            'classes': ['collapse']
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('email', 'first_name', 'last_name', 'bio')
        }),
    )