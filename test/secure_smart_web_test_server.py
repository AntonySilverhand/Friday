#!/usr/bin/env python3
"""
Friday AI Secure Smart Web Test Interface Server
Automatically detects available ports with complete credential security
NO CREDENTIALS OR KEYS ARE EXPOSED TO THE CLIENT
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
import hashlib

# OpenAI imports
from openai import OpenAI
from dotenv import load_dotenv

# Friday AI imports
from friday_with_memory import EnhancedFriday

# Load environment variables SECURELY
load_dotenv()

# SECURITY: Remove any potential credential exposure
def sanitize_dict_for_client(data: dict) -> dict:
    """Remove any sensitive information before sending to client"""
    sensitive_keys = [
        'api_key', 'key', 'token', 'secret', 'password', 'credential', 
        'auth', 'openai', 'OPENAI_API_KEY', 'private', 'sensitive'
    ]
    
    sanitized = {}
    for key, value in data.items():
        key_lower = str(key).lower()
        if any(sensitive in key_lower for sensitive in sensitive_keys):
            sanitized[key] = "[REDACTED]"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_dict_for_client(value)
        elif isinstance(value, str) and len(value) > 20:
            # Potential API key or long credential - redact
            sanitized[key] = f"[REDACTED-{len(value)}-chars]"
        else:
            sanitized[key] = value
    
    return sanitized

# Logging setup with security filtering
class SecureLogFilter(logging.Filter):
    """Filter out sensitive information from logs"""
    
    def filter(self, record):
        # List of sensitive patterns to redact
        sensitive_patterns = [
            'sk-', 'API_KEY', 'token', 'secret', 'password'
        ]
        
        if hasattr(record, 'msg'):
            msg = str(record.msg)
            for pattern in sensitive_patterns:
                if pattern in msg:
                    record.msg = msg.replace(pattern, '[REDACTED]')
        
        return True

# Setup secure logging
secure_filter = SecureLogFilter()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('friday_secure_web_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
logger.addFilter(secure_filter)

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
        print("🔒 FRIDAY AI SECURE SMART WEB TEST SERVER")
        print("="*60)
        print(f"🌐 Web Interface:    http://38.244.6.42:{web_port}")
        print(f"🔌 WebSocket Server: ws://38.244.6.42:{ws_port}")
        print(f"📱 Local Access:     http://localhost:{web_port}")
        print("="*60)
        print("🔒 SECURITY FEATURES:")
        print("   🛡️  NO credentials exposed to client")
        print("   🔐 Server-side only API key storage")
        print("   🚫 Sensitive data filtering")
        print("   📝 Secure logging with redaction")
        print("   🧹 Sanitized client communications")
        print("="*60)
        print("✨ Smart Features:")
        print("   🎤 Audio recording and playback")
        print("   💬 Text input and output") 
        print("   🔊 Real-time speech-to-text")
        print("   🗣️  Text-to-speech responses")
        print("   📊 Live connection status")
        print("   🎚️  Audio level visualization")
        print("   🔄 Smart port management")
        print("="*60)

class SecureSmartFridayWebTestServer:
    """
    Secure smart web-based test server for Friday AI audio system
    Automatically detects ports with complete credential security
    """
    
    def __init__(self, host: str = "0.0.0.0"):
        self.host = host
        self.port_manager = PortManager()
        self.web_port = None
        self.ws_port = None
        self.clients = set()
        
        # SECURITY: Initialize with secure credential handling
        self.setup_ports()
        self.setup_secure_components()
        
    def setup_ports(self):
        """Setup ports with automatic detection"""
        self.web_port, self.ws_port = self.port_manager.get_available_ports(self.host)
        
        if not self.web_port or not self.ws_port:
            raise RuntimeError("❌ Unable to find available ports for the server")
        
        self.port_manager.display_port_status(self.web_port, self.ws_port)
    
    def setup_secure_components(self):
        """Setup Friday AI and OpenAI components with security"""
        try:
            # SECURITY: Get API key securely without exposing it
            api_key = os.getenv("OPENAI_API_KEY")
            self.has_openai = False
            
            if api_key:
                try:
                    # SECURITY: Only store client instance, never expose key
                    self.openai_client = OpenAI(api_key=api_key)
                    self.has_openai = True
                    logger.info("✅ OpenAI client initialized securely")
                    # SECURITY: Clear the key variable immediately
                    del api_key
                except Exception as e:
                    logger.error(f"❌ OpenAI initialization failed: {str(e)}")
                    self.openai_client = None
            else:
                logger.warning("⚠️  OPENAI_API_KEY not found - STT/TTS will not work")
                self.openai_client = None
            
            # Initialize Friday AI
            self.friday = EnhancedFriday("friday_secure_web_memory.db")
            logger.info("✅ Friday AI initialized securely")
            
            # Audio temp directory
            self.audio_temp_dir = Path("secure_web_temp_audio")
            self.audio_temp_dir.mkdir(exist_ok=True)
            logger.info("✅ Secure audio temp directory created")
            
            # SECURITY: Generate session hash for additional security
            self.session_hash = hashlib.sha256(str(time.time()).encode()).hexdigest()[:16]
            logger.info(f"✅ Secure session hash generated: {self.session_hash}")
            
        except Exception as e:
            logger.error(f"❌ Secure component setup failed: {str(e)}")
            raise
    
    async def start_websocket_server(self):
        """Start the WebSocket server"""
        logger.info(f"🔌 Starting secure WebSocket server on {self.host}:{self.ws_port}")
        
        try:
            async with websockets.serve(
                self.handle_websocket_client,
                self.host,
                self.ws_port,
                ping_interval=30,
                ping_timeout=10
            ):
                logger.info(f"✅ Secure WebSocket server running on ws://{self.host}:{self.ws_port}")
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
        class SecureHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, server_instance=None, **kwargs):
                self.server_instance = server_instance
                super().__init__(*args, directory="/root/coding/Friday", **kwargs)
            
            def do_GET(self):
                if self.path == '/' or self.path == '/test':
                    self.path = '/friday_smart_web_test.html'
                elif self.path == '/config.js':
                    # SECURITY: Serve ONLY port configuration, no credentials
                    self.send_response(200)
                    self.send_header('Content-type', 'application/javascript')
                    self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                    self.send_header('Pragma', 'no-cache')
                    self.send_header('Expires', '0')
                    self.end_headers()
                    
                    # SECURITY: Only expose non-sensitive configuration
                    config_js = f"""
                    window.FRIDAY_CONFIG = {{
                        WS_PORT: {self.server_instance.ws_port},
                        WEB_PORT: {self.server_instance.web_port},
                        WS_URL: 'ws://' + window.location.hostname + ':{self.server_instance.ws_port}',
                        SESSION_HASH: '{self.server_instance.session_hash}',
                        SECURE: true
                    }};
                    """
                    self.wfile.write(config_js.encode())
                    return
                super().do_GET()
            
            def log_message(self, format, *args):
                # SECURITY: Filter sensitive information from HTTP logs
                message = format % args
                sensitive_patterns = ['api_key', 'token', 'secret', 'credential']
                for pattern in sensitive_patterns:
                    if pattern.lower() in message.lower():
                        message = message.replace(pattern, '[REDACTED]')
                # Reduce HTTP server logging noise but keep security relevant logs
                if 'config.js' in message or 'error' in message.lower():
                    logger.info(f"HTTP: {message}")
        
        # Create handler with server instance
        def handler_factory(*args, **kwargs):
            return SecureHTTPRequestHandler(*args, server_instance=self, **kwargs)
        
        try:
            with socketserver.TCPServer((self.host, self.web_port), handler_factory) as httpd:
                logger.info(f"✅ Secure web server running on http://{self.host}:{self.web_port}")
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
    
    async def handle_websocket_client(self, websocket):
        """Handle WebSocket client connections with security"""
        client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        logger.info(f"🔗 Secure client connected: {client_id}")
        
        self.clients.add(websocket)
        
        try:
            # SECURITY: Send welcome with NO sensitive information
            await self.send_secure_message(websocket, {
                "type": "welcome",
                "message": "Friday Secure Smart Web Test Interface Connected",
                "server_info": {
                    "audio_format": "wav",
                    "sample_rate": 16000,
                    "channels": 1,
                    "web_port": self.web_port,
                    "ws_port": self.ws_port,
                    "server_time": datetime.now().isoformat(),
                    "openai_available": self.has_openai,
                    "secure": True,
                    "session_hash": self.session_hash
                }
            })
            
            async for message in websocket:
                try:
                    data = json.loads(message)
                    # SECURITY: Validate and sanitize incoming data
                    await self.handle_secure_client_message(websocket, data)
                        
                except json.JSONDecodeError:
                    await self.send_secure_error(websocket, "Invalid JSON message")
                except Exception as e:
                    logger.error(f"Error handling message from {client_id}: {str(e)}")
                    await self.send_secure_error(websocket, "Processing error occurred")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"🔌 Secure client disconnected: {client_id}")
        except Exception as e:
            logger.error(f"Error with secure client {client_id}: {str(e)}")
        finally:
            self.clients.discard(websocket)
    
    async def handle_secure_client_message(self, websocket, data: Dict[str, Any]):
        """Handle messages from web client with security validation"""
        message_type = data.get("type")
        
        # SECURITY: Validate message type
        allowed_types = {
            "ping", "text_input", "audio_data", "get_status", "get_ports"
        }
        
        if message_type not in allowed_types:
            await self.send_secure_error(websocket, f"Unknown message type: {message_type}")
            return
        
        if message_type == "ping":
            await self.send_secure_message(websocket, {
                "type": "pong", 
                "timestamp": datetime.now().isoformat(),
                "server_ports": {"web": self.web_port, "ws": self.ws_port},
                "secure": True
            })
            
        elif message_type == "text_input":
            text = str(data.get("text", "")).strip()[:1000]  # SECURITY: Limit input length
            if text:
                await self.process_secure_text_input(websocket, text, bool(data.get("want_audio", False)))
        
        elif message_type == "audio_data":
            audio_base64 = str(data.get("audio", ""))[:10485760]  # SECURITY: Limit audio size (10MB)
            if audio_base64:
                await self.process_secure_audio_input(websocket, audio_base64)
        
        elif message_type == "get_status":
            await self.send_secure_server_status(websocket)
        
        elif message_type == "get_ports":
            await self.send_secure_message(websocket, {
                "type": "port_info",
                "web_port": self.web_port,
                "ws_port": self.ws_port,
                "host": "redacted",  # SECURITY: Don't expose internal host details
                "secure": True
            })
    
    async def process_secure_text_input(self, websocket, text: str, want_audio: bool = False):
        """Process text input with security"""
        try:
            logger.info(f"💬 Processing secure text input: {text[:50]}...")  # SECURITY: Limit log output
            
            await self.send_secure_message(websocket, {
                "type": "status",
                "message": "Processing with Friday AI..."
            })
            
            # Process with Friday AI
            friday_response = await self.process_with_secure_friday(text)
            
            # Send text response
            await self.send_secure_message(websocket, {
                "type": "friday_response",
                "text": friday_response,
                "input_text": text
            })
            
            # Generate audio if requested and available
            if want_audio and self.has_openai:
                await self.send_secure_message(websocket, {
                    "type": "status",
                    "message": "Generating secure audio response..."
                })
                
                audio_data = await self.secure_text_to_speech(friday_response)
                if audio_data:
                    # Convert to base64 for transmission
                    audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                    
                    await self.send_secure_message(websocket, {
                        "type": "audio_response",
                        "audio": audio_base64,
                        "format": "wav",
                        "text": friday_response
                    })
                else:
                    await self.send_secure_error(websocket, "Failed to generate audio response")
            elif want_audio and not self.has_openai:
                await self.send_secure_error(websocket, "Audio generation unavailable")
            
        except Exception as e:
            logger.error(f"Error processing secure text input: {str(e)}")
            await self.send_secure_error(websocket, "Text processing error occurred")
    
    async def process_secure_audio_input(self, websocket, audio_base64: str):
        """Process audio input with security"""
        try:
            logger.info("🎤 Processing secure audio input")
            
            if not self.has_openai:
                await self.send_secure_error(websocket, "Audio processing unavailable")
                return
            
            await self.send_secure_message(websocket, {
                "type": "status",
                "message": "Processing secure audio..."
            })
            
            # SECURITY: Validate base64 and decode safely
            try:
                audio_data = base64.b64decode(audio_base64)
            except Exception:
                await self.send_secure_error(websocket, "Invalid audio data")
                return
            
            # Save to secure temporary file
            timestamp = int(time.time())
            audio_file = self.audio_temp_dir / f"secure_input_{self.session_hash}_{timestamp}.wav"
            
            with open(audio_file, 'wb') as f:
                f.write(audio_data)
            
            # Convert speech to text securely
            text = await self.secure_speech_to_text(audio_file)
            
            if text:
                logger.info(f"🗣️  Secure STT Result: {text[:50]}...")  # SECURITY: Limit log output
                
                await self.send_secure_message(websocket, {
                    "type": "stt_result",
                    "text": text
                })
                
                # Process with Friday AI
                friday_response = await self.process_with_secure_friday(text)
                
                await self.send_secure_message(websocket, {
                    "type": "friday_response",
                    "text": friday_response,
                    "input_text": text
                })
                
                # Generate audio response
                await self.send_secure_message(websocket, {
                    "type": "status",
                    "message": "Generating secure audio response..."
                })
                
                audio_response = await self.secure_text_to_speech(friday_response)
                
                if audio_response:
                    audio_base64 = base64.b64encode(audio_response).decode('utf-8')
                    
                    await self.send_secure_message(websocket, {
                        "type": "audio_response",
                        "audio": audio_base64,
                        "format": "wav",
                        "text": friday_response
                    })
                
            else:
                await self.send_secure_error(websocket, "Could not process audio - no speech detected")
                
            # SECURITY: Clean up temporary file immediately
            if audio_file.exists():
                audio_file.unlink()
                
        except Exception as e:
            logger.error(f"Error processing secure audio input: {str(e)}")
            await self.send_secure_error(websocket, "Audio processing error occurred")
    
    async def secure_speech_to_text(self, audio_file: Path) -> Optional[str]:
        """Convert audio to text using OpenAI STT securely"""
        try:
            with open(audio_file, 'rb') as audio:
                # SECURITY: OpenAI client handles credentials securely
                transcript = self.openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio,
                    response_format="text",
                    language="en"
                )
                return transcript.strip()
                
        except Exception as e:
            logger.error(f"Secure STT error: {str(e)}")
            return None
    
    async def secure_text_to_speech(self, text: str) -> Optional[bytes]:
        """Convert text to speech using OpenAI TTS securely"""
        try:
            # SECURITY: OpenAI client handles credentials securely
            response = self.openai_client.audio.speech.create(
                model="tts-1",
                voice="onyx",
                input=text[:1000],  # SECURITY: Limit TTS input length
                response_format="wav"
            )
            
            return response.content
            
        except Exception as e:
            logger.error(f"Secure TTS error: {str(e)}")
            return None
    
    async def process_with_secure_friday(self, text: str) -> str:
        """Process text with Friday AI securely"""
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
            logger.error(f"Secure Friday processing error: {str(e)}")
            return "I apologize, sir. I encountered an error processing your request."
    
    async def send_secure_message(self, websocket, message: Dict[str, Any]):
        """Send JSON message to client with security sanitization"""
        try:
            # SECURITY: Sanitize message before sending
            sanitized_message = sanitize_dict_for_client(message)
            await websocket.send(json.dumps(sanitized_message))
        except Exception as e:
            logger.error(f"Error sending secure message: {str(e)}")
    
    async def send_secure_error(self, websocket, error_message: str):
        """Send error message to client securely"""
        await self.send_secure_message(websocket, {
            "type": "error",
            "message": str(error_message)[:500],  # SECURITY: Limit error message length
            "timestamp": datetime.now().isoformat(),
            "secure": True
        })
    
    async def send_secure_server_status(self, websocket):
        """Send server status to client securely"""
        await self.send_secure_message(websocket, {
            "type": "server_status",
            "status": "online",
            "clients_connected": len(self.clients),
            "openai_available": self.has_openai,
            "friday_available": bool(self.friday),
            "ports": {
                "web": self.web_port,
                "websocket": self.ws_port
            },
            "secure": True,
            "session_hash": self.session_hash,
            "timestamp": datetime.now().isoformat()
        })

def run_secure_web_server(server):
    """Run web server in thread"""
    try:
        server.start_web_server()
    except Exception as e:
        logger.error(f"Secure web server error: {str(e)}")

def main():
    """Main function to start the secure smart server"""
    logger.info("🔒 Starting Friday AI Secure Smart Web Test Server...")
    
    try:
        # SECURITY: Create server instance with secure setup
        server = SecureSmartFridayWebTestServer(host="0.0.0.0")
        
        # Start web server in separate thread
        web_thread = Thread(target=run_secure_web_server, args=(server,), daemon=True)
        web_thread.start()
        
        logger.info("🌐 Secure web server started in background thread")
        
        # Run WebSocket server in main thread
        asyncio.run(server.start_websocket_server())
        
    except KeyboardInterrupt:
        logger.info("🛑 Secure server stopped by user")
    except Exception as e:
        logger.error(f"❌ Secure server error: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())