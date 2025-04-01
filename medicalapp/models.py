from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Conversation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    start_time = models.DateTimeField(default=timezone.now)
    last_interaction = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Conversation for {self.user.username} at {self.start_time}"

class Message(models.Model):
    SENDER_CHOICES = [
        ('user', 'User'),
        ('ai', 'AI Assistant')
    ]

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    content = models.TextField()
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES)
    timestamp = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.sender}: {self.content[:50]}"

class MedicalImage(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='medical_images/')
    analysis_result = models.TextField(blank=True, null=True)
    uploaded_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Image for conversation {self.conversation.id}"