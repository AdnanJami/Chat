import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth.models import User


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