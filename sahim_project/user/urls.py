from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

urlpatterns = [
    # ورود یا ثبت نام کاربر
    path('auth/', views.AuthView.as_view(), name='auth'),
    # مشاهده یا ویرایش پروفایل
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    # مشاهده چت های کاربر
    path('chat-list/', views.ChatListView.as_view(), name='chat-list'),
    # لیست تمام کاربرها
    path('user-list/', views.UserListView.as_view(), name='user-list'),
    # API چت کردن
    path('chatSend/', views.SendMessageAPIView.as_view(), name='send-message'),
    # API درست کردن چت
    path('create-chat/', views.CreateChatView.as_view(), name='create-chat'),
    # مشاهده چت های کاربر با یک کاربر خاص
    path('user/<int:user_id>/chats/', views.UserChatListAPIView.as_view(), name='user_chats'),
]
