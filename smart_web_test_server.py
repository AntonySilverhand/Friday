#!/usr/bin/env python3
"""
Friday AI Smart Web Test Interface Server
Automatically detects available ports and provides web-based testing
"""

import asyncio
import websockets
import json
import logging
import os
import base64
import wave
import io
import socket
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
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
        logging.FileHandler('friday_smart_web_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PortManager:
    """Smart port management with automatic detection and fallback"""
    
    def __init__(self):
        # Default preferred ports
        self.preferred_web_ports = [8090, 8092, 8094, 8096, 8098]
        self.preferred_ws_ports = [8091, 8093, 8095, 8097, 8099]
        
        # Fallback port ranges
        self.web_fallback_range = range(8000, 8200)
        self.ws_fallback_range = range(8001, 8201)
        
        # Ports to avoid (commonly used services)
        self.avoid_ports = {
            80, 443, 22, 21, 23, 25, 53, 110, 143, 993, 995,  # Standard services
            3306, 3307, 5432, 6379, 27017,  # Databases
            8080, 8443, 9000, 9090,  # Common web services
            3000, 4000, 5000, 6000, 7000,  # Development servers
            1433, 1521, 5984, 11211,  # Other databases
            2200, 4403, 5200, 8082, 8085, 8089, 8100, 9050, 9853, 12136, 62789  # Your existing services
        }
    
    def is_port_available(self, port: int, host: str = "0.0.0.0") -> bool:
        """Check if a port is available for binding"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                result = sock.bind((host, port))
                return True
        except (OSError, socket.error) as e:
            return False
    
    def find_available_port(self, preferred_ports: list, fallback_range: range, host: str = "0.0.0.0") -> Optional[int]:
        """Find an available port from preferred list or fallback range"""
        
        # First try preferred ports
        for port in preferred_ports:
            if port not in self.avoid_ports and self.is_port_available(port, host):
                logger.info(f"✅ Found preferred port: {port}")
                return port
        
        # If no preferred ports available, try fallback range
        logger.warning("⚠️  No preferred ports available, searching fallback range...")
        
        for port in fallback_range:
            if port not in self.avoid_ports and self.is_port_available(port, host):
                logger.info(f"✅ Found fallback port: {port}")
                return port
        
        return None
    
    def get_available_ports(self, host: str = "0.0.0.0") -> Tuple[Optional[int], Optional[int]]:
        """Get available web and WebSocket ports"""
        
        logger.info("🔍 Scanning for available ports...")
        
        # Find web server port
        web_port = self.find_available_port(self.preferred_web_ports, self.web_fallback_range, host)
        if not web_port:
            logger.error("❌ No available web server ports found!")
            return None, None
        
        # Find WebSocket port (avoid the web port)
        ws_preferred = [p for p in self.preferred_ws_ports if p != web_port]
        ws_fallback = [p for p in self.ws_fallback_range if p != web_port]
        
        ws_port = self.find_available_port(ws_preferred, ws_fallback, host)
        if not ws_port:
            logger.error("❌ No available WebSocket ports found!")
            return None, None
        
        logger.info(f"🎯 Selected ports - Web: {web_port}, WebSocket: {ws_port}")
        return web_port, ws_port
    
    def display_port_status(self, web_port: int, ws_port: int):
        """Display port allocation status"""
        print("\n" + "="*60)
        print("🚀 FRIDAY AI SMART WEB TEST SERVER")
        print("="*60)
        print(f"🌐 Web Interface:    http://38.244.6.42:{web_port}")
        print(f"🔌 WebSocket Server: ws://38.244.6.42:{ws_port}")
        print(f"📱 Local Access:     http://localhost:{web_port}")
        print("="*60)
        print("✨ Features:")
        print("   🎤 Audio recording and playback")
        print("   💬 Text input and output") 
        print("   🔊 Real-time speech-to-text")
        print("   🗣️  Text-to-speech responses")
        print("   📊 Live connection status")
        print("   🎚️  Audio level visualization")
        print("   🔄 Smart port management")
        print("="*60)

class SmartFridayWebTestServer:
    """
    Smart web-based test server for Friday AI audio system
    Automatically detects ports and provides fallback options
    """
    
    def __init__(self, host: str = "0.0.0.0"):
        self.host = host
        self.port_manager = PortManager()
        self.web_port = None
        self.ws_port = None
        self.clients = set()
        
        # Initialize components
        self.setup_ports()
        self.setup_components()
        
    def setup_ports(self):
        """Setup ports with automatic detection"""
        self.web_port, self.ws_port = self.port_manager.get_available_ports(self.host)
        
        if not self.web_port or not self.ws_port:
            raise RuntimeError("❌ Unable to find available ports for the server")
        
        self.port_manager.display_port_status(self.web_port, self.ws_port)
    
    def setup_components(self):
        """Setup Friday AI and OpenAI components"""
        try:
            # Initialize OpenAI client
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                logger.warning("⚠️  OPENAI_API_KEY not found - STT/TTS will not work")
                self.openai_client = None
            else:
                self.openai_client = OpenAI(api_key=api_key)
                logger.info("✅ OpenAI client initialized")
            
            # Initialize Friday AI
            self.friday = EnhancedFriday("friday_smart_web_memory.db")
            logger.info("✅ Friday AI initialized")
            
            # Audio temp directory
            self.audio_temp_dir = Path("smart_web_temp_audio")
            self.audio_temp_dir.mkdir(exist_ok=True)
            logger.info("✅ Audio temp directory created")
            
        except Exception as e:
            logger.error(f"❌ Component setup failed: {e}")
            raise
    
    async def start_websocket_server(self):
        """Start the WebSocket server"""
        logger.info(f"🔌 Starting WebSocket server on {self.host}:{self.ws_port}")
        
        try:
            async with websockets.serve(
                self.handle_websocket_client,
                self.host,
                self.ws_port,
                ping_interval=30,
                ping_timeout=10
            ):
                logger.info(f"✅ WebSocket server running on ws://{self.host}:{self.ws_port}")
                await asyncio.Future()  # Run forever
        except OSError as e:
            if "Address already in use" in str(e):
                logger.error(f"❌ Port {self.ws_port} became unavailable, attempting to find new port...")
                # Try to find a new port
                _, new_ws_port = self.port_manager.get_available_ports(self.host)
                if new_ws_port:
                    self.ws_port = new_ws_port
                    logger.info(f"🔄 Retrying with new WebSocket port: {self.ws_port}")
                    return await self.start_websocket_server()
            raise
    
    def start_web_server(self):
        """Start the HTTP server"""
        class SmartHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, server_instance=None, **kwargs):
                self.server_instance = server_instance
                super().__init__(*args, directory="/root/coding/Friday", **kwargs)
            
            def do_GET(self):
                if self.path == '/' or self.path == '/test':
                    self.path = '/friday_smart_web_test.html'
                elif self.path == '/config.js':
                    # Serve dynamic configuration
                    self.send_response(200)
                    self.send_header('Content-type', 'application/javascript')
                    self.end_headers()
                    config_js = f"""
                    window.FRIDAY_CONFIG = {{
                        WS_PORT: {self.server_instance.ws_port},
                        WEB_PORT: {self.server_instance.web_port},
                        WS_URL: 'ws://' + window.location.hostname + ':{self.server_instance.ws_port}'
                    }};
                    """
                    self.wfile.write(config_js.encode())
                    return
                super().do_GET()
            
            def log_message(self, format, *args):
                # Reduce HTTP server logging noise
                pass
        
        # Create handler with server instance
        def handler_factory(*args, **kwargs):
            return SmartHTTPRequestHandler(*args, server_instance=self, **kwargs)
        
        try:
            with socketserver.TCPServer((self.host, self.web_port), handler_factory) as httpd:
                logger.info(f"✅ Web server running on http://{self.host}:{self.web_port}")
                httpd.serve_forever()
        except OSError as e:
            if "Address already in use" in str(e):
                logger.error(f"❌ Port {self.web_port} became unavailable, attempting to find new port...")
                # Try to find a new port
                new_web_port, _ = self.port_manager.get_available_ports(self.host)
                if new_web_port:
                    self.web_port = new_web_port
                    logger.info(f"🔄 Retrying with new web port: {self.web_port}")
                    return self.start_web_server()
            raise
    
    async def handle_websocket_client(self, websocket, path):
        """Handle WebSocket client connections"""
        client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        logger.info(f"🔗 Web client connected: {client_id}")
        
        self.clients.add(websocket)
        
        try:
            # Send welcome message with dynamic configuration
            await self.send_message(websocket, {
                "type": "welcome",
                "message": "Friday Smart Web Test Interface Connected",
                "server_info": {
                    "audio_format": "wav",
                    "sample_rate": 16000,
                    "channels": 1,
                    "web_port": self.web_port,
                    "ws_port": self.ws_port,
                    "server_time": datetime.now().isoformat(),
                    "openai_available": bool(self.openai_client)
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
            logger.info(f"🔌 Web client disconnected: {client_id}")
        except Exception as e:
            logger.error(f"Error with web client {client_id}: {e}")
        finally:
            self.clients.discard(websocket)
    
    async def handle_client_message(self, websocket, data: Dict[str, Any]):
        """Handle messages from web client"""
        message_type = data.get("type")
        
        if message_type == "ping":
            await self.send_message(websocket, {
                "type": "pong", 
                "timestamp": datetime.now().isoformat(),
                "server_ports": {"web": self.web_port, "ws": self.ws_port}
            })
            
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
        
        elif message_type == "get_ports":
            await self.send_message(websocket, {
                "type": "port_info",
                "web_port": self.web_port,
                "ws_port": self.ws_port,
                "host": self.host
            })
        
        else:
            await self.send_error(websocket, f"Unknown message type: {message_type}")
    
    async def process_text_input(self, websocket, text: str, want_audio: bool = False):
        """Process text input from web client"""
        try:
            logger.info(f"💬 Processing text input: {text}")
            
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
            
            # Generate audio if requested and OpenAI is available
            if want_audio and self.openai_client:
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
            elif want_audio and not self.openai_client:
                await self.send_error(websocket, "Audio generation unavailable - OpenAI API key not configured")
            
        except Exception as e:
            logger.error(f"Error processing text input: {e}")
            await self.send_error(websocket, f"Text processing error: {str(e)}")
    
    async def process_audio_input(self, websocket, audio_base64: str):
        """Process audio input from web client"""
        try:
            logger.info("🎤 Processing audio input from web client")
            
            if not self.openai_client:
                await self.send_error(websocket, "Audio processing unavailable - OpenAI API key not configured")
                return
            
            # Send processing status
            await self.send_message(websocket, {
                "type": "status",
                "message": "Processing audio..."
            })
            
            # Decode base64 audio
            audio_data = base64.b64decode(audio_base64)
            
            # Save to temporary file
            timestamp = int(time.time())
            audio_file = self.audio_temp_dir / f"smart_web_input_{timestamp}.wav"
            
            with open(audio_file, 'wb') as f:
                f.write(audio_data)
            
            # Convert speech to text
            text = await self.speech_to_text(audio_file)
            
            if text:
                logger.info(f"🗣️  STT Result: {text}")
                
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
            "openai_available": bool(self.openai_client),
            "friday_available": bool(self.friday),
            "ports": {
                "web": self.web_port,
                "websocket": self.ws_port
            },
            "timestamp": datetime.now().isoformat()
        })

def run_web_server(server):
    """Run web server in thread"""
    try:
        server.start_web_server()
    except Exception as e:
        logger.error(f"Web server error: {e}")

def main():
    """Main function to start the smart server"""
    logger.info("🚀 Starting Friday AI Smart Web Test Server...")
    
    try:
        # Create server instance with automatic port detection
        server = SmartFridayWebTestServer(host="0.0.0.0")
        
        # Start web server in separate thread
        web_thread = Thread(target=run_web_server, args=(server,), daemon=True)
        web_thread.start()
        
        logger.info("🌐 Web server started in background thread")
        
        # Run WebSocket server in main thread
        asyncio.run(server.start_websocket_server())
        
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())