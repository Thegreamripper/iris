from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
from typing import Optional, Dict
import soundfile as sf
import io
from .ai_service import AIService

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize AI Service
ai_service = AIService()

class TextRequest(BaseModel):
    text: str
    system_prompt: Optional[str] = ""

@app.post("/process-audio")
async def process_audio(file: UploadFile = File(...)):
    try:
        # Read audio file
        contents = await file.read()
        audio_data, sample_rate = sf.read(io.BytesIO(contents))
        
        # Process audio
        results = ai_service.process_audio(audio_data, sample_rate)
        return results
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/generate-response")
async def generate_response(request: TextRequest):
    try:
        response = ai_service.generate_response(request.text, request.system_prompt)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/text-to-speech")
async def text_to_speech(request: TextRequest):
    try:
        audio_data = ai_service.text_to_speech(request.text)
        return {"audio": audio_data.tolist()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/detect-wake-word")
async def detect_wake_word(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        audio_data, sample_rate = sf.read(io.BytesIO(contents))
        is_wake_word = ai_service.detect_wake_word(audio_data)
        return {"detected": is_wake_word}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 