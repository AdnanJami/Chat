from django.urls import path
from . import views

urlpatterns = [
    path('', views.create_or_join, name='index'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),  
    path('logout/', views.logout_view, name='logout'),
    path('leave/', views.leave_room, name='leave_room'),
    path('rejoin/<str:pin>/', views.rejoin_room, name='rejoin_room'),
    path('<str:room_name>/', views.room, name='room'),          
]