from rest_framework import serializers
from .models import Swipe, Match
from accounts.serializers import UserSerializer, UserProfileSerializer


class SwipeSerializer(serializers.ModelSerializer):
    """Serializer pour les swipes"""
    class Meta:
        model = Swipe
        fields = ['id', 'from_user', 'to_user', 'swipe_type', 'created_at']
        read_only_fields = ['id', 'from_user', 'created_at']


class MatchSerializer(serializers.ModelSerializer):
    """Serializer pour les matches"""
    user1 = UserSerializer(read_only=True)
    user2 = UserSerializer(read_only=True)
    user1_profile = serializers.SerializerMethodField()
    user2_profile = serializers.SerializerMethodField()

    class Meta:
        model = Match
        fields = [
            'id', 'user1', 'user2', 'user1_profile', 'user2_profile',
            'is_active', 'user1_seen', 'user2_seen', 'matched_at'
        ]
        read_only_fields = ['id', 'matched_at']

    def get_user1_profile(self, obj):
        try:
            profile = obj.user1.profile
            return UserProfileSerializer(profile).data
        except:
            return None

    def get_user2_profile(self, obj):
        try:
            profile = obj.user2.profile
            return UserProfileSerializer(profile).data
        except:
            return None


class MatchDetailSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour un match (avec l'autre utilisateur)"""
    other_user = serializers.SerializerMethodField()
    other_user_profile = serializers.SerializerMethodField()

    class Meta:
        model = Match
        fields = ['id', 'other_user', 'other_user_profile', 'is_active', 'matched_at']
        read_only_fields = ['id', 'matched_at']

    def get_other_user(self, obj):
        request_user = self.context.get('request').user
        other_user = obj.get_other_user(request_user)
        return UserSerializer(other_user).data

    def get_other_user_profile(self, obj):
        request_user = self.context.get('request').user
        other_user = obj.get_other_user(request_user)
        try:
            profile = other_user.profile
            return UserProfileSerializer(profile).data
        except:
            return None