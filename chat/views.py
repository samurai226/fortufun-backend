from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.utils import timezone
from .models import Conversation, Message, TypingStatus
from .serializers import (
    ConversationSerializer, MessageSerializer,
    MessageCreateSerializer, TypingStatusSerializer
)
from matching.models import Match


class ConversationViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour gérer les conversations"""
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # Récupérer les conversations des matches de l'utilisateur
        return Conversation.objects.filter(
            Q(match__user1=user) | Q(match__user2=user),
            match__is_active=True
        ).order_by('-updated_at')

    def get_serializer_context(self):
        return {'request': self.request}


class MessageViewSet(viewsets.ModelViewSet):
    """ViewSet pour gérer les messages"""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        conversation_id = self.request.query_params.get('conversation')
        if conversation_id:
            return Message.objects.filter(conversation_id=conversation_id).order_by('created_at')
        return Message.objects.none()

    def get_serializer_class(self):
        if self.action == 'create':
            return MessageCreateSerializer
        return MessageSerializer

    def create(self, request):
        """Créer un nouveau message"""
        serializer = MessageCreateSerializer(data=request.data)
        if serializer.is_valid():
            # Vérifier que l'utilisateur fait partie de la conversation
            conversation_id = serializer.validated_data.get('conversation').id
            try:
                conversation = Conversation.objects.get(id=conversation_id)
                match = conversation.match
                
                if request.user not in [match.user1, match.user2]:
                    return Response(
                        {'error': 'Vous ne faites pas partie de cette conversation'},
                        status=status.HTTP_403_FORBIDDEN
                    )
                
                # Créer le message
                message = serializer.save(sender=request.user)
                
                # Mettre à jour le timestamp de la conversation
                conversation.updated_at = timezone.now()
                conversation.save()
                
                return Response(
                    MessageSerializer(message).data,
                    status=status.HTTP_201_CREATED
                )
            except Conversation.DoesNotExist:
                return Response(
                    {'error': 'Conversation non trouvée'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Marquer un message comme lu"""
        message = self.get_object()
        
        # Vérifier que c'est le destinataire
        if message.sender == request.user:
            return Response(
                {'error': 'Vous ne pouvez pas marquer votre propre message comme lu'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        message.is_read = True
        message.read_at = timezone.now()
        message.save()
        
        return Response(MessageSerializer(message).data)

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Marquer tous les messages d'une conversation comme lus"""
        conversation_id = request.data.get('conversation')
        
        if not conversation_id:
            return Response(
                {'error': 'conversation_id requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        messages = Message.objects.filter(
            conversation_id=conversation_id,
            is_read=False
        ).exclude(sender=request.user)
        
        messages.update(is_read=True, read_at=timezone.now())
        
        return Response({'status': f'{messages.count()} messages marqués comme lus'})