# medicalapp/admin.py
from django.contrib import admin
from .models import Conversation, Message, MedicalImage, Medication, MedicationLog,MedicalSpecialty, Doctor, DoctorAvailability, AppointmentCategory,AppointmentSubcategory, LocationOption, Appointment


# Register your models here
admin.site.register(Conversation)
admin.site.register(Message)
admin.site.register(MedicalImage)

@admin.register(Medication)
class MedicationAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'next_dose', 'status', 'refill_date', 'remaining')
    list_filter = ('status', 'refill_date')
    search_fields = ('name', 'user__username')

@admin.register(MedicationLog)
class MedicationLogAdmin(admin.ModelAdmin):
    list_display = ('medication', 'taken_at', 'status')
    list_filter = ('status', 'taken_at')
    search_fields = ('medication__name', 'medication__user__username')

#  Admin classes with improved display
@admin.register(MedicalSpecialty)
class MedicalSpecialtyAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ['name', 'specialty', 'is_active', 'languages']
    list_filter = ['specialty', 'is_active']
    search_fields = ['name', 'specialty__name']

@admin.register(DoctorAvailability)
class DoctorAvailabilityAdmin(admin.ModelAdmin):
    list_display = ['doctor', 'date', 'start_time', 'end_time', 'is_available']
    list_filter = ['date', 'is_available', 'doctor']
    date_hierarchy = 'date'

@admin.register(AppointmentCategory)
class AppointmentCategoryAdmin(admin.ModelAdmin):
    list_display = ['name']
    filter_horizontal = ['specialties']

@admin.register(AppointmentSubcategory)
class AppointmentSubcategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category']
    list_filter = ['category']
    filter_horizontal = ['specialties']

@admin.register(LocationOption)
class LocationOptionAdmin(admin.ModelAdmin):
    list_display = ['name', 'subcategory']
    list_filter = ['subcategory']

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['patient_name', 'doctor', 'appointment_date', 'appointment_time', 'status']
    list_filter = ['status', 'appointment_date', 'doctor']
    date_hierarchy = 'appointment_date'
    search_fields = ['patient_name', 'patient_email', 'doctor__name']
