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

    path('profile-data/', views.profile_view, name='profile_view'),

    path('applications/', views.application_home, name='application_home'),
    path('applications/<int:id>/', views.application_detail, name='application_detail'),

    path('favorites/', views.favorites_home, name='favorites_home'),
    path('favorites/<int:id>/', views.favorite_detail, name='favorite_detail'),

    path('users/', views.user_home, name='user_home'),
    path('users/<int:id>/', views.user_detail, name='user_detail'),
]