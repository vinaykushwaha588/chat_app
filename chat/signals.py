from django.db.models.signals import post_save
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import json
from .models import Message

@receiver(post_save, sender=Message)
def broadcast_new_message(sender, instance, created, **kwargs):
    if created:
        # Compute the same group name as in the consumer using sender and receiver IDs
        sender_id = instance.sender.id
        receiver_id = instance.receiver.id
        sorted_ids = sorted([str(sender_id), str(receiver_id)])
        room_group_name = "conversation_" + "_".join(sorted_ids)
        
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                "type": "chat_message",  # This maps to the chat_message() method in the consumer
                "message": instance.content,
                "sender": instance.sender.name,
            }
        )
