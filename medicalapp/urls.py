app_name = "medicalapp"


from rest_framework.routers import DefaultRouter
from .views import MedicationViewSet, MedicationLogViewSet
from django.urls import path,include
from . import views


# Create router for REST framework
router = DefaultRouter()
router.register(r'medications', MedicationViewSet, basename='medication')
router.register(r'medication-logs', MedicationLogViewSet, basename='medication-log')
router.register(r'medical-specialties', views.MedicalSpecialtyViewSet)
router.register(r'doctors', views.DoctorViewSet)
router.register(r'appointment-categories', views.AppointmentCategoryViewSet)
router.register(r'appointment-subcategories', views.AppointmentSubcategoryViewSet)
router.register(r'appointments', views.AppointmentViewSet, basename='appointment')

urlpatterns = [
    path('login/', views.login_view, name='login'), 
    path("chatbot/", views.chatbot_ui, name="chatbot_ui"), 
    path('conversation/start/', views.start_conversation, name='start_conversation'),
    path('conversation/voice/', views.process_voice_message, name='process_voice_message'),
    path('conversation/upload-image/', views.upload_medical_image, name='upload_medical_image'),
    path('conversation/process/', views.process_conversation, name='process_conversation'),
    path('chatbot/query/', views.unified_chatbot_handler, name='unified_chatbot'),
    path('conversations/manage/', views.manage_conversations, name='manage_conversations'),
    path('api/', include(router.urls)),
    path('api/medication-management/', views.medication_api, name='medication_api'),
    path('api/appointment-chatbot/', views.appointment_chatbot, name='appointment-chatbot'),
]