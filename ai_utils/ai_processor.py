import os
import requests
import re
from dotenv import load_dotenv
from django.conf import settings

# Load API key from .env
load_dotenv()

class AIPromptProcessor:
    def __init__(self, api_key=None):
        """
        Initialize AI Prompt Processor for Groq's Mixtral Model
        
        Args:
            api_key (str, optional): Groq API key
        """
        self.api_key = api_key or settings.GROQ_API_KEY  # ✅ Load from Django settings
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"  # ✅ Corrected URL

    def _sanitize_response(self, text):
        """
        Sanitize AI response to remove unwanted special characters
        
        Args:
            text (str): Raw AI response
            
        Returns:
            str: Sanitized response
        """
        # Remove control characters and other problematic special characters
        sanitized = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', text)
        # Replace multiple spaces with single space
        sanitized = re.sub(r'\s+', ' ', sanitized)
        # Remove any HTML/XML tags that might have been generated
        sanitized = re.sub(r'<[^>]+>', '', sanitized)
        return sanitized.strip()

    def generate_prompt(self, context, query, max_tokens=300):
        """
        Generate AI response using Groq's Mixtral model
        
        Args:
            context (str): Previous conversation context
            query (str): User's current query
            max_tokens (int): Maximum response length
        
        Returns:
            str: AI-generated response
        """
        if not self.api_key:
            return "AI Error: Missing API key!"

        try:
            # Enhance system prompt to strictly restrict to medical topics
            system_prompt = """
            You are a helpful medical assistant. Provide concise, accurate, and empathetic responses 
            ONLY to medical queries. If a question is not related to medicine, health, wellness, 
            or healthcare, politely decline to answer and explain that you're a medical assistant
            only trained to help with health-related questions.
            """
            
            payload = {
                "messages": [
                    {
                        "role": "system", 
                        "content": system_prompt
                    },
                    {
                        "role": "user", 
                        "content": f"Previous context: {context}\n\nNew medical query: {query}"
                    }
                ],
                "model": "llama-3.3-70b-versatile",
                "max_tokens": max_tokens,
                "temperature": 0.7
            }

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            response = requests.post(self.base_url, json=payload, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result['choices'][0]['message']['content']
                return self._sanitize_response(ai_response)  # Apply sanitization
            else:
                print(f"AI API Error: {response.text}")
                return f"AI Error: {response.json().get('error', {}).get('message', 'Unknown error')}"

        except Exception as e:
            print(f"AI Prompt Processing Error: {e}")
            return "An error occurred while processing your medical request."