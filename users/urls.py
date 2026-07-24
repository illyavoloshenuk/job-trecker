from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_page, name='landing'),

    path('login/', views.login_page, name='login_page'),
    path('register/', views.register_page, name='register_page'),
    path('dashboard/', views.dashboard_page, name='dashboard_page'),
    path('applications-page/', views.applications_page, name='applications_page'),
    path('filters/', views.filters_page, name='filters_page'),
    path('profile/', views.profile_page, name='profile_page'),

    path('job-tracker/', views.job_tracker_page, name='job_tracker'),

    path('auth/register/', views.register_view, name='register'),
    path('auth/login/', views.login_view, name='login'),
    path('auth/logout/', views.logout_view, name='logout'),
    path('auth/me/', views.me_view, name='me'),

    path('auth/password-reset/request-code/', views.request_password_reset_code_view, name='request_password_reset_code'),
    path('auth/password-reset/verify-code/', views.verify_password_reset_code_view, name='verify_password_reset_code'),
    path('auth/password-reset/confirm/', views.confirm_password_reset_view, name='confirm_password_reset'),

    path('profile-data/', views.profile_view, name='profile_view'),
    path('support-request/', views.support_request_view, name='support_request'),

    path('resumes/', views.resume_home, name='resume_home'),
    path('resumes/<int:id>/', views.resume_detail, name='resume_detail'),

    path('applications/', views.application_home, name='application_home'),
    path('applications/<int:id>/', views.application_detail, name='application_detail'),

    path('favorites/', views.favorites_home, name='favorites_home'),
    path('favorites/<int:id>/', views.favorite_detail, name='favorite_detail'),
]