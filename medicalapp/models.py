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
    

# Add to medicalapp/models.py
class Medication(models.Model):
    STATUS_CHOICES = [
        ('upcoming', 'Upcoming'),
        ('taken', 'Taken'),
        ('missed', 'Missed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='medications', null=True, blank=True)
    name = models.CharField(max_length=255)
    instructions = models.TextField()
    next_dose = models.TimeField(help_text="Time for the next dose")
    refill_date = models.DateField()
    remaining = models.CharField(max_length=50)  # '15 tablets' format
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='upcoming')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
def __str__(self):
    if self.user:
        return f"{self.name} for {self.user.username}"
    return f"{self.name} (no user)"


class MedicationLog(models.Model):
    medication = models.ForeignKey(Medication, on_delete=models.CASCADE, related_name='logs')
    taken_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=Medication.STATUS_CHOICES)
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.medication.name} - {self.taken_at.strftime('%Y-%m-%d %H:%M')}"