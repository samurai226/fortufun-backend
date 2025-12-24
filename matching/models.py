from django.db import models
from accounts.models import User
import uuid

class Swipe(models.Model):
    """Enregistre chaque swipe (like/pass)"""
    SWIPE_CHOICES = [
        ('like', 'Like'),
        ('pass', 'Pass'),
        ('super_like', 'Super Like'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='swipes_made')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='swipes_received')
    swipe_type = models.CharField(max_length=15, choices=SWIPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.from_user.email} -> {self.swipe_type} -> {self.to_user.email}"

    class Meta:
        unique_together = ['from_user', 'to_user']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['from_user', 'to_user']),
            models.Index(fields=['to_user', 'swipe_type']),
        ]


class Match(models.Model):
    """Match entre deux utilisateurs (like mutuel)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='matches_as_user1')
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='matches_as_user2')
    is_active = models.BooleanField(default=True)
    matched_at = models.DateTimeField(auto_now_add=True)
    
    # Pour savoir si le match a été vu par les utilisateurs
    user1_seen = models.BooleanField(default=False)
    user2_seen = models.BooleanField(default=False)

    def __str__(self):
        return f"Match: {self.user1.email} <-> {self.user2.email}"

    class Meta:
        ordering = ['-matched_at']
        indexes = [
            models.Index(fields=['user1', 'user2']),
            models.Index(fields=['is_active', 'matched_at']),
        ]

    def get_other_user(self, user):
        """Retourne l'autre utilisateur du match"""
        return self.user2 if self.user1 == user else self.user1