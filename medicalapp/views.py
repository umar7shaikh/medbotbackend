from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Conversation, Message, MedicalImage
from ai_utils.speech_processor import SpeechProcessor
from ai_utils.medical_image_analyzer import MedicalImageAnalyzer
from django.http import JsonResponse
import os
from PIL import Image
from django.utils import timezone
from django.conf import settings
from dotenv import load_dotenv
from django.contrib.auth import authenticate, login
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
from ai_utils.ai_processor import AIPromptProcessor
from ai_utils.speech_processor import SpeechProcessor
from django.contrib.auth.models import User  # Add this import

# Helper function to get default user
def get_default_user():
    return User.objects.first()  # Get the first user in the database

@csrf_exempt
def login_view(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            username = data.get("username")
            password = data.get("password")

            if not username or not password:
                return JsonResponse({"error": "Username and password required"}, status=400)

            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return JsonResponse({
                    "message": "Login successful",
                    "user": user.username,
                    "sessionid": request.session.session_key
                })
            else:
                return JsonResponse({"error": "Invalid credentials"}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)

    return render(request, "medicalapp/login.html")

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Initialize AI and Speech Processors
ai_processor = AIPromptProcessor(api_key=settings.GROQ_API_KEY)
speech_processor = SpeechProcessor()

def chatbot_ui(request):
    """Render the chatbot HTML page."""
    return render(request, "medicalapp/chatbot.html")

@csrf_exempt
def start_conversation(request):
    """
    Handles:
    - Speech-to-Text (STT)
    - AI response with context
    - Text-to-Speech (TTS)
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body) if request.body else {}
            conversation_id = data.get('conversation_id')
            
            # Get or create conversation with default user
            conversation = None
            default_user = get_default_user()
            
            if conversation_id:
                try:
                    conversation = Conversation.objects.get(id=conversation_id)
                except Conversation.DoesNotExist:
                    conversation = Conversation.objects.create(user=default_user)
            else:
                conversation = Conversation.objects.create(user=default_user)

            # Build conversation context
            conversation_context = ""
            if conversation:
                previous_messages = conversation.messages.order_by('-timestamp')[:5]
                if previous_messages:
                    conversation_context = "Previous conversation:\n"
                    for msg in reversed(previous_messages):
                        conversation_context += f"{'Patient' if msg.sender == 'user' else 'Doctor'}: {msg.content}\n"

            # Speech-to-Text (STT)
            if "audio_file" in request.FILES:
                audio_file = request.FILES["audio_file"]
                transcript = speech_processor.speech_to_text(audio_file)
                
                if transcript:
                    ai_response = ai_processor.generate_prompt(conversation_context, transcript)
                    
                    # Save conversation
                    Message.objects.create(
                        conversation=conversation,
                        content=transcript,
                        sender='user'
                    )
                    
                    Message.objects.create(
                        conversation=conversation,
                        content=ai_response,
                        sender='ai'
                    )
                    
                    # Convert AI response to speech
                    audio_path = speech_processor.text_to_speech(ai_response)
                    
                    response_data = {
                        "ai_response": ai_response,
                        "transcript": transcript,
                        "audio_url": request.build_absolute_uri(f"/media/{audio_path}"),
                        "conversation_id": conversation.id
                    }
                    
                    return JsonResponse(response_data)

                return JsonResponse({"error": "Speech not recognized"}, status=400)

            # Text Query (Regular AI Chat)
            if "query" in data:
                user_query = data["query"]
                ai_response = ai_processor.generate_prompt(conversation_context, user_query)
                
                # Save conversation
                Message.objects.create(
                    conversation=conversation,
                    content=user_query,
                    sender='user'
                )
                
                Message.objects.create(
                    conversation=conversation,
                    content=ai_response,
                    sender='ai'
                )
                
                response_data = {
                    "ai_response": ai_response,
                    "conversation_id": conversation.id
                }
                    
                return JsonResponse(response_data)

            return JsonResponse({"error": "Invalid request format"}, status=400)

        except Exception as e:
            return JsonResponse({"error": f"Server error: {str(e)}"}, status=500)

    return JsonResponse({"error": "Only POST method allowed"}, status=405)

@csrf_exempt
def process_voice_message(request):
    """
    Process voice recording and return transcription with AI response
    """
    if request.method != 'POST':
        return JsonResponse({"error": "Only POST method allowed"}, status=405)
        
    try:
        # Initialize speech processor
        speech_proc = SpeechProcessor()
        default_user = get_default_user()
        
        # Check if audio file is provided
        if 'audio' not in request.FILES:
            return JsonResponse({"error": "No audio file provided"}, status=400)
            
        # Get language parameter (default to None for auto-detection)
        language = request.POST.get('language')
        
        # Check if this is a transcription-only request
        transcription_only = request.POST.get('transcription_only') == 'true'
        
        # Process speech to text
        text = speech_proc.speech_to_text(
            audio_file=request.FILES.get('audio'),
            language=language
        )
        
        if not text:
            return JsonResponse({"error": "No speech detected or could not recognize speech"}, status=400)
            
        # If transcription only, return the text without AI processing
        if transcription_only:
            return JsonResponse({
                "user_message": text,
                "transcription_only": True
            })
        
        # Process with AI for full response
        ai_proc = AIPromptProcessor(api_key=settings.GROQ_API_KEY)
        
        # Get conversation context if conversation_id is provided
        conversation_id = request.POST.get('conversation_id')
        conversation_context = ""
        conversation = None
        
        if conversation_id:
            try:
                conversation = Conversation.objects.get(id=conversation_id)
                previous_messages = conversation.messages.order_by('-timestamp')[:5]
                
                if previous_messages:
                    conversation_context = "Previous conversation:\n"
                    for msg in reversed(previous_messages):
                        conversation_context += f"{'Patient' if msg.sender == 'user' else 'Doctor'}: {msg.content}\n"
            except Conversation.DoesNotExist:
                # Create new conversation
                conversation = Conversation.objects.create(user=default_user)
        else:
            # Create new conversation
            conversation = Conversation.objects.create(user=default_user)
        
        # Generate AI response
        ai_response = ai_proc.generate_prompt(conversation_context, text)
        
        # Save messages
        Message.objects.create(
            conversation=conversation,
            content=text,
            sender='user'
        )
        
        Message.objects.create(
            conversation=conversation,
            content=ai_response,
            sender='ai'
        )
        
        # Include conversation_id in response
        response_data = {
            "user_message": text,
            "ai_response": ai_response,
            "conversation_id": conversation.id
        }
        
        # Optional: Generate audio response
        audio_path = speech_proc.text_to_speech(ai_response)
        if audio_path:
            response_data["audio_url"] = request.build_absolute_uri(f"/media/{audio_path}")
        
        return JsonResponse(response_data)
        
    except Exception as e:
        import traceback
        print(f"Voice processing error: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({"error": f"Server error: {str(e)}"}, status=500)
    
@csrf_exempt
def upload_medical_image(request):
    """
    Upload medical image and analyze using Hugging Face API with enhanced AI interpretation.
    """
    try:
        # Get default user
        default_user = get_default_user()
        
        # Create or get conversation
        conversation_id = request.POST.get('conversation_id')
        if conversation_id:
            try:
                conversation = Conversation.objects.get(id=conversation_id)
            except Conversation.DoesNotExist:
                conversation = Conversation.objects.create(user=default_user)
        else:
            conversation = Conversation.objects.create(user=default_user)
            
        # Get uploaded image
        image_file = request.FILES.get("image")
        if not image_file:
            return JsonResponse({"error": "No image uploaded"}, status=400)

        # Open image
        image = Image.open(image_file)
        
        # Debug image info
        print(f"Image format: {image.format}, size: {image.size}, mode: {image.mode}")

        # Initialize medical image analyzer
        medical_analyzer = MedicalImageAnalyzer()

        # Analyze image using BLIP (Image Captioning)
        analysis_result = medical_analyzer.analyze_medical_image(image)
        
        # Debug analysis result
        print(f"Analysis result: {analysis_result}")

        # Handle analysis errors
        if 'error' in analysis_result:
            return JsonResponse({
                "error": analysis_result['error'],
                "ai_interpretation": "Failed to analyze image. Please try again."
            }, status=500)

        # Extract caption
        image_caption = analysis_result.get("caption", "No description available")

        # Initialize AI processor to generate a medical response based on the image caption
        ai_processor = AIPromptProcessor()
        ai_response = ai_processor.generate_prompt(
            "",
            f"Medical Image Description: {image_caption}. Provide a medical assessment and possible treatments."
        )
        
        # Save the image to database
        medical_image = MedicalImage.objects.create(
            conversation=conversation,
            image=image_file,
            analysis_result=json.dumps(analysis_result)
        )

        return JsonResponse({
            "image_caption": image_caption,
            "ai_interpretation": ai_response,
            "conversation_id": conversation.id
        })

    except Exception as e:
        print(f"Image upload error: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)
    

@csrf_exempt
@require_POST
def process_conversation(request):
    """
    Process user medical query with context and return AI response
    """
    try:
        data = json.loads(request.body)
        query = data.get("query", "").strip()
        conversation_id = data.get("conversation_id")
        default_user = get_default_user()

        if not query:
            return JsonResponse({"error": "Query cannot be empty"}, status=400)

        # Initialize AI Processor
        ai_processor = AIPromptProcessor(api_key=settings.GROQ_API_KEY)

        # Define a medical-specific prompt
        base_context = (
            "You are a professional AI medical assistant. "
            "Your goal is to provide accurate, medically relevant answers in simple terms. "
            "If symptoms are serious, advise consulting a doctor. Do NOT give misleading or harmful advice."
        )
        
        # Get conversation context if conversation_id is provided
        conversation_context = ""
        conversation = None
        
        if conversation_id:
            try:
                conversation = Conversation.objects.get(id=conversation_id)
                # Get the last 5 messages
                previous_messages = conversation.messages.order_by('-timestamp')[:5]
                
                if previous_messages:
                    conversation_context = "\n\nPrevious conversation:\n"
                    for msg in reversed(previous_messages):
                        conversation_context += f"{'Patient' if msg.sender == 'user' else 'Doctor'}: {msg.content}\n"
            except Conversation.DoesNotExist:
                # Create a new conversation
                conversation = Conversation.objects.create(user=default_user)
        else:
            # Create new conversation
            conversation = Conversation.objects.create(user=default_user)

        # Generate AI response with combined context
        ai_response = ai_processor.generate_prompt(
            context=base_context + conversation_context, 
            query=f"Patient's concern: {query}\n\nMedical AI Response:"
        )

        # Save the conversation messages
        # Save user message
        Message.objects.create(
            conversation=conversation,
            content=query,
            sender='user'
        )
        
        # Save AI response
        Message.objects.create(
            conversation=conversation,
            content=ai_response,
            sender='ai'
        )
        
        return JsonResponse({
            "ai_response": ai_response,
            "conversation_id": conversation.id
        })

    except Exception as e:
        print(f"Process conversation error: {str(e)}")
        return JsonResponse({"error": "An error occurred while processing your request"}, status=500)
    

@csrf_exempt
def unified_chatbot_handler(request):
    """
    Unified endpoint with context handling for all types of medical queries
    """
    try:
        # Initialize processors
        ai_processor = AIPromptProcessor(api_key=settings.GROQ_API_KEY)
        speech_processor = SpeechProcessor()
        image_analyzer = MedicalImageAnalyzer()
        default_user = get_default_user()
        
        # Get conversation ID if it exists
        conversation_id = None
        if request.method == 'POST' and request.content_type and 'application/json' in request.content_type:
            try:
                json_data = json.loads(request.body)
                conversation_id = json_data.get('conversation_id')
                text_query = json_data.get('query', '')
            except json.JSONDecodeError:
                text_query = None
        else:
            # Process form data
            conversation_id = request.POST.get('conversation_id')
            text_query = request.POST.get('text')
        
        # Get or create conversation
        if conversation_id:
            try:
                conversation = Conversation.objects.get(id=conversation_id)
            except Conversation.DoesNotExist:
                conversation = Conversation.objects.create(user=default_user)
        else:
            conversation = Conversation.objects.create(user=default_user)
            
        # Variables to store different input types
        voice_transcript = None
        image_caption = None
        
        # Process voice input if available
        if 'audio' in request.FILES or 'voice' in request.FILES:
            audio_file = request.FILES.get('audio') or request.FILES.get('voice')
            voice_transcript = speech_processor.speech_to_text(audio_file=audio_file)
        
        # Process image if available
        if 'image' in request.FILES:
            # IMPORTANT: Don't read or process the file here, just pass the file object
            image_file = request.FILES.get('image')
            # Use the image file object directly - don't read contents as text
            analysis_result = image_analyzer.analyze_medical_image(image_file)
            
            if 'caption' in analysis_result:
                image_caption = analysis_result['caption']
                
                # Save medical image
                MedicalImage.objects.create(
                    conversation=conversation,
                    image=image_file,
                    analysis_result=json.dumps(analysis_result)
                )
            elif 'error' in analysis_result:
                return JsonResponse({"error": f"Image analysis failed: {analysis_result['error']}"}, status=400)
        
        # Combine all inputs into a comprehensive query
        final_query = ""
        
        # Add text query if available
        if text_query and text_query.strip():
            final_query += text_query.strip()
        
        # Add voice transcript if available
        if voice_transcript and not text_query:
            final_query += voice_transcript
        
        # Add image caption to the query if available
        if image_caption:
            if final_query:
                final_query += f"\n\nThe uploaded medical image shows: {image_caption}"
            else:
                final_query = f"Please analyze this medical image description: {image_caption}"
        
        # Verify we have a query to process
        if not final_query.strip():
            return JsonResponse({
                "error": "No valid input provided. Please provide text, voice, or image."
            }, status=400)
        
        # Generate AI response 
        ai_response = ai_processor.generate_prompt(
            context="You are a professional AI medical assistant.",
            query=f"Patient's information: {final_query}\n\nMedical AI Response:"
        )
        
        # Save user query and AI response
        Message.objects.create(
            conversation=conversation,
            content=final_query,
            sender='user'
        )
        
        Message.objects.create(
            conversation=conversation,
            content=ai_response,
            sender='ai'
        )
        
        # Create response data
        response_data = {
            "ai_response": ai_response,
            "conversation_id": conversation.id
        }
        
        if image_caption:
            response_data["image_caption"] = image_caption
            
        return JsonResponse(response_data)
        
    except Exception as e:
        import traceback
        stack_trace = traceback.format_exc()
        print(f"Unified chatbot error: {str(e)}\nStack trace: {stack_trace}")
        return JsonResponse({"error": str(e)}, status=500)
    

@csrf_exempt
def manage_conversations(request):
    """
    Get user's conversations or delete a conversation
    """
    default_user = get_default_user()
    
    if request.method == "GET":
        # Get all conversations for default user
        conversations = Conversation.objects.filter(
            user=default_user
        ).order_by('-last_interaction')
        
        result = []
        for conv in conversations:
            # Get first message as preview
            first_message = conv.messages.filter(sender='user').first()
            message_preview = first_message.content[:50] if first_message else "No messages"
            
            result.append({
                "id": conv.id,
                "start_time": conv.start_time,
                "last_interaction": conv.last_interaction,
                "message_count": conv.messages.count(),
                "preview": message_preview
            })
        
        return JsonResponse({"conversations": result})
        
    elif request.method == "DELETE":
        # Delete a conversation
        try:
            data = json.loads(request.body)
            conversation_id = data.get("conversation_id")
            
            if not conversation_id:
                return JsonResponse({"error": "Conversation ID required"}, status=400)
                
            # Get conversation
            conversation = Conversation.objects.get(id=conversation_id)
            conversation.delete()
            
            return JsonResponse({"message": "Conversation deleted successfully"})
            
        except Conversation.DoesNotExist:
            return JsonResponse({"error": "Conversation not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    
    return JsonResponse({"error": "Method not allowed"}, status=405)




# Add to medicalapp/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Medication, MedicationLog
from .serializers import MedicationSerializer, MedicationLogSerializer
from django.contrib.auth.decorators import login_required
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from datetime import datetime, date, timedelta

# Medication viewset for RESTful API
class MedicationViewSet(viewsets.ModelViewSet):
    serializer_class = MedicationSerializer
    # authentication_classes = [TokenAuthentication, SessionAuthentication]
    # permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Since we're removing authentication, we need to handle unauthenticated users
        if self.request.user.is_authenticated:
            return Medication.objects.filter(user=self.request.user).order_by('next_dose')
        else:
            # Return all medications or an empty queryset for unauthenticated users
            # For development purposes, you might want to return all medications
            return Medication.objects.all().order_by('next_dose')
    
    def perform_create(self, serializer):
        from django.contrib.auth.models import User
        default_user = User.objects.first()  # Get the first user in database
        serializer.save(user=default_user)
    
    @action(detail=True, methods=['post'])
    def mark_as_taken(self, request, pk=None):
        medication = self.get_object()
        medication.status = 'taken'
        medication.save()
        
        # Create a log entry
        MedicationLog.objects.create(
            medication=medication,
            taken_at=timezone.now(),
            status='taken',
            notes=request.data.get('notes', '')
        )
        
        return Response({
            'status': 'success',
            'message': 'Medication marked as taken',
            'medication': MedicationSerializer(medication).data
        })
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get all medications due today"""
         # Get today's date
        today = timezone.now().date()
    
         # Get all medications regardless of status (not just 'upcoming')
         # This ensures medications remain visible after being marked as taken
        today_meds = self.get_queryset()
    
        # You can add additional filtering if needed, like:
        # today_meds = today_meds.filter(next_dose_date=today)
        # But for simplicity, we're showing all medications
        
        serializer = self.get_serializer(today_meds, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get medication statistics"""
        queryset = self.get_queryset()
        total = queryset.count()
        upcoming = queryset.filter(status='upcoming').count()
        taken = queryset.filter(status='taken').count()
        missed = queryset.filter(status='missed').count()
        
        # Calculate refill reminders
        today = date.today()
        refill_soon = queryset.filter(refill_date__lte=today + timedelta(days=7)).count()
        
        return Response({
            'total': total,
            'upcoming': upcoming,
            'taken': taken,
            'missed': missed,
            'refill_soon': refill_soon
        })

# Medication logs viewset
class MedicationLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = MedicationLogSerializer
    # authentication_classes = [TokenAuthentication, SessionAuthentication]
    # permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return MedicationLog.objects.all().order_by('-taken_at')    

# JSON API for medication management
@csrf_exempt
@login_required
def medication_api(request):
    """Handle medication CRUD operations"""
    if request.method == "GET":
        medications = Medication.objects.all()
        data = []
        for med in medications:
            data.append({
                "id": med.id,
                "name": med.name,
                "instructions": med.instructions,
                "next_dose": med.next_dose.strftime("%H:%M"),
                "refill_date": med.refill_date.strftime("%Y-%m-%d"),
                "remaining": med.remaining,
                "status": med.status
            })
        return JsonResponse({"medications": data})
    
    elif request.method == "POST":
        try:
            data = json.loads(request.body)
            
            # Create new medication
            medication = Medication.objects.create(
                user=request.user,
                name=data.get("name"),
                instructions=data.get("instructions"),
                next_dose=datetime.strptime(data.get("next_dose"), "%H:%M").time(),
                refill_date=datetime.strptime(data.get("refill_date"), "%Y-%m-%d").date(),
                remaining=data.get("remaining"),
                status=data.get("status", "upcoming")
            )
            
            return JsonResponse({
                "message": "Medication added successfully",
                "medication_id": medication.id
            })
            
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    
    elif request.method == "PUT":
        try:
            data = json.loads(request.body)
            medication_id = data.get("id")
            
            if not medication_id:
                return JsonResponse({"error": "Medication ID required"}, status=400)
            
            # Get medication and verify ownership
            medication = Medication.objects.get(id=medication_id, user=request.user)
            
            # Update fields
            if "name" in data:
                medication.name = data["name"]
            if "instructions" in data:
                medication.instructions = data["instructions"]
            if "next_dose" in data:
                medication.next_dose = datetime.strptime(data["next_dose"], "%H:%M").time()
            if "refill_date" in data:
                medication.refill_date = datetime.strptime(data["refill_date"], "%Y-%m-%d").date()
            if "remaining" in data:
                medication.remaining = data["remaining"]
            if "status" in data:
                medication.status = data["status"]
                
                # Create log entry if status changed to taken
                if data["status"] == "taken":
                    MedicationLog.objects.create(
                        medication=medication,
                        status="taken",
                        notes=data.get("notes", "")
                    )
            
            medication.save()
            
            return JsonResponse({"message": "Medication updated successfully"})
            
        except Medication.DoesNotExist:
            return JsonResponse({"error": "Medication not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    
    elif request.method == "DELETE":
        try:
            data = json.loads(request.body)
            medication_id = data.get("id")
            
            if not medication_id:
                return JsonResponse({"error": "Medication ID required"}, status=400)
            
            # Get medication and verify ownership
            medication = Medication.objects.get(id=medication_id, user=request.user)
            medication.delete()
            
            return JsonResponse({"message": "Medication deleted successfully"})
            
        except Medication.DoesNotExist:
            return JsonResponse({"error": "Medication not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    
    return JsonResponse({"error": "Method not allowed"}, status=405)