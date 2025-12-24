from rest_framework import serializers
from .models import Conversation, Message, TypingStatus
from accounts.serializers import UserSerializer


class MessageSerializer(serializers.ModelSerializer):
    """Serializer pour les messages"""
    sender = UserSerializer(read_only=True)

    class Meta:
        model = Message
        fields = [
            'id', 'conversation', 'sender', 'message_type',
            'content', 'file', 'is_read', 'read_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'sender', 'created_at', 'updated_at']


class MessageCreateSerializer(serializers.ModelSerializer):
    """Serializer pour créer un message"""
    class Meta:
        model = Message
        fields = ['conversation', 'message_type', 'content', 'file']

    def validate(self, attrs):
        message_type = attrs.get('message_type')
        content = attrs.get('content')
        file = attrs.get('file')

        if message_type == 'text' and not content:
            raise serializers.ValidationError({"content": "Le contenu est requis pour un message texte."})
        
        if message_type in ['image', 'file'] and not file:
            raise serializers.ValidationError({"file": "Un fichier est requis pour ce type de message."})

        return attrs


class ConversationSerializer(serializers.ModelSerializer):
    """Serializer pour les conversations"""
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    other_user = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ['id', 'match', 'last_message', 'unread_count', 'other_user', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_last_message(self, obj):
        last_message = obj.messages.last()
        if last_message:
            return MessageSerializer(last_message).data
        return None

    def get_unread_count(self, obj):
        request_user = self.context.get('request').user
        return obj.messages.filter(is_read=False).exclude(sender=request_user).count()

    def get_other_user(self, obj):
        request_user = self.context.get('request').user
        other_user = obj.match.get_other_user(request_user)
        return UserSerializer(other_user).data


class TypingStatusSerializer(serializers.ModelSerializer):
    """Serializer pour le statut 'en train d'écrire'"""
    class Meta:
        model = TypingStatus
        fields = ['conversation', 'user', 'is_typing', 'updated_at']
        read_only_fields = ['user', 'updated_at']