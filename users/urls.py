from django.urls import path
from . import views

urlpatterns = [
    path('', views.user_home, name='user_home'),
    path('<int:id>/', views.user_detail, name='user_detail'),


]