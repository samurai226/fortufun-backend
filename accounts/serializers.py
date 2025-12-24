from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, UserProfile, ProfilePhoto, Interest, UserInterest


class LoginSerializer(serializers.Serializer):
    """Serializer pour la connexion"""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class UserSerializer(serializers.ModelSerializer):
    """Serializer pour l'utilisateur"""
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'phone', 'is_verified', 
                  'is_online', 'last_seen', 'created_at']
        read_only_fields = ['id', 'is_verified', 'is_online', 'last_seen', 'created_at']


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer pour l'inscription"""
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['email', 'username', 'password', 'password2', 'phone']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Les mots de passe ne correspondent pas."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            phone=validated_data.get('phone', '')
        )
        return user


class ProfilePhotoSerializer(serializers.ModelSerializer):
    """Serializer pour les photos de profil"""
    class Meta:
        model = ProfilePhoto
        fields = ['id', 'image', 'order', 'is_primary', 'created_at']
        read_only_fields = ['id', 'created_at']


class InterestSerializer(serializers.ModelSerializer):
    """Serializer pour les centres d'intérêt"""
    class Meta:
        model = Interest
        fields = ['id', 'name', 'icon']


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer pour le profil utilisateur"""
    user = UserSerializer(read_only=True)
    photos = ProfilePhotoSerializer(many=True, read_only=True)
    interests = serializers.SerializerMethodField()
    age = serializers.IntegerField(read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'bio', 'birth_date', 'gender', 'looking_for',
            'city', 'country', 'latitude', 'longitude', 'max_distance',
            'min_age_preference', 'max_age_preference', 'age',
            'swipe_count', 'match_count', 'photos', 'interests',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'swipe_count', 'match_count', 'created_at', 'updated_at']

    def get_interests(self, obj):
        user_interests = UserInterest.objects.filter(profile=obj).select_related('interest')
        return InterestSerializer([ui.interest for ui in user_interests], many=True).data


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour la mise à jour du profil"""
    interest_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = UserProfile
        fields = [
            'bio', 'birth_date', 'gender', 'looking_for',
            'city', 'country', 'latitude', 'longitude', 'max_distance',
            'min_age_preference', 'max_age_preference', 'interest_ids'
        ]

    def update(self, instance, validated_data):
        interest_ids = validated_data.pop('interest_ids', None)
        
        # Mettre à jour le profil
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Mettre à jour les intérêts
        if interest_ids is not None:
            UserInterest.objects.filter(profile=instance).delete()
            for interest_id in interest_ids:
                try:
                    interest = Interest.objects.get(id=interest_id)
                    UserInterest.objects.create(profile=instance, interest=interest)
                except Interest.DoesNotExist:
                    pass

        return instance