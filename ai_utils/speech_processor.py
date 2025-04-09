import os
import json
import wave
import logging
import base64
import requests
import speech_recognition as sr
from vosk import Model, KaldiRecognizer
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import subprocess
import tempfile
from gtts import gTTS

class SpeechProcessor:
    def __init__(self):
        """
        Initialize STT (Vosk) and TTS (gTTS)
        """
        self.logger = logging.getLogger(__name__)
        self.recognizer = sr.Recognizer()
        self.vosk_model = Model("vosk-model-small-en-us-0.15")  # Ensure Vosk model is downloaded

    def speech_to_text(self, audio_file=None, timeout=5):
        """
        Convert speech to text using Vosk (offline STT)

        Args:
            audio_file (str, optional): Path to audio file

        Returns:
            str: Recognized text or None if speech is unclear
        """
        try:
            if audio_file:
                with sr.AudioFile(audio_file) as source:
                    audio = self.recognizer.record(source)

                # Convert audio to Vosk format
                audio_data = audio.get_wav_data(convert_rate=16000, convert_width=2)
                wf = wave.open("temp_audio.wav", "wb")
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                wf.writeframes(audio_data)
                wf.close()

                # Process with Vosk
                recognizer = KaldiRecognizer(self.vosk_model, 16000)
                with open("temp_audio.wav", "rb") as f:
                    recognizer.AcceptWaveform(f.read())

                text_output = json.loads(recognizer.Result())["text"]
                os.remove("temp_audio.wav")  # Cleanup
                return text_output

            else:
                with sr.Microphone() as source:
                    self.logger.info("Listening...")
                    self.recognizer.adjust_for_ambient_noise(source, duration=1)
                    audio = self.recognizer.listen(source, timeout=timeout)

                return self.recognizer.recognize_google(audio)

        except sr.UnknownValueError:
            self.logger.warning("Could not understand audio")
            return None
        except sr.RequestError as e:
            self.logger.error(f"STT API Error: {e}")
            return None

    def text_to_speech(self, text, lang='en', tld='com'):
        """
        Convert text to speech using Google Text-to-Speech (gTTS)

        Args:
            text (str): Text to convert
            lang (str): Language code (default: 'en')
            tld (str): Top-level domain for the Google TTS service (default: 'com')
                       Options include: 'com', 'co.uk', 'com.au', etc.

        Returns:
            str: Path to generated audio file
        """
        try:
            # Output file path
            output_path = "output.mp3"
            
            # Create gTTS object
            tts = gTTS(text=text, lang=lang, tld=tld, slow=False)
            
            # Save to file
            tts.save(output_path)
            
            return output_path

        except Exception as e:
            self.logger.error(f"TTS Error: {e}")
            return None