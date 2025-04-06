# medicalapp/serializers.py
from rest_framework import serializers
from .models import Medication, MedicationLog, Conversation, Message, MedicalImage

class MedicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medication
        fields = ['id', 'name', 'instructions', 'next_dose', 'refill_date', 'remaining', 'status', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class MedicationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicationLog
        fields = ['id', 'medication', 'taken_at', 'status', 'notes']

# Adding serializers for existing models for completeness
class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'content', 'sender', 'timestamp']

class ConversationSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)
    
    class Meta:
        model = Conversation
        fields = ['id', 'start_time', 'last_interaction', 'messages']