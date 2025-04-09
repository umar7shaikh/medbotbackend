import requests
import logging
from PIL import Image
from io import BytesIO
from django.conf import settings

class MedicalImageAnalyzer:
    def __init__(self):
        """
        Initialize medical image analysis using Hugging Face API (BLIP Image Captioning).
        """
        self.logger = logging.getLogger(__name__)
        self.api_url = "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-base"
        self.api_key = settings.HUGGINGFACE_API_KEY  # Ensure this is correctly set in Django settings

    def analyze_medical_image(self, image):
        """
        Analyze an image using BLIP image captioning model.

        Args:
            image (PIL.Image or file-like object): The uploaded medical image

        Returns:
            dict: Caption (text-based description) of the image
        """
        try:
            # Handle both PIL Image and file-like objects
            if not isinstance(image, Image.Image):
                try:
                    # Make sure to reset file pointer to start if it's a file
                    if hasattr(image, 'seek'):
                        image.seek(0)
                    image = Image.open(image)
                except Exception as e:
                    self.logger.error(f"Failed to open image: {e}")
                    return {"error": f"Failed to process image: {str(e)}"}

            # Convert image to binary format
            buffered = BytesIO()
            image.save(buffered, format="JPEG")
            image_bytes = buffered.getvalue()

            # Debug info
            self.logger.info(f"Sending image to Hugging Face API: {len(image_bytes)} bytes")

            # Prepare API request
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/octet-stream"  # Important for binary data
            }
            
            # Send raw image bytes in request body
            response = requests.post(
                self.api_url,
                headers=headers,
                data=image_bytes  # Send the raw bytes directly
            )

            # Log response details
            self.logger.info(f"API response status: {response.status_code}")
            self.logger.info(f"API response text: {response.text}")

            # Handle API errors
            if response.status_code != 200:
                return {"error": f"Hugging Face API Error: {response.text}"}

            # Extract caption from API response
            results = response.json()
            if isinstance(results, list) and len(results) > 0 and "generated_text" in results[0]:
                return {"caption": results[0]["generated_text"]}

            return {"error": "Unexpected response format from Hugging Face API"}

        except Exception as e:
            self.logger.error(f"Image analysis error: {e}")
            return {"error": str(e)}