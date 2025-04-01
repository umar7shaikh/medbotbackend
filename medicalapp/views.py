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
from ai_utils.ai_processor import AIPromptProcessor  # Correct import path
from ai_utils.speech_processor import SpeechProcessor  # Assuming this exists

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
                    "sessionid": request.session.session_key  # ✅ Send session ID
                })
            else:
                return JsonResponse({"error": "Invalid credentials"}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)

    # ✅ Serve an HTML page when accessed via GET
    return render(request, "medicalapp/login.html")


load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")


# Initialize AI and Speech Processors
ai_processor = AIPromptProcessor(api_key=settings.GROQ_API_KEY)  # ✅ Pass API key correctly
speech_processor = SpeechProcessor()

def chatbot_ui(request):
    """Render the chatbot HTML page."""
    return render(request, "medicalapp/chatbot.html")

@csrf_exempt
def start_conversation(request):
    """
    Handles:
    - Speech-to-Text (STT)
    - AI response
    - Text-to-Speech (TTS)
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body) if request.body else {}

            # Speech-to-Text (STT)
            if "audio_file" in request.FILES:
                audio_file = request.FILES["audio_file"]
                transcript = speech_processor.speech_to_text(audio_file)
                
                if transcript:
                    ai_response = ai_processor.generate_prompt("", transcript)
                    
                    # Convert AI response to speech
                    audio_path = speech_processor.text_to_speech(ai_response)
                    
                    return JsonResponse({
                        "ai_response": ai_response,
                        "transcript": transcript,
                        "audio_url": request.build_absolute_uri(f"/media/{audio_path}")  # Frontend can play this
                    })

                return JsonResponse({"error": "Speech not recognized"}, status=400)

            # Text Query (Regular AI Chat)
            if "query" in data:
                user_query = data["query"]
                ai_response = ai_processor.generate_prompt("", user_query)

                return JsonResponse({"ai_response": ai_response})

            return JsonResponse({"error": "Invalid request format"}, status=400)

        except Exception as e:
            return JsonResponse({"error": f"Server error: {str(e)}"}, status=500)

    return JsonResponse({"error": "Only POST method allowed"}, status=405)

def process_voice_message(request, conversation_id):
    if request.method == 'POST':
        # Use the speech processor to convert speech to text
        speech_proc = SpeechProcessor()
        text = speech_proc.speech_to_text(audio_file=request.FILES.get('audio'))
        
        if text:
            # Save user message
            conversation = Conversation.objects.get(id=conversation_id)
            user_message = Message.objects.create(
                conversation=conversation,
                content=text,
                sender='user'
            )
            
            # Process with AI - use settings API key
            ai_proc = AIPromptProcessor(api_key=settings.GROQ_API_KEY)
            context = " ".join(conversation.messages.values_list('content', flat=True)[:5])
            ai_response = ai_proc.generate_prompt(context, text)
            
            # Rest of the code...
            
            # Save AI message
            ai_message = Message.objects.create(
                conversation=conversation,
                content=ai_response,
                sender='ai'
            )
            
            # Optional: Convert AI response to speech
            speech_proc.text_to_speech(ai_response)
            
            return JsonResponse({
                'user_message': text,
                'ai_response': ai_response
            })
        
        return JsonResponse({'error': 'No speech detected'}, status=400)
    
@csrf_exempt
def upload_medical_image(request):
    """
    Upload medical image and analyze using Hugging Face API with enhanced AI interpretation.
    """
    try:
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
            }, status=500)  # Changed to 500 status to indicate server error

        # Extract caption
        image_caption = analysis_result.get("caption", "No description available")

        # Initialize AI processor to generate a medical response based on the image caption
        ai_processor = AIPromptProcessor()
        ai_response = ai_processor.generate_prompt(
            "",
            f"Medical Image Description: {image_caption}. Provide a medical assessment and possible treatments."
        )

        return JsonResponse({
            "image_caption": image_caption,
            "ai_interpretation": ai_response
        })

    except Exception as e:
        print(f"Image upload error: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
@require_POST
def process_conversation(request):
    """
    Process user medical query and return AI response
    """
    try:
        data = json.loads(request.body)
        query = data.get("query", "").strip()

        if not query:
            return JsonResponse({"error": "Query cannot be empty"}, status=400)

        # Initialize AI Processor
        ai_processor = AIPromptProcessor(api_key=settings.GROQ_API_KEY)

        # Define a medical-specific prompt
        context = (
            "You are a professional AI medical assistant. "
            "Your goal is to provide accurate, medically relevant answers in simple terms. "
            "If symptoms are serious, advise consulting a doctor. Do NOT give misleading or harmful advice."
        )

        # Generate AI response with proper context
        ai_response = ai_processor.generate_prompt(
            context=context, 
            query=f"Patient's concern: {query}\n\nMedical AI Response:"
        )

        # Log the response for debuggin

        return JsonResponse({"ai_response": ai_response})

    except Exception as e:

        return JsonResponse({"error": "An error occurred while processing your request"}, status=500)