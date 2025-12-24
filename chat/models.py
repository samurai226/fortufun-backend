from django.db import models
from accounts.models import User
from matching.models import Match
import uuid

class Conversation(models.Model):
    """Conversation entre deux utilisateurs matchés"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    match = models.OneToOneField(Match, on_delete=models.CASCADE, related_name='conversation')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Conversation: {self.match}"

    class Meta:
        ordering = ['-updated_at']


class Message(models.Model):
    """Message dans une conversation"""
    MESSAGE_TYPES = [
        ('text', 'Texte'),
        ('image', 'Image'),
        ('file', 'Fichier'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default='text')
    content = models.TextField(blank=True)  # Pour les messages texte
    file = models.FileField(upload_to='chat_files/%Y/%m/%d/', blank=True, null=True)
    
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Message de {self.sender.email} dans {self.conversation.id}"

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
            models.Index(fields=['sender', 'created_at']),
        ]


class TypingStatus(models.Model):
    """Statut "en train d'écrire" """
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='typing_statuses')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_typing = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} typing in {self.conversation.id}"

    class Meta:
        unique_together = ['conversation', 'user']