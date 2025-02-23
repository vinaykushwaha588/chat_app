from django.urls import path
from .consumers import ChatConsumer, OneToOneChatConsumer

websocket_urlpatterns = [
    path("ws/chat/<str:room_name>/", ChatConsumer.as_asgi()),
    path("ws/onetone/<uuid:user_id>/", OneToOneChatConsumer.as_asgi()),
]
