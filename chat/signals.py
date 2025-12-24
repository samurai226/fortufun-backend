from django.db.models.signals import post_save
from django.dispatch import receiver
from matching.models import Match
from .models import Conversation


@receiver(post_save, sender=Match)
def create_conversation(sender, instance, created, **kwargs):
    """Créer automatiquement une conversation quand il y a un match"""
    if created:
        Conversation.objects.create(match=instance)