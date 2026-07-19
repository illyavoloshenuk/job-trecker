from django.urls import path
from . import views

urlpatterns = [
    path('applications/', views.application_home, name='application_home'),
    path('applications/<int:id>/', views.application_detail, name='application_detail'),

    path('', views.user_home, name='user_home'),
    path('<int:id>/', views.user_detail, name='user_detail'),

]