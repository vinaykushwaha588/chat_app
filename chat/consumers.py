import json
from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Message, User
from channels.db import database_sync_to_async
from datetime import datetime
from channels.layers import get_channel_layer


channel_layer = get_channel_layer()

async def send_chat_message(sender, receiver, message):
    """ Sends message only to the receiver's WebSocket group """
    await channel_layer.group_send(
        f"chat_{receiver}",  
        {
            "type": "chat_message",
            "message": message,
            "sender": sender
        }
    )       

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        await self.send(text_data=json.dumps({
            "message": f"Welcome to chat {self.room_name}",  
            "sender": "System"
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get("message", "")
        sender = data.get("sender", "Anonymous")

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": message,
                "sender": sender,
                "sender_channel": self.channel_name  
            }
        ) 

    async def chat_message(self, event):
        """ Sends message only to other users in the group, not the sender """
        if event["sender_channel"] != self.channel_name:  
            await self.send(text_data=json.dumps({
                "message": event["message"],
                "sender": event["sender"],
                "timestamp": datetime.utcnow().isoformat()
            }))


class OneToOneChatConsumer(AsyncWebsocketConsumer):
    
    async def connect(self):
        """Connect WebSocket and join a unique conversation room."""
        self.other_user_id = str(self.scope['url_route']['kwargs']['user_id'])
        self.user_id = str(self.scope["user"].id)

        # Ensure stable room name (sorted user IDs)
        sorted_ids = sorted([self.user_id, self.other_user_id])
        self.room_group_name = f"conversation_{'_'.join(sorted_ids)}"

        # Join WebSocket room
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # Send a welcome message
        await self.send(text_data=json.dumps({
            "message": "Welcome to your conversation!",
            "sender": getattr(self.scope["user"], "name", "Unknown")
        }))

    async def disconnect(self, close_code):
        """Disconnect WebSocket and leave the conversation room."""
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        """Receive message from WebSocket, validate input, save to DB, and send to group."""
        try:
            data = json.loads(text_data)
            message = data.get("message", "").strip()
            action = data.get("action")  # Check if action is "mark_seen"
            receiver_id = self.other_user_id  # This should always exist

            sender = self.scope["user"]
            sender_id = str(sender.id)

            # 🔥 If action is "mark_seen", update message status 🔥
            if action == "mark_seen":
                message_ids = data.get("message_ids", [])
                await self.mark_messages_seen(message_ids)
                return

            # Validate required fields
            if not message:
                print("Error: Message cannot be empty!")
                return

            print(f"📩 Message Received: {message}, Sender: {sender_id}, Receiver: {receiver_id}")

            # Save message to DB and get the message ID
            message_id = await self.save_message(sender_id, receiver_id, message)

            # Send message to the group with `message_id`
            event_data = {
                "type": "chat_message",
                "message": message,
                "message_id": message_id,
                "sender_id": sender_id,
                "sender_name": getattr(sender, "name", "Unknown"),
                "receiver_id": receiver_id,
                "seen": False  # 🔥 Initially, message is unseen 🔥
            }
            await self.channel_layer.group_send(self.room_group_name, event_data)

        except json.JSONDecodeError:
            print("JSON Decode Error: Invalid JSON format!")
        except Exception as e:
            print(f"Error in receive method: {e}")

    async def chat_message(self, event):
        """Send the chat message to the WebSocket client (excluding the sender)."""
        try:
            print(f"Event Received in chat_message: {event}")

            receiver_id = event.get("receiver_id")
            sender_id = event.get("sender_id")
            message_id = event.get("message_id")

            if not receiver_id or not message_id:
                print("Error: `receiver_id` or `message_id` is missing in event data!")
                return

            current_user_id = str(self.scope["user"].id)

            # Prevent the sender from receiving their own message
            if current_user_id == sender_id:
                print("Skipping message for sender")
                return

            sender_display = event.get("sender_name", "Unknown")

            await self.send(text_data=json.dumps({
                "message": event["message"],
                "sender": sender_display,
                "receiver_id": receiver_id,
                "message_id": message_id,
                "seen": False  
            }))

        except Exception as e:
            print(f"Error in chat_message method: {e}")

    async def mark_messages_seen(self, message_ids):
        """Mark multiple messages as seen."""
        await self._mark_messages_seen(message_ids)

    @database_sync_to_async
    def _mark_messages_seen(self, message_ids):
        """Mark messages as seen in the database."""
        try:
            messages = Message.objects.filter(id__in=message_ids, seen=False)
            for msg in messages:
                msg.mark_seen()
            print(f"✅ Marked messages as seen: {message_ids}")
        except Exception as e:
            print(f"Error updating seen status: {e}")

    async def save_message(self, sender_id, receiver_id, message):
        """Save chat message in the database asynchronously."""
        return await self._save_message(sender_id, receiver_id, message)

    @database_sync_to_async
    def _save_message(self, sender_id, receiver_id, message):
        """Perform Django ORM operations in a separate thread using `database_sync_to_async`."""
        try:
            sender = User.objects.get(id=sender_id)
            receiver = User.objects.get(id=receiver_id)

            chat_message = Message.objects.create(
                sender=sender,
                receiver=receiver,
                content=message
            )
            return str(chat_message.id)  # Return message ID

        except User.DoesNotExist:
            print("Error: Sender or Receiver not found in database!")
        except Exception as e:
            print(f"Database Save Error: {e}")
            return None