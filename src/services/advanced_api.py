from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json
import asyncio
from typing import List, Dict
from .advanced_ai_service import AdvancedAIService
import logging

logger = logging.getLogger(__name__)

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting message: {e}")

manager = ConnectionManager()

# Initialize AI Service
ai_service = AdvancedAIService()

async def on_wake_word():
    await manager.broadcast({
        "type": "wake_word_detected",
        "message": "Wake word detected!"
    })

async def on_transcription(text: str):
    await manager.broadcast({
        "type": "transcription",
        "message": text
    })

async def on_response(response: str):
    await manager.broadcast({
        "type": "response",
        "message": response
    })

# Set callbacks
ai_service.set_callbacks(
    wake_word_callback=lambda: asyncio.create_task(on_wake_word()),
    transcription_callback=lambda x: asyncio.create_task(on_transcription(x)),
    response_callback=lambda x: asyncio.create_task(on_response(x))
)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                command = json.loads(data)
                if command.get("action") == "start_listening":
                    ai_service.start_listening()
                    await websocket.send_json({"status": "listening_started"})
                elif command.get("action") == "stop_listening":
                    ai_service.stop_listening()
                    await websocket.send_json({"status": "listening_stopped"})
            except json.JSONDecodeError:
                await websocket.send_json({"error": "Invalid JSON format"})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        ai_service.stop_listening()

@app.on_event("startup")
async def startup_event():
    logger.info("Starting IRIS AI Service...")
    # Start listening automatically
    ai_service.start_listening()

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down IRIS AI Service...")
    ai_service.stop_listening() 