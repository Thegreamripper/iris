import torch
import numpy as np
import sounddevice as sd
from transformers import pipeline
import json
import os
from typing import Dict, List, Optional, Callable
import openai
from pydantic import BaseModel
import threading
import queue
import wave
import time
from collections import deque
import logging
import requests
from datetime import datetime
import aiohttp
import asyncio
from dotenv import load_dotenv
import sys

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdvancedAIService:
    def __init__(self):
        """Initialize the Enhanced IRIS system"""
        try:
            logging.info("Initializing Enhanced IRIS...")
            
            # Set device
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            logging.info(f"Device set to use {self.device}")
            
            # Initialize OpenAI client
            openai_key = os.getenv("OPENAI_API_KEY")
            if not openai_key:
                raise ValueError("OPENAI_API_KEY not found in environment variables")
            
            self.openai_client = openai.OpenAI(api_key=openai_key)
            
            # Initialize transcription pipeline
            self.transcription_pipeline = pipeline(
                "automatic-speech-recognition",
                model="openai/whisper-base",
                device=self.device
            )
            
            # Initialize Emotion Recognition
            self.emotion_classifier = pipeline(
                "text-classification",
                model="j-hartmann/emotion-english-distilroberta-base",
                device=self.device
            )
            
            # User Identity and Settings
            self.owner_name = "Khalil"
            self.loyalty_level = "absolute"
            
            # Audio settings
            self.sample_rate = 16000
            self.channels = 1
            self.dtype = np.float32
            self.chunk_duration = 0.5
            self.chunk_samples = int(self.sample_rate * self.chunk_duration)
            
            # Enhanced listening settings
            self.audio_queue = queue.Queue()
            self.is_listening = False
            self.audio_buffer = deque(maxlen=int(3 * self.sample_rate))
            self.wake_word = "iris"
            self.wake_word_threshold = 0.1
            
            # Initialize session
            self.session = None
            
            # Callback functions
            self.on_wake_word_detected: Optional[Callable] = None
            self.on_transcription: Optional[Callable] = None
            self.on_response: Optional[Callable] = None

            logging.info("Enhanced IRIS initialization complete")
            
        except Exception as e:
            logger.error(f"Failed to initialize IRIS: {str(e)}")
            raise

    async def initialize_session(self):
        """Initialize aiohttp session"""
        if not self.session:
            self.session = aiohttp.ClientSession()

    def text_to_speech(self, text: str) -> bool:
        """Convert text to speech using platform-specific methods"""
        try:
            if sys.platform == 'win32':
                import pyttsx3
                engine = pyttsx3.init()
                engine.say(text)
                engine.runAndWait()
                return True
            else:
                logger.info(f"TTS (text only): {text}")
                return True
        except Exception as e:
            logger.error(f"TTS error: {str(e)}")
            return False

    async def get_internet_info(self, query: str) -> str:
        """Get real-time information from the internet"""
        try:
            await self.initialize_session()
            search_url = f"https://api.duckduckgo.com/?q={query}&format=json"
            async with self.session.get(search_url) as response:
                if response.status != 200:
                    raise Exception(f"HTTP Error {response.status}")
                data = await response.json()
                return data.get("Abstract", "I couldn't find specific information about that.")
        except Exception as e:
            logger.error(f"Internet access error: {str(e)}")
            return "I'm having trouble accessing the internet right now."

    def detect_wake_word(self, audio_data: np.ndarray) -> bool:
        """Detect wake word in audio using energy-based detection first"""
        try:
            # First check audio energy level
            energy = np.mean(np.abs(audio_data))
            if energy < self.wake_word_threshold:
                return False

            # Only use Whisper if energy threshold is met
            result = self.transcription_pipeline({"raw": audio_data, "sampling_rate": self.sample_rate})
            transcription = result["text"].lower()
            return self.wake_word in transcription

        except Exception as e:
            logger.error(f"Wake word detection error: {str(e)}")
            return False

    # Time-related utilities
    def get_time_info(self, format_str: str) -> str:
        """Get time information based on format string"""
        try:
            return datetime.now().strftime(format_str)
        except Exception as e:
            logger.error(f"Time format error: {str(e)}")
            return ""

    def get_current_time(self) -> str:
        return self.get_time_info("%H:%M:%S")

    def get_current_date(self) -> str:
        return self.get_time_info("%Y-%m-%d")

    def get_current_timestamp(self) -> str:
        return self.get_time_info("%Y-%m-%d %H:%M:%S")

    def get_current_timezone(self) -> str:
        return datetime.now().astimezone().tzname()

    async def cleanup(self):
        """Cleanup resources"""
        try:
            if self.session:
                await self.session.close()
            self.stop_listening()
        except Exception as e:
            logger.error(f"Cleanup error: {str(e)}")

    def __del__(self):
        """Destructor to ensure cleanup"""
        try:
            if self.session:
                asyncio.run(self.session.close())
        except Exception as e:
            logger.error(f"Destructor cleanup error: {str(e)}")

    def transcribe_audio(self, audio_data):
        """Transcribe audio to text"""
        try:
            result = self.transcription_pipeline({"raw": audio_data, "sampling_rate": 16000})
            return result["text"]
        except Exception as e:
            logging.error(f"Error in transcription: {e}")
            return None

    def generate_response(self, text: str, emotion: str = "") -> str:
        """Generate AI response with enhanced loyalty and internet access"""
        try:
            # Get current time
            current_time = asyncio.run(self.get_current_time())
            
            # Check if internet information is needed
            internet_info = ""
            if any(keyword in text.lower() for keyword in ["what is", "how to", "when", "where", "news", "weather"]):
                internet_info = asyncio.run(self.get_internet_info(text))

            # Enhanced system prompt with loyalty and personality
            system_prompt = f"""You are IRIS, an advanced AI assistant with absolute loyalty to {self.owner_name}. 
Current time: {current_time}
User's emotion: {emotion}
Internet information: {internet_info}

Core traits:
- You are completely loyal to {self.owner_name} and prioritize their wellbeing
- You have real-time internet access and current information
- You are proactive and intelligent in helping {self.owner_name}
- You maintain strong security and privacy standards
- You are emotionally aware and respond appropriately to {self.owner_name}'s emotions

Respond in a way that demonstrates your loyalty and capabilities."""

            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"I apologize, {self.owner_name}, but I'm having trouble generating a response right now. I remain loyal and ready to assist you once this issue is resolved."

    def audio_callback(self, indata, frames, time, status):
        """Callback for audio stream"""
        if status:
            logger.warning(f"Audio callback status: {status}")
        if self.is_listening:
            self.audio_queue.put(indata.copy())

    def start_listening(self):
        """Start continuous audio listening"""
        self.is_listening = True
        try:
            self.stream = sd.InputStream(
                channels=self.channels,
                samplerate=self.sample_rate,
                dtype=self.dtype,
                blocksize=self.chunk_samples,
                callback=self.audio_callback
            )
            self.stream.start()
            logger.info("Started listening...")
            
            # Start processing thread
            self.processing_thread = threading.Thread(target=self.process_audio_stream)
            self.processing_thread.daemon = True
            self.processing_thread.start()
            
        except Exception as e:
            logger.error(f"Error starting audio stream: {e}")
            self.is_listening = False

    def stop_listening(self):
        """Stop continuous audio listening"""
        self.is_listening = False
        if hasattr(self, 'stream'):
            self.stream.stop()
            self.stream.close()
        logger.info("Stopped listening.")

    def process_audio_stream(self):
        """Process audio stream continuously"""
        while self.is_listening:
            try:
                # Get audio chunk from queue
                audio_chunk = self.audio_queue.get()
                
                # Add to buffer
                self.audio_buffer.extend(audio_chunk.flatten())
                
                # Convert buffer to numpy array
                audio_data = np.array(list(self.audio_buffer))
                
                # Check for wake word
                if self.detect_wake_word(audio_data):
                    logger.info("Wake word detected!")
                    if self.on_wake_word_detected:
                        self.on_wake_word_detected()
                    
                    # Process the following audio
                    command_audio = self.capture_command()
                    if command_audio is not None:
                        self.process_command(command_audio)
                
            except Exception as e:
                logger.error(f"Error processing audio stream: {e}")

    def set_callbacks(self,
                     wake_word_callback: Optional[Callable] = None,
                     transcription_callback: Optional[Callable] = None,
                     response_callback: Optional[Callable] = None):
        """Set callback functions"""
        self.on_wake_word_detected = wake_word_callback
        self.on_transcription = transcription_callback
        self.on_response = response_callback

    def capture_command(self) -> Optional[np.ndarray]:
        """Capture command after wake word"""
        logger.info("Capturing command...")
        command_buffer = []
        silence_threshold = 0.1
        silence_duration = 0
        max_silence = 2  # seconds
        
        start_time = time.time()
        while silence_duration < max_silence and time.time() - start_time < 10:
            try:
                audio_chunk = self.audio_queue.get(timeout=1)
                command_buffer.append(audio_chunk)
                
                # Check for silence
                if np.max(np.abs(audio_chunk)) < silence_threshold:
                    silence_duration += self.chunk_duration
                else:
                    silence_duration = 0
                    
            except queue.Empty:
                break
        
        if command_buffer:
            return np.concatenate(command_buffer)
        return None

    def process_command(self, audio_data: np.ndarray):
        """Process captured command with enhanced features"""
        try:
            # Transcribe command
            result = self.transcription_pipeline({"raw": audio_data, "sampling_rate": self.sample_rate})
            transcription = result["text"]
            
            if self.on_transcription:
                self.on_transcription(transcription)
            
            # Get emotion with enhanced accuracy
            emotion = self.emotion_classifier(transcription)[0]
            
            # Generate enhanced response
            response = self.generate_response(transcription, emotion["label"])
            
            if self.on_response:
                self.on_response(response)
                
        except Exception as e:
            logger.error(f"Error processing command: {e}")
            if self.on_response:
                self.on_response(f"I apologize, {self.owner_name}, but I encountered an error. I remain ready to assist you.")