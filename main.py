import asyncio
import logging
from src.services.advanced_ai_service import AdvancedAIService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def on_wake_word():
    logger.info("Wake word detected!")

def on_transcription(text):
    logger.info(f"Transcribed: {text}")

def on_response(response):
    logger.info(f"Response: {response}")

async def main():
    try:
        # Initialize the AI service
        ai_service = AdvancedAIService()
        
        # Set up callbacks
        ai_service.set_callbacks(
            wake_word_callback=on_wake_word,
            transcription_callback=on_transcription,
            response_callback=on_response
        )
        
        # Start listening
        ai_service.start_listening()
        
        # Keep the program running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        finally:
            # Cleanup
            await ai_service.cleanup()
            
    except Exception as e:
        logger.error(f"Error in main: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 