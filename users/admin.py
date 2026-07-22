from django.contrib import admin
from .models import UserProfile, JobApplication


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email')
    search_fields = ('name', 'email')


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'title',
        'company',
        'status',
        'label_color',
        'is_favorite',
        'salary',
        'location',
        'date_applied',
        'contact_name',
    )
    list_filter = ('status', 'label_color', 'is_favorite', 'company', 'date_applied', 'location')
    search_fields = ('title', 'company', 'contact_name', 'notes', 'location', 'salary')