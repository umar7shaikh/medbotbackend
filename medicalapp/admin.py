# medicalapp/admin.py
from django.contrib import admin
from .models import Conversation, Message, MedicalImage, Medication, MedicationLog

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