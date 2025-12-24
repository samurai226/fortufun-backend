from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.utils import timezone
from .models import Swipe, Match
from .serializers import SwipeSerializer, MatchSerializer, MatchDetailSerializer
from accounts.models import UserProfile
from accounts.serializers import UserProfileSerializer
import math


class DiscoverViewSet(viewsets.ViewSet):
    """ViewSet pour découvrir des profils à swiper"""
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """Retourne une liste de profils à swiper"""
        user = request.user
        try:
            user_profile = user.profile
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'Veuillez compléter votre profil'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Récupérer les IDs des utilisateurs déjà swipés
        swiped_user_ids = Swipe.objects.filter(from_user=user).values_list('to_user_id', flat=True)

        # Filtrer les profils selon les préférences
        profiles = UserProfile.objects.exclude(
            Q(user=user) | Q(user__id__in=swiped_user_ids)
        ).filter(
            gender=user_profile.looking_for if user_profile.looking_for != 'B' else Q(gender__in=['M', 'F', 'O']),
            looking_for__in=['B', user_profile.gender]
        )

        # Filtrer par âge
        if user_profile.age:
            profiles = profiles.filter(
                birth_date__isnull=False
            )
            # Filtrer par l'âge calculé (approximatif)

        # Filtrer par distance (si coordonnées disponibles)
        if user_profile.latitude and user_profile.longitude:
            profiles = profiles.filter(
                latitude__isnull=False,
                longitude__isnull=False
            )
            # Calcul de distance à faire côté client ou avec PostGIS pour plus de précision

        # Limiter à 20 profils
        profiles = profiles[:20]

        serializer = UserProfileSerializer(profiles, many=True)
        return Response(serializer.data)


class SwipeViewSet(viewsets.ModelViewSet):
    """ViewSet pour gérer les swipes"""
    serializer_class = SwipeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Swipe.objects.filter(from_user=self.request.user)

    def create(self, request):
        """Créer un swipe et vérifier si c'est un match"""
        to_user_id = request.data.get('to_user')
        swipe_type = request.data.get('swipe_type', 'pass')

        if not to_user_id:
            return Response(
                {'error': 'to_user requis'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Vérifier que l'utilisateur n'a pas déjà swipé
        if Swipe.objects.filter(from_user=request.user, to_user_id=to_user_id).exists():
            return Response(
                {'error': 'Vous avez déjà swipé cet utilisateur'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Créer le swipe
        swipe = Swipe.objects.create(
            from_user=request.user,
            to_user_id=to_user_id,
            swipe_type=swipe_type
        )

        # Incrémenter le compteur de swipes
        request.user.profile.swipe_count += 1
        request.user.profile.save()

        # Vérifier si c'est un match (like mutuel)
        is_match = False
        match = None

        if swipe_type in ['like', 'super_like']:
            # Vérifier si l'autre utilisateur a aussi liké
            reciprocal_swipe = Swipe.objects.filter(
                from_user_id=to_user_id,
                to_user=request.user,
                swipe_type__in=['like', 'super_like']
            ).first()

            if reciprocal_swipe:
                # C'est un match!
                match = Match.objects.create(
                    user1=request.user if request.user.id < reciprocal_swipe.from_user.id else reciprocal_swipe.from_user,
                    user2=reciprocal_swipe.from_user if request.user.id < reciprocal_swipe.from_user.id else request.user
                )

                # Incrémenter les compteurs de match
                request.user.profile.match_count += 1
                request.user.profile.save()
                
                reciprocal_swipe.from_user.profile.match_count += 1
                reciprocal_swipe.from_user.profile.save()

                is_match = True

        return Response({
            'swipe': SwipeSerializer(swipe).data,
            'is_match': is_match,
            'match': MatchSerializer(match).data if match else None
        }, status=status.HTTP_201_CREATED)


class MatchViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour gérer les matches"""
    serializer_class = MatchDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Match.objects.filter(
            Q(user1=user) | Q(user2=user),
            is_active=True
        ).order_by('-matched_at')

    def get_serializer_context(self):
        return {'request': self.request}

    @action(detail=True, methods=['post'])
    def mark_seen(self, request, pk=None):
        """Marquer un match comme vu"""
        match = self.get_object()
        
        if match.user1 == request.user:
            match.user1_seen = True
        else:
            match.user2_seen = True
        
        match.save()
        
        return Response({'status': 'Match marqué comme vu'})

    @action(detail=True, methods=['post'])
    def unmatch(self, request, pk=None):
        """Annuler un match"""
        match = self.get_object()
        match.is_active = False
        match.save()
        
        return Response({'status': 'Match annulé'})