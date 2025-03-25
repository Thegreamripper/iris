import threading
import queue
import sounddevice as sd
import numpy as np
from transformers import pipeline
import openai
import pyttsx3
import logging
from datetime import datetime
import os
from dotenv import load_dotenv
import torch
import signal
import sys

# Load environment variables
load_dotenv()

class IrisCLI:
    def __init__(self):
        # Initialize components
        self.setup_logging()
        self.setup_ai()
        self.setup_audio()
        signal.signal(signal.SIGINT, self.handle_exit)
        
    def setup_logging(self):
        """Initialize logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
    def setup_ai(self):
        """Initialize AI components"""
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.logger.info(f"Using device: {self.device}")
        
        # Initialize models
        self.transcription_model = pipeline(
            "automatic-speech-recognition",
            model="openai/whisper-base",
            device=self.device
        )
        
        # Initialize OpenAI
        self.openai_client = openai.OpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Initialize TTS
        self.tts_engine = pyttsx3.init()
        voices = self.tts_engine.getProperty('voices')
        # Set a female voice if available
        for voice in voices:
            if "female" in voice.name.lower():
                self.tts_engine.setProperty('voice', voice.id)
                break
        # Set speech rate
        self.tts_engine.setProperty('rate', 150)
        
    def setup_audio(self):
        """Setup audio components"""
        self.sample_rate = 16000
        self.channels = 1
        self.chunk_duration = 0.5
        self.chunk_samples = int(self.sample_rate * self.chunk_duration)
        self.audio_queue = queue.Queue()
        self.is_listening = False
        self.wake_word = "iris"
        
    def log_message(self, sender, message):
        """Print message to console"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {sender}: {message}")
        
    def audio_callback(self, indata, frames, time, status):
        """Handle incoming audio data"""
        if status:
            self.logger.warning(f"Audio status: {status}")
        if self.is_listening:
            # Ensure single channel by taking the mean if stereo
            if indata.shape[1] > 1:
                audio_data = np.mean(indata, axis=1)
            else:
                audio_data = indata[:, 0]
            self.audio_queue.put(audio_data.copy())
            
    def start(self):
        """Start IRIS"""
        self.is_listening = True
        try:
            self.stream = sd.InputStream(
                channels=self.channels,
                samplerate=self.sample_rate,
                dtype=np.float32,
                blocksize=self.chunk_samples,
                callback=self.audio_callback
            )
            self.stream.start()
            
            # Start processing thread
            self.processing_thread = threading.Thread(target=self.process_audio)
            self.processing_thread.daemon = True
            self.processing_thread.start()
            
            # Welcome message
            welcome_msg = "Hello! I'm IRIS. How can I help you today? (Say 'IRIS' to activate me, or press Ctrl+C to exit)"
            self.log_message("IRIS", welcome_msg)
            self.speak(welcome_msg)
            
            # Keep the main thread running
            while self.is_listening:
                pass
                
        except Exception as e:
            self.logger.error(f"Error starting audio stream: {e}")
            self.is_listening = False
            
    def process_audio(self):
        """Process incoming audio"""
        while self.is_listening:
            try:
                audio_chunk = self.audio_queue.get()
                # Reshape audio for the model
                audio_data = audio_chunk.reshape(-1)
                # Convert audio to text
                result = self.transcription_model({"raw": audio_data, "sampling_rate": self.sample_rate})
                text = result["text"].lower()
                
                # Check for wake word
                if self.wake_word in text:
                    self.log_message("You", text)
                    self.handle_command(text)
                    
            except Exception as e:
                self.logger.error(f"Error processing audio: {e}")
                
    def handle_command(self, text):
        """Handle user commands"""
        try:
            # Generate response
            response = self.generate_response(text)
            
            # Log response
            self.log_message("IRIS", response)
            
            # Speak response
            self.speak(response)
            
        except Exception as e:
            self.logger.error(f"Error handling command: {e}")
            
    def generate_response(self, text):
        """Generate AI response"""
        try:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            system_prompt = f"""You are IRIS, an advanced AI assistant.
Current time: {current_time}

Core traits:
- Intelligent and helpful
- Security conscious
- Natural and friendly

Respond naturally and helpfully to the user."""

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
            self.logger.error(f"Error generating response: {e}")
            return "I apologize, but I'm having trouble generating a response."
            
    def speak(self, text):
        """Convert text to speech"""
        try:
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        except Exception as e:
            self.logger.error(f"Error in text-to-speech: {e}")
            
    def handle_exit(self, signum, frame):
        """Handle exit gracefully"""
        print("\nShutting down IRIS...")
        self.is_listening = False
        if hasattr(self, 'stream'):
            self.stream.stop()
            self.stream.close()
        self.speak("Goodbye!")
        sys.exit(0)

if __name__ == "__main__":
    print("Starting IRIS...")
    print("=" * 50)
    print("IRIS is an AI assistant that can:")
    print("1. Listen for voice commands (say 'IRIS' to activate)")
    print("2. Respond with voice and text")
    print("3. Use GPT-4 for intelligent responses")
    print("=" * 50)
    print("Press Ctrl+C to exit")
    print("=" * 50)
    
    iris = IrisCLI()
    iris.start() 