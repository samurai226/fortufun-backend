from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import User, UserProfile, ProfilePhoto, Interest
from .serializers import (
    RegisterSerializer, UserSerializer, UserProfileSerializer,
    UserProfileUpdateSerializer, ProfilePhotoSerializer, InterestSerializer,LoginSerializer
)


class RegisterView(generics.CreateAPIView):
    """Inscription d'un nouvel utilisateur"""
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Créer le profil automatiquement
        UserProfile.objects.create(user=user)
        
        # Générer les tokens JWT
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)


class LoginView(generics.GenericAPIView):
    """Connexion d'un utilisateur"""
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer  # AJOUTE CETTE LIGNE

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response(
                {'error': 'Email et mot de passe requis'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Authenticate avec email
        user = User.objects.filter(email=email).first()
        if user and user.check_password(password):
            # Mettre à jour le statut en ligne
            user.is_online = True
            user.save()

            # Générer les tokens
            refresh = RefreshToken.for_user(user)

            return Response({
                'user': UserSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })

        return Response(
            {'error': 'Identifiants invalides'},
            status=status.HTTP_401_UNAUTHORIZED
        )

class LogoutView(generics.GenericAPIView):
    """Déconnexion d'un utilisateur"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # Mettre à jour le statut hors ligne
            request.user.is_online = False
            request.user.save()

            # Blacklist le refresh token
            refresh_token = request.data.get("refresh")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()

            return Response({'message': 'Déconnexion réussie'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class UserProfileViewSet(viewsets.ModelViewSet):
    """ViewSet pour gérer le profil utilisateur"""
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserProfile.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return UserProfileUpdateSerializer
        return UserProfileSerializer

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Récupérer le profil de l'utilisateur connecté"""
        try:
            profile = request.user.profile
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'Profil non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['patch'])
    def update_profile(self, request):
        """Mettre à jour le profil de l'utilisateur connecté"""
        try:
            profile = request.user.profile
            serializer = UserProfileUpdateSerializer(profile, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(UserProfileSerializer(profile).data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'Profil non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )


class ProfilePhotoViewSet(viewsets.ModelViewSet):
    """ViewSet pour gérer les photos de profil"""
    serializer_class = ProfilePhotoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ProfilePhoto.objects.filter(profile__user=self.request.user)

    def perform_create(self, serializer):
        profile = self.request.user.profile
        
        # Limiter à 6 photos maximum
        if profile.photos.count() >= 6:
            return Response(
                {'error': 'Maximum 6 photos autorisées'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer.save(profile=profile)

    @action(detail=True, methods=['post'])
    def set_primary(self, request, pk=None):
        """Définir une photo comme photo principale"""
        photo = self.get_object()
        
        # Retirer le flag primary des autres photos
        ProfilePhoto.objects.filter(profile=photo.profile).update(is_primary=False)
        
        # Définir cette photo comme principale
        photo.is_primary = True
        photo.save()
        
        return Response(ProfilePhotoSerializer(photo).data)


class InterestViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour lire les centres d'intérêt disponibles"""
    queryset = Interest.objects.all()
    serializer_class = InterestSerializer
    permission_classes = [IsAuthenticated]