# chatbot_handler.py
import logging
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from PIL import Image
from io import BytesIO

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
        self.conversation_context = ""  # Store conversation history

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
        
        # Case 1 & 4: Process text input if available
        if text:
            text_query = text
        
        # Case 2 & 5: Process voice input if available
        if voice and not text:
            # Save voice temporarily
            voice_path = default_storage.save(f'temp_audio/input_{hash(str(voice))}.wav', ContentFile(voice.read()))
            # Convert speech to text
            text_query = self.speech_processor.speech_to_text(voice_path) or "Could not understand audio"
            # Clean up temp file
            default_storage.delete(voice_path)
        
        # Case 3, 4 & 5: Process image if available
        if image:
            # Analyze image
            image_result = self.image_analyzer.analyze_medical_image(Image.open(image))
            image_description = image_result.get('caption', image_result.get('error', 'No image description available'))
        
        # Combine inputs for final query
        final_query = text_query
        
        # Add image description to query if available
        if image_description:
            if final_query:
                final_query += f"\n\nThe medical image shows: {image_description}"
            else:
                final_query = f"Please analyze this medical image: {image_description}"
        
        # If no query could be formed, provide error message
        if not final_query:
            return {
                "text": "I couldn't process your request. Please provide text, voice, or an image to analyze.",
                "audio": None
            }
        
        # Process through AI
        ai_response = self.ai_processor.generate_prompt(self.conversation_context, final_query)
        
        # Update conversation context
        self.conversation_context += f"\nUser: {final_query}\nAssistant: {ai_response}\n"
        
        # Generate speech if input was voice
        audio_file = None
        if voice:
            audio_file = self.speech_processor.text_to_speech(ai_response)
        
        return {
            "text": ai_response,
            "audio": audio_file
        }

    def reset_conversation(self):
        """Reset the conversation context"""
        self.conversation_context = ""
        return {"status": "conversation reset"}