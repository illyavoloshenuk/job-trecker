from django.urls import path
from . import views

urlpatterns = [

    path('job-tracker/', views.job_tracker_page, name='job_tracker'),

    path('auth/register/', views.register_view, name='register'),
    path('auth/login/', views.login_view, name='login'),
    path('auth/logout/', views.logout_view, name='logout'),
    path('auth/me/', views.me_view, name='me'),

    path('applications/', views.application_home, name='application_home'),
    path('applications/<int:id>/', views.application_detail, name='application_detail'),

    path('', views.user_home, name='user_home'),
    path('<int:id>/', views.user_detail, name='user_detail'),



]