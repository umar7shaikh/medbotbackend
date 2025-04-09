import os
import logging
from pathlib import Path
import tempfile
from faster_whisper import WhisperModel
from django.conf import settings
from gtts import gTTS
import re
from pydub import AudioSegment

class SpeechProcessor:
    def __init__(self):
        """
        Initialize STT (faster-whisper) and TTS (gTTS)
        """
        self.logger = logging.getLogger(__name__)
        self.model_size = getattr(settings, 'WHISPER_MODEL_SIZE', 'small')
        self.device = getattr(settings, 'WHISPER_DEVICE', 'cuda')  # <-- use 'cuda'
        self.compute_type = 'float16'  # <-- use 'float16' for GPU

        self.logger.info(f"Loading Whisper {self.model_size} model on {self.device}...")

        self.whisper_model = WhisperModel(
            self.model_size,
            device=self.device,
            compute_type=self.compute_type
        )
        self.logger.info("Whisper model loaded successfully")



    def speech_to_text(self, audio_file=None, language=None):
        """
        Convert speech to text using faster-whisper (multilingual STT)

        Args:
            audio_file (str): Path to audio file
            language (str, optional): Language code to optimize recognition

        Returns:
            str: Recognized text or None if speech is unclear
        """
        try:
            if not audio_file:
                self.logger.error("No audio file provided")
                return None
                
            # Transcribe audio using Whisper
            self.logger.info(f"Transcribing audio file: {audio_file}")
            segments, info = self.whisper_model.transcribe(
                audio_file, 
                beam_size=5,  # Higher beam size for better accuracy
                language=language,  # Will auto-detect if None
                vad_filter=True,  # Voice activity detection to filter non-speech parts
                vad_parameters={"min_silence_duration_ms": 500}  # Adjust silence detection
            )
            
            # Log detected language
            detected_language = info.language
            language_probability = info.language_probability
            self.logger.info(f"Detected language: {detected_language} (confidence: {language_probability:.2f})")
            
            # Extract full text from segments
            text_segments = []
            for segment in segments:
                text_segments.append(segment.text)
            
            text_output = " ".join(text_segments).strip()
            
            if not text_output:
                self.logger.warning("Empty transcription result")
                return None
                
            return text_output

        except Exception as e:
            self.logger.error(f"STT Error: {e}", exc_info=True)
            return None

    def text_to_speech(self, text, lang=None, tld=None):
        """
        Convert (even long) text to speech using Google Text-to-Speech (gTTS).
        Splits long text into sentences if needed.
        """
        try:
            if not text:
                self.logger.error("No text provided for TTS")
                return None

            # Auto-set defaults if not provided
            if lang is None:
                lang = 'en'

            tld_map = {
                'en': 'com',
                'hi': 'co.in',
                'es': 'es',
                'fr': 'fr',
                'de': 'de',
                'ar': 'com.sa',
                'zh-CN': 'com.cn',
                'ta': 'co.in',
                'te': 'co.in',
            }
            if tld is None:
                tld = tld_map.get(lang, 'com')

            # Create output directory
            output_dir = Path(settings.MEDIA_ROOT) / 'tts_output'
            os.makedirs(str(output_dir), exist_ok=True)

            # Generate unique filename
            output_filename = f"tts_{abs(hash(text))}.mp3"
            output_path = output_dir / output_filename

            # --- NEW: Split long text into smaller sentences ---
            sentences = re.split(r'(?<=[।.?!])\s+', text.strip())  # Hindi '।' and normal '.' etc.

            # Temporary list of small audio clips
            audio_clips = []

            for idx, sentence in enumerate(sentences):
                if sentence.strip():
                    tts = gTTS(text=sentence, lang=lang, tld=tld, slow=False)
                    temp_path = output_dir / f"temp_{idx}.mp3"
                    tts.save(str(temp_path))
                    audio_clips.append(AudioSegment.from_file(str(temp_path)))

            # Concatenate all clips
            final_audio = AudioSegment.empty()
            for clip in audio_clips:
                final_audio += clip

            # Export final merged audio
            final_audio.export(str(output_path), format="mp3")

            # Clean up temporary files
            for idx in range(len(audio_clips)):
                temp_file = output_dir / f"temp_{idx}.mp3"
                if temp_file.exists():
                    temp_file.unlink()

            # Return relative path
            relative_path = f'tts_output/{output_filename}'
            return relative_path

        except Exception as e:
            self.logger.error(f"TTS Error: {e}", exc_info=True)
            return None