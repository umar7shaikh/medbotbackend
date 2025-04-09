# chatbot_handler.py
import logging
import json
from datetime import datetime
import time
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from PIL import Image
from io import BytesIO
import os

from .ai_processor import AIPromptProcessor
from .speech_processor import SpeechProcessor
from .medical_image_analyzer import MedicalImageAnalyzer

class ChatbotHandler:
    def __init__(self):
        """
        Initialize the unified chatbot handler that processes different input types.
        """
        self.logger = logging.getLogger(__name__)
        self.ai_processor = AIPromptProcessor()
        self.speech_processor = SpeechProcessor()
        self.image_analyzer = MedicalImageAnalyzer()
        
        # Initialize conversation history as structured format
        self.conversation_history = []
        
        # Maximum number of previous exchanges to include as context
        self.max_context_exchanges = 5
        
        # Maximum context length in characters
        self.max_context_length = 2000

    def _save_image(self, image_data):
        """
        Save uploaded image to temporary storage
        
        Args:
            image_data: The uploaded image data
            
        Returns:
            str: Path to saved image
        """
        try:
            if isinstance(image_data, Image.Image):
                # If already a PIL Image object
                img = image_data
            else:
                # Handle binary image data
                img = Image.open(BytesIO(image_data))
                
            # Save to temp location
            path = default_storage.save(
                f'temp_images/{settings.TEMP_IMAGE_PREFIX}_{hash(str(img))}.jpg', 
                ContentFile(BytesIO(img.tobytes()).getvalue())
            )
            return path
        except Exception as e:
            self.logger.error(f"Error saving image: {e}")
            return None
    
    def _build_context_from_history(self):
        """
        Build context string from conversation history
        
        Returns:
            str: Formatted context for AI
        """
        if not self.conversation_history:
            return ""
        
        # Get the most recent exchanges (limited by max_context_exchanges)
        recent_exchanges = self.conversation_history[-self.max_context_exchanges:]
        
        # Build context string
        context_parts = []
        total_length = 0
        
        # Start from the most recent and go backwards until we hit the length limit
        for exchange in reversed(recent_exchanges):
            exchange_text = f"User: {exchange['user']}\nAssistant: {exchange['assistant']}\n\n"
            exchange_length = len(exchange_text)
            
            # Check if adding this exchange would exceed the max length
            if total_length + exchange_length > self.max_context_length:
                break
                
            context_parts.insert(0, exchange_text)  # Insert at beginning to maintain chronological order
            total_length += exchange_length
        
        # Join all parts and return
        return "".join(context_parts).strip()

    def process_query(self, text=None, voice=None, image=None):
        """
        Process user query based on available inputs.
        
        Args:
            text (str, optional): Text input from user
            voice (file, optional): Voice input from user
            image (file, optional): Image input from user
            
        Returns:
            dict: Response with text, audio file path, and additional info
        """
        text_query = ""
        image_description = ""
        detected_language = "en"  # Default language

        # Process voice input if available
        if voice and not text:
            # Save voice temporarily
            voice_path = default_storage.save(f'temp_audio/input_{abs(hash(str(voice)))}.wav', ContentFile(voice.read()))
            
            # Get full path to the file
            full_voice_path = os.path.join(settings.MEDIA_ROOT, voice_path)
            
            # Convert speech to text and get the detected language
            speech_result = self.speech_processor.speech_to_text(full_voice_path)
            
            if speech_result:
                text_query = speech_result.get('text', '')
                detected_language = speech_result.get('language', 'en')
            else:
                text_query = "Could not understand audio"
            
            # Clean up temp file
            default_storage.delete(voice_path)

        # Process text input if available
        if text:
            text_query = text

        # Process image input if available
        if image:
            # Analyze the image
            image_result = self.image_analyzer.analyze_medical_image(Image.open(image))
            image_description = image_result.get('caption', image_result.get('error', 'No image description available'))

        # Combine text and image description into final query
        final_query = text_query

        if image_description:
            if final_query:
                final_query += f"\n\nThe medical image shows: {image_description}"
            else:
                final_query = f"Please analyze this medical image: {image_description}"

        # If no query could be formed, provide error message
        if not final_query:
            return {
                "text": "I couldn't process your request. Please provide text, voice, or an image to analyze.",
                "audio": None,
                "detected_language": detected_language
            }

        # Build context from previous conversation
        context = self._build_context_from_history()

        # Process through AI with context
        ai_response = self.ai_processor.generate_prompt(context, final_query)

        # Add this exchange to conversation history
        self.conversation_history.append({
            "user": final_query,
            "assistant": ai_response
        })

        # Generate speech in the detected language if input was voice
        audio_file = None
        if voice:
            audio_file = self.speech_processor.text_to_speech(ai_response, lang=detected_language)

        return {
            "text": ai_response,
            "audio": audio_file,
            "detected_language": detected_language  # Optional: return detected language
        }

    def reset_conversation(self):
        """Reset the conversation context"""
        self.conversation_history = []
        return {"status": "conversation reset"}
    
    def save_conversation(self, user_id=None):
        """
        Save the current conversation to a file
        
        Args:
            user_id (str, optional): User identifier
            
        Returns:
            str: Path to saved file
        """
        if not self.conversation_history:
            return None
            
        try:
            # Create a conversation record with metadata
            conversation_data = {
                "user_id": user_id or "anonymous",
                "timestamp": str(datetime.now()),
                "exchanges": self.conversation_history
            }
            
            # Generate filename
            filename = f"conversation_{user_id or 'anonymous'}_{int(time.time())}.json"
            
            # Save to file
            file_path = default_storage.save(
                f'conversations/{filename}',
                ContentFile(json.dumps(conversation_data, indent=2))
            )
            
            return file_path
            
        except Exception as e:
            self.logger.error(f"Error saving conversation: {e}")
            return None
    
    def load_conversation(self, file_path):
        """
        Load a conversation from a file
        
        Args:
            file_path (str): Path to conversation file
            
        Returns:
            bool: Success status
        """
        try:
            with default_storage.open(file_path, 'r') as f:
                conversation_data = json.loads(f.read())
                
            self.conversation_history = conversation_data.get("exchanges", [])
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading conversation: {e}")
            return False