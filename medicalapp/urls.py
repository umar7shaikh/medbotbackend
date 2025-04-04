app_name = "medicalapp"

from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'), 
    path("chatbot/", views.chatbot_ui, name="chatbot_ui"), 
    path('conversation/start/', views.start_conversation, name='start_conversation'),
    path('conversation/<int:conversation_id>/voice/', views.process_voice_message, name='process_voice_message'),
    path('conversation/upload-image/', views.upload_medical_image, name='upload_medical_image'),
    path('conversation/process/', views.process_conversation, name='process_conversation'),
    path('chatbot/query/', views.unified_chatbot_handler, name='unified_chatbot'),
    path('conversations/manage/', views.manage_conversations, name='manage_conversations'),
]