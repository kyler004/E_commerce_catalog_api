from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import EmailOTP, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ('email', 'is_active', 'email_verified_at', 'is_staff')
    list_filter = ('is_active', 'is_staff', 'email_verified_at')
    ordering = ('email',)
    search_fields = ('email',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Verification', {'fields': ('email_verified_at',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'is_active', 'is_staff'),
        }),
    )


@admin.register(EmailOTP)
class EmailOTPAdmin(admin.ModelAdmin):
    list_display = ('user', 'purpose', 'expires_at', 'attempts', 'is_used', 'created_at')
    list_filter = ('purpose', 'is_used')
    readonly_fields = ('user', 'purpose', 'code_hash', 'expires_at', 'attempts', 'is_used', 'created_at')
