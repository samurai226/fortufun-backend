from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

class User(AbstractUser):
    """Modèle User personnalisé"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

    class Meta:
        ordering = ['-created_at']


class UserProfile(models.Model):
    """Profil utilisateur pour le matching"""
    GENDER_CHOICES = [
        ('M', 'Homme'),
        ('F', 'Femme'),
        ('O', 'Autre'),
    ]

    LOOKING_FOR_CHOICES = [
        ('M', 'Homme'),
        ('F', 'Femme'),
        ('B', 'Les deux'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(max_length=500, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    looking_for = models.CharField(max_length=1, choices=LOOKING_FOR_CHOICES)
    
    # Localisation
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    
    # Préférences de distance (en km)
    max_distance = models.IntegerField(
        default=50,
        validators=[MinValueValidator(1), MaxValueValidator(500)]
    )
    
    # Préférences d'âge
    min_age_preference = models.IntegerField(
        default=18,
        validators=[MinValueValidator(18), MaxValueValidator(100)]
    )
    max_age_preference = models.IntegerField(
        default=35,
        validators=[MinValueValidator(18), MaxValueValidator(100)]
    )
    
    # Statistiques
    swipe_count = models.IntegerField(default=0)
    match_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile de {self.user.email}"

    @property
    def age(self):
        """Calcule l'âge à partir de la date de naissance"""
        if self.birth_date:
            from datetime import date
            today = date.today()
            return today.year - self.birth_date.year - (
                (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
            )
        return None

    class Meta:
        ordering = ['-created_at']


class ProfilePhoto(models.Model):
    """Photos de profil (max 6 photos)"""
    profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='profile_photos/%Y/%m/%d/')
    order = models.IntegerField(default=0)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Photo {self.order} de {self.profile.user.email}"

    class Meta:
        ordering = ['order']
        unique_together = ['profile', 'order']


class Interest(models.Model):
    """Centres d'intérêt"""
    name = models.CharField(max_length=50, unique=True)
    icon = models.CharField(max_length=50, blank=True)  # Nom de l'icône pour Flutter

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class UserInterest(models.Model):
    """Association User <-> Intérêts"""
    profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='interests')
    interest = models.ForeignKey(Interest, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.profile.user.email} - {self.interest.name}"

    class Meta:
        unique_together = ['profile', 'interest']