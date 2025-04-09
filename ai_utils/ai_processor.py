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
        self.api_key = api_key or settings.GROQ_API_KEY
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        
        # Maximum token limit for combined context and query
        self.max_context_tokens = 4000

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
        # Remove asterisks (*)
        sanitized = re.sub(r'\*+', '', sanitized)
        
        return sanitized.strip()
    
    def _estimate_token_count(self, text):
        """
        Roughly estimate token count (1 token ~= 4 characters for English text)
        
        Args:
            text (str): Input text
            
        Returns:
            int: Estimated token count
        """
        return len(text) // 4
    
    def _is_likely_medical_query(self, query):
        """
        Basic check if query is likely medical-related
        This is a simple fallback since we don't have the validator class
        
        Args:
            query (str): User query
            
        Returns:
            bool: True if likely medical, False otherwise
        """
        query = query.lower()
        
        # Common medical keywords
        medical_keywords = [
            'health', 'doctor', 'symptom', 'disease', 'condition', 'treatment',
            'medicine', 'drug', 'prescription', 'diagnosis', 'therapy', 'pain',
            'hospital', 'clinic', 'medical', 'healthcare', 'patient', 'physician',
            'nurse', 'surgery', 'exam', 'test', 'blood', 'heart', 'lung', 'brain',
            'cancer', 'diabetes', 'infection', 'virus', 'bacteria', 'injury'
        ]
        
        # Non-medical topics
        non_medical_topics = [
            'politics', 'entertainment', 'sports', 'finance', 'investment',
            'stock market', 'celebrity', 'movie', 'game', 'music', 'art'
        ]
        
        # Quick rejection
        for topic in non_medical_topics:
            if topic in query:
                return False
                
        # Check for medical keywords
        for keyword in medical_keywords:
            if keyword in query:
                return True
        
        # If image analysis request, consider it medical
        if "image" in query and any(term in query for term in ["analyze", "scan", "x-ray", "mri", "ct"]):
            return True
            
        # Default to letting the AI decide (will be filtered by system prompt)
        return True

    def generate_prompt(self, context, query, max_tokens=1000):
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
            # Basic check - if clearly non-medical, reject early
            if not self._is_likely_medical_query(query):
                return ("I'm a medical assistant designed to help with health-related questions only. "
                        "Please ask me about medical conditions, symptoms, treatments, or general health advice.")
            
            # Enhanced system prompt to strictly restrict to medical topics
            system_prompt = """
            You are a specialized medical assistant. Your ONLY purpose is to provide medical information and support.
            
            STRICT OPERATIONAL GUIDELINES:
            1. ONLY respond to health and medical queries
            2. For ANY non-medical topics, politely redirect: "I'm a medical assistant and can only help with health-related questions."
            3. For medical topics, provide evidence-based, accurate, and empathetic responses
            4. Use previous conversation context to provide personalized assistance
            5. Always include appropriate medical disclaimers when needed
            6. Be concise and clear in your medical explanations
            7. Encourage users to seek professional medical advice for diagnosis or treatment
            
            If ANYTHING in the query is not health-related, politely decline to respond with the redirect message.
            """
            
            # Format the context properly if it exists
            context_prompt = ""
            if context:
                context_prompt = f"Previous conversation history:\n{context}\n\n"
                
                # Check if context is too long and might exceed token limits
                estimated_tokens = self._estimate_token_count(context_prompt + query)
                if estimated_tokens > self.max_context_tokens:
                    # Truncate context if needed (rough approximation)
                    max_chars = len(context_prompt) - (estimated_tokens - self.max_context_tokens) * 4
                    context_prompt = f"Previous conversation history (truncated):\n{context[:max_chars]}...\n\n"
            
            # Combine context with current query
            combined_prompt = f"{context_prompt}New medical query: {query}"
            
            payload = {
                "messages": [
                    {
                        "role": "system", 
                        "content": system_prompt
                    },
                    {
                        "role": "user", 
                        "content": combined_prompt
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
                return self._sanitize_response(ai_response)
            else:
                print(f"AI API Error: {response.text}")
                return f"AI Error: {response.json().get('error', {}).get('message', 'Unknown error')}"

        except Exception as e:
            print(f"AI Prompt Processing Error: {e}")
            return "An error occurred while processing your medical request."