"""
Serializers de Soporte
"""

from rest_framework import serializers
from .models import SupportTicket, TicketMessage, FAQ, KnowledgeBaseArticle


class TicketMessageSerializer(serializers.ModelSerializer):
    """Serializer de mensaje de ticket."""
    
    sender_name = serializers.SerializerMethodField()
    
    class Meta:
        model = TicketMessage
        fields = [
            'id', 'sender', 'sender_name', 'message_type',
            'content', 'attachments', 'is_internal',
            'is_read', 'created_at'
        ]
    
    def get_sender_name(self, obj):
        return obj.sender.get_display_name()


class SupportTicketSerializer(serializers.ModelSerializer):
    """Serializer de ticket de soporte."""
    
    messages = TicketMessageSerializer(many=True, read_only=True)
    user_name = serializers.SerializerMethodField()
    assigned_to_name = serializers.SerializerMethodField()
    
    class Meta:
        model = SupportTicket
        fields = [
            'id', 'ticket_number', 'user', 'user_name',
            'assigned_to', 'assigned_to_name', 'category',
            'priority', 'status', 'subject', 'description',
            'related_order', 'related_product', 'attachments',
            'first_response_at', 'satisfaction_rating',
            'created_at', 'updated_at', 'resolved_at', 'closed_at',
            'messages'
        ]
    
    def get_user_name(self, obj):
        return obj.user.get_display_name()
    
    def get_assigned_to_name(self, obj):
        if obj.assigned_to:
            return obj.assigned_to.get_display_name()
        return None


class SupportTicketCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear ticket."""
    
    class Meta:
        model = SupportTicket
        fields = [
            'category', 'priority', 'subject', 'description',
            'related_order', 'related_product'
        ]


class FASerializer(serializers.ModelSerializer):
    """Serializer de FAQ."""
    
    class Meta:
        model = FAQ
        fields = ['id', 'question', 'answer', 'category', 'views', 'order']


class KnowledgeBaseArticleSerializer(serializers.ModelSerializer):
    """Serializer de artículo KB."""
    
    author_name = serializers.SerializerMethodField()
    
    class Meta:
        model = KnowledgeBaseArticle
        fields = [
            'id', 'title', 'slug', 'content', 'category',
            'meta_title', 'meta_description', 'keywords',
            'is_published', 'is_featured', 'views',
            'helpful_yes', 'helpful_no', 'author_name',
            'created_at', 'updated_at', 'published_at'
        ]
    
    def get_author_name(self, obj):
        if obj.author:
            return obj.author.get_display_name()
        return None
