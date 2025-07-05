#!/usr/bin/env python3
"""
Friday AI Web Test Interface Server
Provides web-based testing for audio and text communication
"""

import asyncio
import websockets
import json
import logging
import os
import base64
import wave
import io
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import http.server
import socketserver
from threading import Thread
import time

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
        logging.FileHandler('friday_web_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FridayWebTestServer:
    """
    Web-based test server for Friday AI audio system
    Serves HTML interface and handles WebSocket communication
    """
    
    def __init__(self, web_port: int = 8090, ws_port: int = 8091):
        self.web_port = web_port
        self.ws_port = ws_port
        self.clients = set()
        
        # Initialize OpenAI client
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Initialize Friday AI
        self.friday = EnhancedFriday("friday_web_memory.db")
        
        # Audio temp directory
        self.audio_temp_dir = Path("web_temp_audio")
        self.audio_temp_dir.mkdir(exist_ok=True)
        
        logger.info(f"Web test server initialized - Web: {web_port}, WebSocket: {ws_port}")
    
    async def start_websocket_server(self):
        """Start the WebSocket server for client communication"""
        logger.info(f"Starting WebSocket server on port {self.ws_port}")
        
        async with websockets.serve(
            self.handle_websocket_client,
            "0.0.0.0",
            self.ws_port,
            ping_interval=30,
            ping_timeout=10
        ):
            logger.info(f"WebSocket server running on ws://0.0.0.0:{self.ws_port}")
            await asyncio.Future()  # Run forever
    
    def start_web_server(self):
        """Start the HTTP server for serving the web interface"""
        class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory="/root/coding/Friday", **kwargs)
            
            def do_GET(self):
                if self.path == '/' or self.path == '/test':
                    self.path = '/friday_web_test.html'
                super().do_GET()
            
            def log_message(self, format, *args):
                # Reduce HTTP server logging
                pass
        
        with socketserver.TCPServer(("0.0.0.0", self.web_port), CustomHTTPRequestHandler) as httpd:
            logger.info(f"Web server running on http://0.0.0.0:{self.web_port}")
            httpd.serve_forever()
    
    async def handle_websocket_client(self, websocket, path):
        """Handle WebSocket client connections"""
        client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        logger.info(f"Web client connected: {client_id}")
        
        self.clients.add(websocket)
        
        try:
            # Send welcome message
            await self.send_message(websocket, {
                "type": "welcome",
                "message": "Friday Web Test Interface Connected",
                "server_info": {
                    "audio_format": "wav",
                    "sample_rate": 16000,
                    "channels": 1,
                    "server_time": datetime.now().isoformat()
                }
            })
            
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self.handle_client_message(websocket, data)
                        
                except json.JSONDecodeError:
                    await self.send_error(websocket, "Invalid JSON message")
                except Exception as e:
                    logger.error(f"Error handling message from {client_id}: {e}")
                    await self.send_error(websocket, f"Processing error: {str(e)}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Web client disconnected: {client_id}")
        except Exception as e:
            logger.error(f"Error with web client {client_id}: {e}")
        finally:
            self.clients.discard(websocket)
    
    async def handle_client_message(self, websocket, data: Dict[str, Any]):
        """Handle messages from web client"""
        message_type = data.get("type")
        
        if message_type == "ping":
            await self.send_message(websocket, {"type": "pong", "timestamp": datetime.now().isoformat()})
            
        elif message_type == "text_input":
            text = data.get("text", "").strip()
            if text:
                await self.process_text_input(websocket, text, data.get("want_audio", False))
        
        elif message_type == "audio_data":
            audio_base64 = data.get("audio", "")
            if audio_base64:
                await self.process_audio_input(websocket, audio_base64)
        
        elif message_type == "get_status":
            await self.send_server_status(websocket)
        
        else:
            await self.send_error(websocket, f"Unknown message type: {message_type}")
    
    async def process_text_input(self, websocket, text: str, want_audio: bool = False):
        """Process text input from web client"""
        try:
            logger.info(f"Processing text input: {text}")
            
            # Send processing status
            await self.send_message(websocket, {
                "type": "status",
                "message": "Processing with Friday AI..."
            })
            
            # Process with Friday AI
            friday_response = await self.process_with_friday(text)
            
            # Send text response
            await self.send_message(websocket, {
                "type": "friday_response",
                "text": friday_response,
                "input_text": text
            })
            
            # Generate audio if requested
            if want_audio:
                await self.send_message(websocket, {
                    "type": "status",
                    "message": "Generating audio response..."
                })
                
                audio_data = await self.text_to_speech(friday_response)
                if audio_data:
                    # Convert to base64 for web transmission
                    audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                    
                    await self.send_message(websocket, {
                        "type": "audio_response",
                        "audio": audio_base64,
                        "format": "wav",
                        "text": friday_response
                    })
                else:
                    await self.send_error(websocket, "Failed to generate audio response")
            
        except Exception as e:
            logger.error(f"Error processing text input: {e}")
            await self.send_error(websocket, f"Text processing error: {str(e)}")
    
    async def process_audio_input(self, websocket, audio_base64: str):
        """Process audio input from web client"""
        try:
            logger.info("Processing audio input from web client")
            
            # Send processing status
            await self.send_message(websocket, {
                "type": "status",
                "message": "Processing audio..."
            })
            
            # Decode base64 audio
            audio_data = base64.b64decode(audio_base64)
            
            # Save to temporary file
            timestamp = int(time.time())
            audio_file = self.audio_temp_dir / f"web_input_{timestamp}.wav"
            
            with open(audio_file, 'wb') as f:
                f.write(audio_data)
            
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
                    "text": friday_response,
                    "input_text": text
                })
                
                # Generate audio response
                await self.send_message(websocket, {
                    "type": "status",
                    "message": "Generating audio response..."
                })
                
                audio_response = await self.text_to_speech(friday_response)
                
                if audio_response:
                    # Convert to base64 for web transmission
                    audio_base64 = base64.b64encode(audio_response).decode('utf-8')
                    
                    await self.send_message(websocket, {
                        "type": "audio_response",
                        "audio": audio_base64,
                        "format": "wav",
                        "text": friday_response
                    })
                
            else:
                await self.send_error(websocket, "Could not process audio - no speech detected")
                
            # Cleanup temporary file
            if audio_file.exists():
                audio_file.unlink()
                
        except Exception as e:
            logger.error(f"Error processing audio input: {e}")
            await self.send_error(websocket, f"Audio processing error: {str(e)}")
    
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
    
    async def send_server_status(self, websocket):
        """Send server status to client"""
        await self.send_message(websocket, {
            "type": "server_status",
            "status": "online",
            "clients_connected": len(self.clients),
            "openai_available": bool(os.getenv("OPENAI_API_KEY")),
            "friday_available": bool(self.friday),
            "timestamp": datetime.now().isoformat()
        })

def run_web_server(server):
    """Run web server in thread"""
    server.start_web_server()

def main():
    """Main function to start both servers"""
    # Check for required environment variables
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY not found in environment variables")
        return
    
    # Create server instance
    server = FridayWebTestServer(web_port=8090, ws_port=8091)
    
    # Start web server in separate thread
    web_thread = Thread(target=run_web_server, args=(server,), daemon=True)
    web_thread.start()
    
    logger.info("Web server started in background thread")
    
    try:
        # Run WebSocket server in main thread
        asyncio.run(server.start_websocket_server())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")

if __name__ == "__main__":
    main()