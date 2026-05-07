import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ChatRoom, Message
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth.models import User


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.pin = self.scope['url_route']['kwargs']['pin']
        self.room_group_name = f'chat_{self.pin}'

        # Get user from token
        query_string = self.scope['query_string'].decode()
        params = dict(p.split('=') for p in query_string.split('&') if '=' in p)
        token = params.get('token')
        self.user = await self.get_user_from_token(token)

        if not self.user:
            await self.close()
            return

        self.username = self.user.username

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # Send history first
        history = await self.get_message_history()
        for msg in history:
            await self.send(text_data=json.dumps({
                'type': 'message',
                'message': msg['content'],
                'username': msg['username'],
                'timestamp': msg['timestamp'],
            }))

        # Broadcast join notification to everyone
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_join',
                'username': self.username,
            }
        )

    async def disconnect(self, close_code):
        if hasattr(self, 'username'):
            # Broadcast leave notification
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_leave',
                    'username': self.username,
                }
            )
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        username = self.username

        timestamp = await self.save_message(username, message)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'username': username,
                'timestamp': timestamp,
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event['message'],
            'username': event['username'],
            'timestamp': event['timestamp'],
        }))

    async def user_join(self, event):
        await self.send(text_data=json.dumps({
            'type': 'join',
            'username': event['username'],
        }))

    async def user_leave(self, event):
        await self.send(text_data=json.dumps({
            'type': 'leave',
            'username': event['username'],
        }))

    @database_sync_to_async
    def get_user_from_token(self, token):
        try:
            from rest_framework_simplejwt.tokens import AccessToken
            from django.contrib.auth.models import User
            validated = AccessToken(token)
            return User.objects.get(id=validated['user_id'])
        except Exception:
            return None

    @database_sync_to_async
    def get_message_history(self):
        try:
            room = ChatRoom.objects.get(pin=self.pin)
            messages = Message.objects.filter(room=room).order_by('timestamp')[:100]
            return [
                {
                    'username': m.username,
                    'content': m.content,
                    'timestamp': m.timestamp.strftime('%H:%M'),
                }
                for m in messages
            ]
        except ChatRoom.DoesNotExist:
            return []

    @database_sync_to_async
    def save_message(self, username, content):
        room = ChatRoom.objects.get(pin=self.pin)
        msg = Message.objects.create(room=room, username=username, content=content)
        return msg.timestamp.strftime('%H:%M')
    

class SignalingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.pin = self.scope['url_route']['kwargs']['pin']
        self.room_group_name = f'signal_{self.pin}'

        # Authenticate via token
        query_string = self.scope['query_string'].decode()
        params = dict(p.split('=') for p in query_string.split('&') if '=' in p)
        token = params.get('token')
        self.user = await self.get_user_from_token(token)

        if not self.user:
            await self.close()
            return

        self.username = self.user.username

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # Notify others someone joined
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_joined',
                'username': self.username,
                'channel': self.channel_name,
            }
        )

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_left',
                    'username': self.username,
                }
            )
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        msg_type = data.get('type')

        # Relay offer, answer, ice-candidate to the group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'signal_relay',
                'message': data,
                'sender': self.channel_name,
                'username': self.username,
            }
        )

    async def signal_relay(self, event):
        # Don't send back to sender
        if event['sender'] == self.channel_name:
            return
        await self.send(text_data=json.dumps(event['message']))

    async def user_joined(self, event):
        if event['channel'] == self.channel_name:
            return
        await self.send(text_data=json.dumps({
            'type': 'user-joined',
            'username': event['username'],
        }))

    async def user_left(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user-left',
            'username': event['username'],
        }))

    @database_sync_to_async
    def get_user_from_token(self, token):
        try:
            validated = AccessToken(token)
            return User.objects.get(id=validated['user_id'])
        except Exception:
            return None