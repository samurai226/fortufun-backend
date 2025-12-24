from django.contrib import admin
from .models import Conversation, Message, TypingStatus

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['id', 'match', 'created_at', 'updated_at']
    search_fields = ['match__user1__email', 'match__user2__email']
    date_hierarchy = 'created_at'
    ordering = ['-updated_at']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'conversation', 'message_type', 'is_read', 'created_at']
    list_filter = ['message_type', 'is_read', 'created_at']
    search_fields = ['sender__email', 'content']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']


@admin.register(TypingStatus)
class TypingStatusAdmin(admin.ModelAdmin):
    list_display = ['user', 'conversation', 'is_typing', 'updated_at']
    list_filter = ['is_typing']