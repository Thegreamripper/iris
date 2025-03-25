import torch
import numpy as np
import sounddevice as sd
from transformers import pipeline
import json
import os
from typing import Dict, List, Optional
import openai
from pydantic import BaseModel

class AIService:
    def __init__(self):
        # Initialize ASR
        self.transcription_pipeline = pipeline("automatic-speech-recognition", "openai/whisper-base")
        
        # Initialize TTS
        self.tts_pipeline = pipeline("text-to-speech", "facebook/fastspeech2-en-ljspeech")
        
        # Initialize Emotion Recognition
        self.emotion_classifier = pipeline(
            "text-classification",
            model="j-hartmann/emotion-english-distilroberta-base"
        )
        
        # OpenAI Configuration
        self.openai_client = openai.OpenAI()

    def process_audio(self, audio_data: np.ndarray, sample_rate: int) -> Dict:
        try:
            # Convert audio to format expected by Whisper
            if len(audio_data.shape) > 1:
                audio_data = audio_data.mean(axis=1)
            
            results = {
                "transcription": None,
                "emotion": None
            }
            
            # ASR using Whisper
            transcription = self.transcription_pipeline({"raw": audio_data, "sampling_rate": sample_rate})
            results["transcription"] = transcription["text"]
            
            # Emotion Recognition
            if results["transcription"]:
                emotion = self.emotion_classifier(results["transcription"])[0]
                results["emotion"] = emotion["label"]
            
            return results
        except Exception as e:
            print(f"Error processing audio: {str(e)}")
            return {"error": str(e)}

    def generate_response(self, text: str, system_prompt: str = "") -> str:
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",  # or "gpt-3.5-turbo"
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating response: {str(e)}"

    def text_to_speech(self, text: str) -> np.ndarray:
        try:
            audio = self.tts_pipeline(text)[0]["audio"]
            return np.array(audio)
        except Exception as e:
            print(f"TTS Error: {str(e)}")
            return np.array([]) 