#!/usr/bin/env python3
"""
Test client for Friday Audio Server
Simulates ESP32S3 communication
"""

import asyncio
import websockets
import json
import wave
import struct
import random
import time
from pathlib import Path

class AudioClientTest:
    """Test client for Friday Audio Server"""
    
    def __init__(self, server_url: str = "ws://localhost:8080"):
        self.server_url = server_url
        self.websocket = None
        
    async def connect(self):
        """Connect to the audio server"""
        try:
            self.websocket = await websockets.connect(self.server_url)
            print(f"Connected to {self.server_url}")
            
            # Start listening for messages
            await self.listen_for_messages()
            
        except Exception as e:
            print(f"Connection error: {e}")
    
    async def listen_for_messages(self):
        """Listen for messages from server"""
        try:
            async for message in self.websocket:
                if isinstance(message, bytes):
                    # Handle binary audio data
                    await self.handle_audio_response(message)
                else:
                    # Handle text messages
                    data = json.loads(message)
                    await self.handle_server_message(data)
                    
        except websockets.exceptions.ConnectionClosed:
            print("Connection closed")
        except Exception as e:
            print(f"Error listening: {e}")
    
    async def handle_server_message(self, data: dict):
        """Handle text messages from server"""
        message_type = data.get("type")
        
        if message_type == "welcome":
            print(f"Server: {data.get('message')}")
            print(f"Audio config: {data.get('server_info')}")
            
            # Start testing after welcome
            await self.start_testing()
            
        elif message_type == "status":
            print(f"Status: {data.get('message')}")
            
        elif message_type == "stt_result":
            print(f"STT Result: {data.get('text')}")
            
        elif message_type == "friday_response":
            print(f"Friday: {data.get('text')}")
            
        elif message_type == "audio_response":
            print(f"Audio response incoming: {data.get('size')} bytes")
            
        elif message_type == "error":
            print(f"Error: {data.get('message')}")
            
        elif message_type == "pong":
            print("Pong received")
            
        else:
            print(f"Unknown message type: {message_type}")
    
    async def handle_audio_response(self, audio_data: bytes):
        """Handle audio response from server"""
        print(f"Received audio response: {len(audio_data)} bytes")
        
        # Save audio to file for testing
        timestamp = int(time.time())
        audio_file = Path(f"response_{timestamp}.wav")
        
        with open(audio_file, 'wb') as f:
            f.write(audio_data)
        
        print(f"Audio saved to: {audio_file}")
    
    async def start_testing(self):
        """Start the testing sequence"""
        print("Starting tests...")
        
        # Test 1: Send ping
        await self.send_ping()
        await asyncio.sleep(1)
        
        # Test 2: Send text input
        await self.send_text_input("Hello Friday, how are you?")
        await asyncio.sleep(3)
        
        # Test 3: Send simulated audio
        await self.send_test_audio()
        await asyncio.sleep(5)
        
        # Test 4: Send text with audio response request
        await self.send_text_with_audio("What's the weather like?")
        await asyncio.sleep(3)
        
        print("Tests completed!")
    
    async def send_ping(self):
        """Send ping message"""
        await self.websocket.send(json.dumps({"type": "ping"}))
        print("Ping sent")
    
    async def send_text_input(self, text: str):
        """Send text input message"""
        message = {
            "type": "text_input",
            "text": text
        }
        await self.websocket.send(json.dumps(message))
        print(f"Text sent: {text}")
    
    async def send_text_with_audio(self, text: str):
        """Send text input with audio response request"""
        message = {
            "type": "text_input",
            "text": text,
            "want_audio": True
        }
        await self.websocket.send(json.dumps(message))
        print(f"Text with audio request sent: {text}")
    
    async def send_test_audio(self):
        """Send simulated audio data"""
        # Generate test audio (simulated voice)
        sample_rate = 16000
        duration = 3  # 3 seconds
        frequency = 440  # A4 note
        
        # Generate sine wave
        samples = []
        for i in range(sample_rate * duration):
            t = i / sample_rate
            sample = int(32767 * 0.3 * (
                0.5 * (1 + 0.5 * random.random()) *  # Add some randomness
                (1 + 0.3 * (t % 0.5)) *  # Add some modulation
                (1 if (t % 1) < 0.5 else 0.7)  # Add some rhythm
            ))
            samples.append(sample)
        
        # Convert to bytes
        audio_data = b''.join(struct.pack('<h', sample) for sample in samples)
        
        print(f"Sending test audio: {len(audio_data)} bytes")
        await self.websocket.send(audio_data)
    
    async def send_audio_config(self, sample_rate: int = 16000, channels: int = 1):
        """Send audio configuration"""
        message = {
            "type": "audio_config",
            "sample_rate": sample_rate,
            "channels": channels
        }
        await self.websocket.send(json.dumps(message))
        print(f"Audio config sent: {sample_rate}Hz, {channels} channels")

async def main():
    """Main function"""
    client = AudioClientTest()
    await client.connect()

if __name__ == "__main__":
    asyncio.run(main())