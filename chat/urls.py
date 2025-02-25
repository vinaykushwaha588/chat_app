from django.urls import path, include
from .views import *
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('auth', AuthViewSet, basename='auth')

urlpatterns = [
    path("",include(router.urls)),
    path('register/', UserCreateView.as_view(), name='user-register'),
    path('login/', LoginView.as_view(), name='login'),
    path('private-chats/', PrivateChatListCreateView.as_view(), name='private-chat-list'),
    path('conversations/<str:user_id>/', ConversationMessageListCreateView.as_view(), name='conversation-messages'),
    path('search-users/', search_users, name='search_users'),
]


