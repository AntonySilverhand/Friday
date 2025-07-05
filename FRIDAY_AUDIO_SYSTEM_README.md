# Friday AI Audio System for ESP32S3

## Overview

Complete audio integration system for Friday AI Assistant with ESP32S3 hardware support. This system enables voice interaction with Friday through WebSocket-based communication, featuring OpenAI STT/TTS integration.

## System Architecture

```
[ESP32S3 Device] ←→ [WebSocket] ←→ [Friday Audio Server] ←→ [Friday AI + MCPs]
      ↓                              ↓                       ↓
   I2S Audio                    OpenAI STT/TTS           Email/Calendar
   (Mic/Speaker)                Audio Processing         Integration
```

## Server Information

- **IP Address**: `38.244.6.42` (Debian 12 server)
- **Port**: `8080`
- **Protocol**: WebSocket
- **Connection URL**: `ws://38.244.6.42:8080`

## Features

### ✅ Implemented Features

#### Audio Processing
- **Speech-to-Text**: OpenAI Whisper integration
- **Text-to-Speech**: OpenAI TTS with Onyx voice
- **Real-time Streaming**: Low-latency audio processing
- **Format Support**: WAV, 16kHz, mono, 16-bit PCM

#### ESP32S3 Integration
- **WebSocket Client**: Reliable bidirectional communication
- **I2S Audio**: High-quality microphone and speaker support
- **Button Control**: Physical button for recording activation
- **LED Feedback**: Visual status indicators
- **Auto-reconnection**: Robust connection handling

#### Friday AI Integration
- **Memory System**: Conversation context and history
- **MCP Support**: Email and calendar functionality
- **Error Handling**: Graceful degradation
- **Async Processing**: Non-blocking operation

### 🎯 Audio Pipeline

1. **Input**: ESP32S3 records audio via I2S microphone
2. **Transmission**: Audio sent to server via WebSocket
3. **STT**: OpenAI Whisper converts speech to text
4. **Processing**: Friday AI processes the request
5. **TTS**: OpenAI TTS converts response to speech
6. **Output**: Audio streamed back to ESP32S3 speaker

## File Structure

```
Friday/
├── audio_server.py                 # Main WebSocket audio server
├── audio_client_test.py           # Test client for development
├── audio_requirements.txt         # Python dependencies
├── start_audio_server.sh          # Server startup script
├── ESP32S3_ARDUINO_CODE.ino      # Arduino code for ESP32S3
├── ESP32S3_COMMUNICATION_PROTOCOL.md  # Protocol documentation
└── FRIDAY_AUDIO_SYSTEM_README.md  # This file
```

## Quick Start

### 1. Server Setup (Debian 12)

```bash
# Install dependencies
pip3 install -r audio_requirements.txt

# Set OpenAI API key
export OPENAI_API_KEY="your-api-key-here"

# Start server
./start_audio_server.sh
```

### 2. ESP32S3 Setup

#### Hardware Requirements
- ESP32S3 development board
- I2S microphone (e.g., INMP441)
- I2S DAC/amplifier (e.g., MAX98357A)
- Speaker
- Push button
- LED (optional)

#### Arduino Libraries
```cpp
// Install via Arduino Library Manager
#include <WiFi.h>
#include <WebSocketsClient.h>
#include <ArduinoJson.h>
#include <driver/i2s.h>
```

#### Pin Configuration
```cpp
#define I2S_WS 15        // I2S Word Select
#define I2S_SCK 14       // I2S Serial Clock
#define I2S_SD_IN 32     // I2S Serial Data In (Microphone)
#define I2S_SD_OUT 25    // I2S Serial Data Out (Speaker)
#define RECORD_BUTTON_PIN 0  // Recording button
#define STATUS_LED_PIN 2     // Status LED
```

### 3. Usage

#### ESP32S3 Operation
1. **Power on**: ESP32S3 connects to WiFi and server
2. **Status LED**: Solid = connected, blinking = processing
3. **Recording**: Press and hold button to record (3 seconds)
4. **Playback**: Friday's response plays automatically

#### Voice Commands
```
"Hello Friday, how are you?"
"What's on my calendar today?"
"Send an email to John about the meeting"
"What's the weather like?"
"Schedule a meeting for tomorrow at 2 PM"
```

## Technical Specifications

### Audio Settings
- **Sample Rate**: 16,000 Hz
- **Channels**: 1 (Mono)
- **Bit Depth**: 16-bit
- **Format**: PCM WAV
- **Buffer Size**: 1024 bytes
- **Recording Duration**: 3 seconds (configurable)

### Network Protocol
- **Transport**: WebSocket over TCP
- **Message Format**: JSON for control, binary for audio
- **Reconnection**: Automatic with exponential backoff
- **Heartbeat**: Ping/pong every 30 seconds

### Performance
- **Latency**: ~2-3 seconds end-to-end
- **Audio Quality**: CD quality (16kHz)
- **Reliability**: Auto-reconnection and error recovery
- **Power**: Optimized for battery operation

## Testing

### Server Testing
```bash
# Test WebSocket server
python3 audio_client_test.py

# Check server logs
tail -f friday_audio_server.log
```

### ESP32S3 Testing
```cpp
// Serial monitor output shows:
// - WiFi connection status
// - WebSocket connection
// - Audio processing events
// - Error messages
```

### Audio Quality Testing
- Record test phrases and verify STT accuracy
- Check TTS output quality and clarity
- Test in various noise environments
- Validate latency and responsiveness

## Troubleshooting

### Common Issues

#### Connection Problems
- **WiFi Issues**: Check SSID/password, signal strength
- **Server Unreachable**: Verify IP address and port
- **WebSocket Errors**: Check firewall, network connectivity

#### Audio Problems
- **No Recording**: Check I2S microphone connections
- **No Playback**: Verify speaker/DAC connections
- **Poor Quality**: Adjust sample rate, check noise levels
- **High Latency**: Optimize buffer sizes, check network

#### ESP32S3 Issues
- **Boot Loops**: Check power supply, pin conflicts
- **Memory Errors**: Reduce buffer sizes, optimize code
- **I2S Errors**: Verify pin configuration, clock settings

### Debug Commands
```bash
# Check server status
curl http://38.244.6.42:8080

# Monitor network traffic
tcpdump -i any port 8080

# Test audio processing
ffplay response_audio.wav
```

## Configuration Options

### Server Configuration
```python
# In audio_server.py
AUDIO_FORMAT = "wav"
SAMPLE_RATE = 16000
CHANNELS = 1
SERVER_PORT = 8080
TTS_VOICE = "onyx"  # alloy, echo, fable, onyx, nova, shimmer
```

### ESP32S3 Configuration
```cpp
// In ESP32S3_ARDUINO_CODE.ino
#define SAMPLE_RATE 16000
#define RECORDING_DURATION 3000  // milliseconds
#define AUDIO_BUFFER_SIZE 1024
const char* server_ip = "38.244.6.42";
```

## Security Considerations

### Network Security
- **WiFi Encryption**: Use WPA2/WPA3
- **Server Access**: Consider VPN for remote access
- **API Keys**: Secure OpenAI credentials

### Audio Privacy
- **Local Processing**: Minimize cloud dependencies
- **Data Retention**: Automatic cleanup of temp files
- **User Control**: Physical mute options

## Future Enhancements

### Planned Features
- **Wake Word Detection**: "Hey Friday" activation
- **Noise Cancellation**: Advanced audio filtering
- **Multiple Devices**: Support for multiple ESP32S3 units
- **Offline Mode**: Local STT/TTS capabilities
- **Voice Training**: Custom voice models

### Hardware Upgrades
- **Better Microphones**: Far-field microphone arrays
- **Audio Processing**: Dedicated DSP chips
- **Display**: OLED for visual feedback
- **Sensors**: Environmental data integration

## Development

### Adding New Features
1. **Server Side**: Modify `audio_server.py`
2. **ESP32S3 Side**: Update Arduino code
3. **Protocol**: Update communication protocol
4. **Testing**: Add comprehensive tests

### Code Structure
```python
# audio_server.py structure
class AudioServer:
    def __init__()           # Initialize server
    def start_server()       # Start WebSocket server
    def handle_client()      # Handle client connections
    def speech_to_text()     # STT processing
    def text_to_speech()     # TTS processing
    def process_with_friday() # AI processing
```

## Support

### Documentation
- **Protocol Details**: `ESP32S3_COMMUNICATION_PROTOCOL.md`
- **Arduino Code**: `ESP32S3_ARDUINO_CODE.ino`
- **Server Code**: `audio_server.py`

### Resources
- **OpenAI Documentation**: STT/TTS API reference
- **ESP32S3 Documentation**: Hardware and I2S guides
- **WebSocket Protocol**: RFC 6455 specification

## License

This Friday AI Audio System is part of the Friday AI Assistant project and follows the same licensing terms.

---

**🎤 With this audio system, Friday becomes your voice-activated AI assistant, accessible through natural speech interaction on ESP32S3 hardware!**