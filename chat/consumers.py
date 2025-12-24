import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import Conversation, Message, TypingStatus
from accounts.models import User
from .serializers import MessageSerializer


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f'chat_{self.conversation_id}'
        self.user = self.scope['user']

        # Vérifier que l'utilisateur est authentifié
        if self.user.is_anonymous:
            await self.close()
            return

        # Vérifier que l'utilisateur fait partie de cette conversation
        has_access = await self.check_conversation_access()
        if not has_access:
            await self.close()
            return

        # Rejoindre le groupe de conversation
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # Mettre l'utilisateur en ligne
        await self.set_user_online(True)

        # Notifier les autres utilisateurs que cet utilisateur est en ligne
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_status',
                'user_id': str(self.user.id),
                'is_online': True
            }
        )

    async def disconnect(self, close_code):
        # Mettre l'utilisateur hors ligne
        await self.set_user_online(False)

        # Arrêter le statut "en train d'écrire"
        await self.update_typing_status(False)

        # Notifier que l'utilisateur est hors ligne
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_status',
                'user_id': str(self.user.id),
                'is_online': False
            }
        )

        # Quitter le groupe
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """Recevoir un message du WebSocket"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            if message_type == 'chat_message':
                # Envoyer un message de chat
                await self.handle_chat_message(data)

            elif message_type == 'typing':
                # Gérer le statut "en train d'écrire"
                await self.handle_typing(data)

            elif message_type == 'read_receipt':
                # Gérer l'accusé de lecture
                await self.handle_read_receipt(data)

        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'error': 'Invalid JSON'
            }))

    async def handle_chat_message(self, data):
        """Gérer l'envoi d'un message de chat"""
        content = data.get('content', '')
        message_type = data.get('message_type', 'text')

        if not content and message_type == 'text':
            return

        # Sauvegarder le message en base de données
        message = await self.save_message(content, message_type)

        if message:
            # Serialiser le message
            message_data = await self.serialize_message(message)

            # Envoyer le message au groupe
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message_data
                }
            )

    async def handle_typing(self, data):
        """Gérer le statut 'en train d'écrire'"""
        is_typing = data.get('is_typing', False)
        
        # Mettre à jour le statut en base de données
        await self.update_typing_status(is_typing)

        # Notifier les autres utilisateurs
        await self.channel_la