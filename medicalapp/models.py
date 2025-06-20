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


# appointment
class MedicalSpecialty(models.Model):
    """Medical specialties like Cardiology, Orthopedics, etc."""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Medical Specialties"


class Doctor(models.Model):
    """Doctor model with specialization and availability"""
    name = models.CharField(max_length=100)
    specialty = models.ForeignKey(MedicalSpecialty, on_delete=models.CASCADE, related_name='doctors')
    bio = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    languages = models.CharField(max_length=200, blank=True, help_text="Comma-separated languages")
    # Optional: Add doctor's photo
    photo = models.ImageField(upload_to='doctor_photos/', blank=True, null=True)
    
    def __str__(self):
        return f"Dr. {self.name} ({self.specialty})"
    
    
class DoctorAvailability(models.Model):
    """Doctor's available time slots"""
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='available_slots')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.doctor} - {self.date} {self.start_time}-{self.end_time}"
    
    class Meta:
        verbose_name_plural = "Doctor Availabilities"


class AppointmentCategory(models.Model):
    """Top-level categories for medical concerns (e.g., Bone/Joint/Muscle issues)"""
    name = models.CharField(max_length=100)
    specialties = models.ManyToManyField(MedicalSpecialty, related_name='categories')
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Appointment Categories"


class AppointmentSubcategory(models.Model):
    """Subcategories for medical concerns (e.g., Joint pain, Back problems)"""
    category = models.ForeignKey(AppointmentCategory, on_delete=models.CASCADE, related_name='subcategories')
    name = models.CharField(max_length=100)
    specialties = models.ManyToManyField(MedicalSpecialty, related_name='subcategories')
    
    def __str__(self):
        return f"{self.category} - {self.name}"
    
    class Meta:
        verbose_name_plural = "Appointment Subcategories"


class LocationOption(models.Model):
    """Location options for specific issues (e.g., Knee, Shoulder)"""
    subcategory = models.ForeignKey(AppointmentSubcategory, on_delete=models.CASCADE, related_name='locations')
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return f"{self.subcategory} - {self.name}"


class Appointment(models.Model):
    """Appointment bookings"""
    STATUS_CHOICES = (
        ('scheduled', 'Scheduled'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='appointments')
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    category = models.ForeignKey(AppointmentCategory, on_delete=models.SET_NULL, null=True, blank=True)
    subcategory = models.ForeignKey(AppointmentSubcategory, on_delete=models.SET_NULL, null=True, blank=True)
    location = models.ForeignKey(LocationOption, on_delete=models.SET_NULL, null=True, blank=True)
    patient_name = models.CharField(max_length=100)
    patient_phone = models.CharField(max_length=20)
    patient_email = models.EmailField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.patient_name} with {self.doctor} on {self.appointment_date} at {self.appointment_time}"



from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class HealthMetrics(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='health_metrics')
    timestamp = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    # Vital Signs
    systolic_bp = models.PositiveSmallIntegerField(null=True, blank=True)
    diastolic_bp = models.PositiveSmallIntegerField(null=True, blank=True)
    heart_rate = models.PositiveSmallIntegerField(null=True, blank=True)
    oxygen_saturation = models.PositiveSmallIntegerField(null=True, blank=True)
    
    # Biochemical
    blood_glucose = models.PositiveSmallIntegerField(null=True, blank=True)
    
    # Anthropometric
    weight = models.FloatField(null=True, blank=True)  # kg
    height = models.FloatField(null=True, blank=True)  # cm
    
    # Activity
    daily_steps = models.PositiveIntegerField(null=True, blank=True)
    sleep_hours = models.FloatField(null=True, blank=True)
    
    # Calculated Fields
    bmi = models.FloatField(null=True, blank=True)
    health_score = models.PositiveSmallIntegerField(null=True, blank=True)

    def save(self, *args, **kwargs):
        """Auto-calculate BMI on save"""
        if self.height and self.weight:
            self.bmi = round(self.weight / ((self.height/100) ** 2), 1)
        super().save(*args, **kwargs)

    def calculate_health_score(self):
        scores = {}

    
        # Blood Pressure (30 points max)
        if self.systolic_bp and self.diastolic_bp:
            if self.systolic_bp <= 120 and self.diastolic_bp <= 80:
                scores['bp'] = 30  # Perfect
            elif self.systolic_bp <= 130 and self.diastolic_bp <= 85:
                scores['bp'] = 25  # Elevated
            elif self.systolic_bp <= 140 or self.diastolic_bp <= 90:
                scores['bp'] = 15  # Stage 1 Hypertension
            else:
                scores['bp'] = 5   # Stage 2 Hypertension

        # Blood Glucose (20 points max)
        if self.blood_glucose:
            if self.blood_glucose <= 100:
                scores['glucose'] = 20
            elif self.blood_glucose <= 125:
                scores['glucose'] = 10
            else:
                scores['glucose'] = 5  # Deduct more for high glucose

        # BMI (15 points max)
        if self.bmi:
            if 18.5 <= self.bmi <= 24.9:
                scores['bmi'] = 15
            elif 25 <= self.bmi <= 29.9:
                scores['bmi'] = 8  # Overweight penalty
            else:
                scores['bmi'] = 3  # Obese penalty

        # Activity (15 points max)
        if self.daily_steps:
            if self.daily_steps >= 10000:
                scores['activity'] = 15
            elif self.daily_steps >= 8000:
                scores['activity'] = 10
            else:
                scores['activity'] = 5

        # Other metrics (20 points total)
        scores['other'] = 0
        if self.heart_rate and 60 <= self.heart_rate <= 80:
            scores['other'] += 5
        if self.sleep_hours and 7 <= self.sleep_hours <= 9:
            scores['other'] += 5
        if self.oxygen_saturation and self.oxygen_saturation >= 95:
            scores['other'] += 5
        if self.weight and self.height:  # Already counted in BMI
            scores['other'] += 5

        total_score = sum(scores.values())
        self.health_score = min(100, max(0, round(total_score)))
        return self.health_score