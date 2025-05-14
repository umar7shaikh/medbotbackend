# medicalapp/serializers.py
from rest_framework import serializers
from .models import Medication, MedicationLog, Conversation, Message, MedicalImage
from .models import (
    MedicalSpecialty, Doctor, DoctorAvailability,
    AppointmentCategory, AppointmentSubcategory, LocationOption, Appointment,HealthMetrics
)


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


class MedicalSpecialtySerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalSpecialty
        fields = '__all__'


class DoctorSerializer(serializers.ModelSerializer):
    specialty_name = serializers.CharField(source='specialty.name', read_only=True)
    
    class Meta:
        model = Doctor
        fields = ['id', 'name', 'specialty', 'specialty_name', 'bio', 'languages', 'photo', 'is_active']


class DoctorAvailabilitySerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source='doctor.name', read_only=True)
    
    class Meta:
        model = DoctorAvailability
        fields = ['id', 'doctor', 'doctor_name', 'date', 'start_time', 'end_time', 'is_available']


class LocationOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = LocationOption
        fields = ['id', 'name', 'subcategory']


class AppointmentSubcategorySerializer(serializers.ModelSerializer):
    locations = LocationOptionSerializer(many=True, read_only=True)
    
    class Meta:
        model = AppointmentSubcategory
        fields = ['id', 'name', 'category', 'locations', 'specialties']


class AppointmentCategorySerializer(serializers.ModelSerializer):
    subcategories = AppointmentSubcategorySerializer(many=True, read_only=True)
    
    class Meta:
        model = AppointmentCategory
        fields = ['id', 'name', 'subcategories', 'specialties']


class AppointmentSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source='doctor.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    subcategory_name = serializers.CharField(source='subcategory.name', read_only=True)
    location_name = serializers.CharField(source='location.name', read_only=True, allow_null=True)
    
    class Meta:
        model = Appointment
        fields = [
            'id', 'user', 'doctor', 'doctor_name', 'appointment_date', 'appointment_time',
            'category', 'category_name', 'subcategory', 'subcategory_name',
            'location', 'location_name', 'patient_name', 'patient_phone',
            'patient_email', 'status', 'notes', 'created_at'
        ]


class HealthMetricsSerializer(serializers.ModelSerializer):
    class Meta:
        model = HealthMetrics
        fields = '__all__'
        read_only_fields = ('user', 'timestamp', 'bmi', 'health_score')

    def validate(self, data):
        errors = {}
        if 'systolic_bp' in data and 'diastolic_bp' in data:
            if data['systolic_bp'] < data['diastolic_bp']:
                errors['blood_pressure'] = "Systolic must be higher than diastolic"
        if errors:
            raise serializers.ValidationError(errors)
        return data