#!/usr/bin/env python3
"""
Friday AI Audio Server for ESP32S3 Integration
Handles WebSocket connections, audio streaming, STT, and TTS
"""

import asyncio
import websockets
import json
import logging
import time
import wave
import io
from typing import Optional, Dict, Any, List
from datetime import datetime
import os
from pathlib import Path

# OpenAI imports
from openai import OpenAI
from dotenv import load_dotenv

# Friday AI imports
from friday_with_memory import EnhancedFriday

# Load environment variables
load_dotenv()

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('friday_audio_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AudioServer:
    """
    Audio server for ESP32S3 communication with Friday AI
    Handles WebSocket connections, audio processing, STT, and TTS
    """
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8080):
        self.host = host
        self.port = port
        self.clients = set()
        
        # Initialize OpenAI client
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Initialize Friday AI
        self.friday = EnhancedFriday("friday_audio_memory.db")
        
        # Audio settings
        self.audio_format = "wav"
        self.sample_rate = 16000
        self.channels = 1
        self.chunk_size = 1024
        
        # Audio storage
        self.audio_temp_dir = Path("temp_audio")
        self.audio_temp_dir.mkdir(exist_ok=True)
        
        logger.info(f"Audio server initialized on {host}:{port}")
    
    async def start_server(self):
        """Start the WebSocket server"""
        logger.info(f"Starting Friday Audio Server on {self.host}:{self.port}")
        
        async with websockets.serve(
            self.handle_client,
            self.host,
            self.port,
            ping_interval=30,
            ping_timeout=10
        ):
            logger.info(f"Friday Audio Server running on ws://{self.host}:{self.port}")
            await asyncio.Future()  # Run forever
    
    async def handle_client(self, websocket, path):
        """Handle individual client connections"""
        client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        logger.info(f"Client connected: {client_id}")
        
        self.clients.add(websocket)
        
        try:
            # Send welcome message
            await self.send_message(websocket, {
                "type": "welcome",
                "message": "Friday Audio Server connected",
                "server_info": {
                    "audio_format": self.audio_format,
                    "sample_rate": self.sample_rate,
                    "channels": self.channels
                }
            })
            
            async for message in websocket:
                try:
                    if isinstance(message, bytes):
                        # Handle binary audio data
                        await self.handle_audio_data(websocket, message)
                    else:
                        # Handle text messages
                        data = json.loads(message)
                        await self.handle_text_message(websocket, data)
                        
                except json.JSONDecodeError:
                    await self.send_error(websocket, "Invalid JSON message")
                except Exception as e:
                    logger.error(f"Error handling message from {client_id}: {e}")
                    await self.send_error(websocket, f"Processing error: {str(e)}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client disconnected: {client_id}")
        except Exception as e:
            logger.error(f"Error with client {client_id}: {e}")
        finally:
            self.clients.discard(websocket)
    
    async def handle_audio_data(self, websocket, audio_data: bytes):
        """Handle incoming audio data from ESP32S3"""
        try:
            logger.info(f"Received audio data: {len(audio_data)} bytes")
            
            # Save audio to temporary file
            timestamp = int(time.time())
            audio_file = self.audio_temp_dir / f"input_{timestamp}.wav"
            
            # Create WAV file from raw audio data
            with wave.open(str(audio_file), 'wb') as wav_file:
                wav_file.setnchannels(self.channels)
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(self.sample_rate)
                wav_file.writeframes(audio_data)
            
            # Send processing status
            await self.send_message(websocket, {
                "type": "status",
                "message": "Processing audio..."
            })
            
            # Convert speech to text
            text = await self.speech_to_text(audio_file)
            
            if text:
                logger.info(f"STT Result: {text}")
                
                # Send STT result
                await self.send_message(websocket, {
                    "type": "stt_result",
                    "text": text
                })
                
                # Process with Friday AI
                friday_response = await self.process_with_friday(text)
                
                # Send Friday's response
                await self.send_message(websocket, {
                    "type": "friday_response",
                    "text": friday_response
                })
                
                # Convert response to speech
                audio_response = await self.text_to_speech(friday_response)
                
                if audio_response:
                    # Send audio response
                    await self.send_audio_response(websocket, audio_response)
                
            else:
                await self.send_error(websocket, "Could not process audio")
                
            # Cleanup temporary file
            if audio_file.exists():
                audio_file.unlink()
                
        except Exception as e:
            logger.error(f"Error processing audio data: {e}")
            await self.send_error(websocket, f"Audio processing error: {str(e)}")
    
    async def handle_text_message(self, websocket, data: Dict[str, Any]):
        """Handle text messages from client"""
        message_type = data.get("type")
        
        if message_type == "ping":
            await self.send_message(websocket, {"type": "pong"})
            
        elif message_type == "text_input":
            text = data.get("text", "")
            if text:
                # Process text directly with Friday
                friday_response = await self.process_with_friday(text)
                
                await self.send_message(websocket, {
                    "type": "friday_response",
                    "text": friday_response
                })
                
                # Convert to speech if requested
                if data.get("want_audio", False):
                    audio_response = await self.text_to_speech(friday_response)
                    if audio_response:
                        await self.send_audio_response(websocket, audio_response)
        
        elif message_type == "audio_config":
            # Update audio configuration
            self.sample_rate = data.get("sample_rate", self.sample_rate)
            self.channels = data.get("channels", self.channels)
            
            await self.send_message(websocket, {
                "type": "config_updated",
                "sample_rate": self.sample_rate,
                "channels": self.channels
            })
        
        else:
            await self.send_error(websocket, f"Unknown message type: {message_type}")
    
    async def speech_to_text(self, audio_file: Path) -> Optional[str]:
        """Convert audio to text using OpenAI STT"""
        try:
            with open(audio_file, 'rb') as audio:
                transcript = self.openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio,
                    response_format="text",
                    language="en"
                )
                return transcript.strip()
                
        except Exception as e:
            logger.error(f"STT error: {e}")
            return None
    
    async def text_to_speech(self, text: str) -> Optional[bytes]:
        """Convert text to speech using OpenAI TTS"""
        try:
            response = self.openai_client.audio.speech.create(
                model="tts-1",
                voice="onyx",
                input=text,
                response_format="wav"
            )
            
            # Return audio as bytes
            return response.content
            
        except Exception as e:
            logger.error(f"TTS error: {e}")
            return None
    
    async def process_with_friday(self, text: str) -> str:
        """Process text with Friday AI"""
        try:
            # Run Friday processing in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                self.friday.get_response, 
                text
            )
            return response
            
        except Exception as e:
            logger.error(f"Friday processing error: {e}")
            return "I apologize, sir. I encountered an error processing your request."
    
    async def send_message(self, websocket, message: Dict[str, Any]):
        """Send JSON message to client"""
        try:
            await websocket.send(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending message: {e}")
    
    async def send_error(self, websocket, error_message: str):
        """Send error message to client"""
        await self.send_message(websocket, {
            "type": "error",
            "message": error_message,
            "timestamp": datetime.now().isoformat()
        })
    
    async def send_audio_response(self, websocket, audio_data: bytes):
        """Send audio response to client"""
        try:
            # Send audio metadata first
            await self.send_message(websocket, {
                "type": "audio_response",
                "size": len(audio_data),
                "format": "wav",
                "sample_rate": self.sample_rate,
                "channels": self.channels
            })
            
            # Send audio data
            await websocket.send(audio_data)
            
        except Exception as e:
            logger.error(f"Error sending audio response: {e}")
    
    async def broadcast_message(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients"""
        if self.clients:
            await asyncio.gather(
                *[self.send_message(client, message) for client in self.clients],
                return_exceptions=True
            )

def main():
    """Main function to start the audio server"""
    # Check for required environment variables
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY not found in environment variables")
        return
    
    # Create and start server
    server = AudioServer(host="0.0.0.0", port=8080)
    
    try:
        asyncio.run(server.start_server())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")

if __name__ == "__main__":
    main()