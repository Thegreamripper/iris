import tkinter as tk
from tkinter import ttk, scrolledtext
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

# Load environment variables
load_dotenv()

class IrisApp:
    def __init__(self, root):
        self.root = root
        self.root.title("IRIS - Your Personal AI Assistant")
        self.root.geometry("800x600")
        self.root.configure(bg='#2E2E2E')
        
        # Initialize components
        self.setup_logging()
        self.setup_ai()
        self.setup_audio()
        self.create_gui()
        
    def setup_logging(self):
        """Initialize logging"""
        logging.basicConfig(level=logging.INFO)
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
        
        self.emotion_model = pipeline(
            "text-classification",
            model="j-hartmann/emotion-english-distilroberta-base",
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
        
    def create_gui(self):
        """Create the graphical user interface"""
        # Create main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # Style configuration
        style = ttk.Style()
        style.configure("Custom.TFrame", background='#2E2E2E')
        style.configure("Custom.TButton", 
                       padding=10, 
                       font=('Helvetica', 10))
        
        # Chat display
        self.chat_display = scrolledtext.ScrolledText(
            main_frame,
            wrap=tk.WORD,
            width=70,
            height=20,
            font=("Helvetica", 10),
            bg='#1E1E1E',
            fg='#FFFFFF'
        )
        self.chat_display.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)
        
        # Control buttons frame
        control_frame = ttk.Frame(main_frame, style="Custom.TFrame")
        control_frame.pack(fill=tk.X, pady=5)
        
        # Start button
        self.start_button = ttk.Button(
            control_frame,
            text="Start IRIS",
            command=self.toggle_listening,
            style="Custom.TButton"
        )
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        # Status label
        self.status_label = ttk.Label(
            control_frame,
            text="IRIS is ready",
            font=("Helvetica", 10),
            background='#2E2E2E',
            foreground='#FFFFFF'
        )
        self.status_label.pack(side=tk.LEFT, padx=10)
        
    def toggle_listening(self):
        """Toggle listening state"""
        if not self.is_listening:
            self.start_listening()
            self.start_button.configure(text="Stop IRIS")
            self.status_label.configure(text="IRIS is listening...")
            self.log_message("System", "IRIS activated and listening...")
        else:
            self.stop_listening()
            self.start_button.configure(text="Start IRIS")
            self.status_label.configure(text="IRIS is ready")
            self.log_message("System", "IRIS deactivated")
            
    def log_message(self, sender, message):
        """Add message to chat display"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.chat_display.insert(tk.END, f"[{timestamp}] {sender}: {message}\n")
        self.chat_display.see(tk.END)
        
    def audio_callback(self, indata, frames, time, status):
        """Handle incoming audio data"""
        if status:
            self.logger.warning(f"Audio status: {status}")
        if self.is_listening:
            self.audio_queue.put(indata.copy())
            
    def start_listening(self):
        """Start listening for voice input"""
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
            welcome_msg = "Hello! I'm IRIS. How can I help you today?"
            self.log_message("IRIS", welcome_msg)
            self.speak(welcome_msg)
            
        except Exception as e:
            self.logger.error(f"Error starting audio stream: {e}")
            self.is_listening = False
            
    def process_audio(self):
        """Process incoming audio"""
        while self.is_listening:
            try:
                audio_chunk = self.audio_queue.get()
                # Convert audio to text
                result = self.transcription_model({"raw": audio_chunk, "sampling_rate": self.sample_rate})
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
            # Detect emotion
            emotion = self.emotion_model(text)[0]
            
            # Generate response
            response = self.generate_response(text, emotion["label"])
            
            # Log response
            self.log_message("IRIS", response)
            
            # Speak response
            self.speak(response)
            
        except Exception as e:
            self.logger.error(f"Error handling command: {e}")
            
    def generate_response(self, text, emotion):
        """Generate AI response"""
        try:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            system_prompt = f"""You are IRIS, an advanced AI assistant.
Current time: {current_time}
User's emotion: {emotion}

Core traits:
- Emotionally aware
- Intelligent and helpful
- Security conscious

Respond naturally and appropriately to the user's emotion."""

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
            
    def stop_listening(self):
        """Stop listening for voice input"""
        self.is_listening = False
        if hasattr(self, 'stream'):
            self.stream.stop()
            self.stream.close()
        self.speak("Goodbye!")

if __name__ == "__main__":
    root = tk.Tk()
    app = IrisApp(root)
    root.mainloop() 