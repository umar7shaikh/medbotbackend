import logging
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration
import torch

class MedicalImageAnalyzer:
    def __init__(self):
        """
        Initialize medical image analysis using local BLIP model.
        """
        self.logger = logging.getLogger(__name__)
        print("⏳ Loading BLIP processor and model...")

        try:
            self.processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
            self.model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

            # Optional: use GPU if available
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self.model.to(self.device)

            print("✅ BLIP model loaded successfully!")
        except Exception as e:
            print(f"💥 Failed to load BLIP: {e}")
            self.logger.error(f"BLIP load error: {e}")
            raise

    def analyze_medical_image(self, image):
        """
        Analyze an image using locally loaded BLIP image captioning.
        """
        try:
            # Handle both PIL Image and file-like objects
            if not isinstance(image, Image.Image):
                try:
                    if hasattr(image, 'seek'):
                        image.seek(0)
                    image = Image.open(image).convert("RGB")
                except Exception as e:
                    self.logger.error(f"Failed to open image: {e}")
                    return {"error": f"Failed to process image: {str(e)}"}

            print("🖼️  Running BLIP captioning locally...")

            # Preprocess and generate
            inputs = self.processor(images=image, return_tensors="pt").to(self.device)
            output = self.model.generate(**inputs)

            caption = self.processor.decode(output[0], skip_special_tokens=True)
            print(f"📝 Caption: {caption}")

            return {"caption": caption}

        except Exception as e:
            print(f"💥 Exception during image analysis: {str(e)}")
            self.logger.error(f"Image analysis error: {e}")
            return {"error": str(e)}
