from django.contrib import admin

from .models import UserProfile, JobApplication, Resume, PasswordResetCode


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'avatar')
    search_fields = ('user__username', 'user__email')


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'title',
        'company',
        'status',
        'label_color',
        'date_applied',
        'is_favorite',
    )
    list_filter = ('status', 'label_color', 'company', 'date_applied', 'is_favorite')
    search_fields = ('title', 'company', 'contact_name', 'notes', 'location', 'salary', 'user__username')


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'title', 'created_at', 'updated_at')
    search_fields = ('title', 'notes', 'user__username', 'user__email')
    list_filter = ('created_at', 'updated_at')


@admin.register(PasswordResetCode)
class PasswordResetCodeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'email', 'code', 'is_verified', 'created_at', 'expires_at')
    search_fields = ('email', 'code', 'user__username')
    list_filter = ('is_verified', 'created_at', 'expires_at')