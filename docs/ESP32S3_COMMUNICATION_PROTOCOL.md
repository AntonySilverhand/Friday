# ESP32S3 Communication Protocol for Friday AI Audio Server

## Overview

This document describes the WebSocket-based communication protocol between the ESP32S3 chip and the Friday AI Audio Server running on Debian 12 (IP: 38.244.6.42).

## Connection Details

- **Server IP**: `38.244.6.42`
- **Port**: `8080`
- **Protocol**: WebSocket (ws://)
- **Connection URL**: `ws://38.244.6.42:8080`

## Audio Specifications

### Server Audio Settings
- **Format**: WAV
- **Sample Rate**: 16000 Hz
- **Channels**: 1 (Mono)
- **Bit Depth**: 16-bit
- **Encoding**: PCM

### ESP32S3 Audio Settings
- **Input**: I2S microphone
- **Output**: I2S DAC/speaker
- **Buffer Size**: 1024 bytes recommended
- **Streaming**: Real-time audio chunks

## Message Protocol

### Connection Flow
1. ESP32S3 connects to WebSocket server
2. Server sends welcome message with audio configuration
3. ESP32S3 acknowledges and begins audio streaming
4. Bidirectional communication established

### Message Types

#### 1. Welcome Message (Server → ESP32S3)
```json
{
  "type": "welcome",
  "message": "Friday Audio Server connected",
  "server_info": {
    "audio_format": "wav",
    "sample_rate": 16000,
    "channels": 1
  }
}
```

#### 2. Audio Data (ESP32S3 → Server)
- **Format**: Binary data (WAV audio)
- **Size**: Variable (recommend 1-5 second chunks)
- **Processing**: Automatic STT conversion

#### 3. STT Result (Server → ESP32S3)
```json
{
  "type": "stt_result",
  "text": "Hello Friday, how are you today?"
}
```

#### 4. Friday Response (Server → ESP32S3)
```json
{
  "type": "friday_response",
  "text": "Good morning, sir. I am functioning optimally. How may I assist you?"
}
```

#### 5. Audio Response Metadata (Server → ESP32S3)
```json
{
  "type": "audio_response",
  "size": 45678,
  "format": "wav",
  "sample_rate": 16000,
  "channels": 1
}
```

#### 6. Audio Response Data (Server → ESP32S3)
- **Format**: Binary data (WAV audio)
- **Follows metadata message**
- **Ready for playback**

#### 7. Status Messages (Server → ESP32S3)
```json
{
  "type": "status",
  "message": "Processing audio..."
}
```

#### 8. Error Messages (Server → ESP32S3)
```json
{
  "type": "error",
  "message": "Audio processing failed",
  "timestamp": "2024-07-05T10:30:00Z"
}
```

#### 9. Ping/Pong (Bidirectional)
```json
{
  "type": "ping"
}
```
```json
{
  "type": "pong"
}
```

#### 10. Audio Configuration (ESP32S3 → Server)
```json
{
  "type": "audio_config",
  "sample_rate": 16000,
  "channels": 1
}
```

## ESP32S3 Implementation Guidelines

### Required Libraries
- **WebSocketsClient**: For WebSocket communication
- **ArduinoJson**: For JSON message handling
- **I2S**: For audio input/output
- **WiFi**: For network connection

### Basic ESP32S3 Code Structure
```cpp
#include <WiFi.h>
#include <WebSocketsClient.h>
#include <ArduinoJson.h>
#include <driver/i2s.h>

// Audio configuration
#define SAMPLE_RATE 16000
#define CHANNELS 1
#define BITS_PER_SAMPLE 16
#define AUDIO_BUFFER_SIZE 1024

// Server configuration
const char* server_ip = "38.244.6.42";
const int server_port = 8080;

WebSocketsClient webSocket;

void setup() {
    // Initialize WiFi
    WiFi.begin(ssid, password);
    
    // Initialize I2S for audio
    i2s_config_t i2s_config = {
        .mode = I2S_MODE_MASTER | I2S_MODE_RX | I2S_MODE_TX,
        .sample_rate = SAMPLE_RATE,
        .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
        .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
        .communication_format = I2S_COMM_FORMAT_I2S,
        .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
        .dma_buf_count = 8,
        .dma_buf_len = AUDIO_BUFFER_SIZE
    };
    
    i2s_driver_install(I2S_NUM_0, &i2s_config, 0, NULL);
    
    // Initialize WebSocket
    webSocket.begin(server_ip, server_port, "/");
    webSocket.onEvent(webSocketEvent);
}

void loop() {
    webSocket.loop();
    
    // Record and send audio
    if (should_record_audio()) {
        recordAndSendAudio();
    }
}
```

### Audio Recording Flow
1. **Voice Activity Detection**: Detect when user starts speaking
2. **Audio Capture**: Record audio chunks via I2S
3. **Buffer Management**: Accumulate audio data
4. **Transmission**: Send complete audio buffer to server
5. **Response Handling**: Receive and play TTS response

### Audio Playback Flow
1. **Receive Metadata**: Get audio response information
2. **Receive Audio Data**: Download WAV audio data
3. **Buffer Audio**: Store in playback buffer
4. **I2S Playback**: Stream audio to speaker/DAC

## Error Handling

### Connection Errors
- **Network Loss**: Implement reconnection logic
- **Server Unavailable**: Retry with backoff
- **Authentication**: Handle credential issues

### Audio Errors
- **Recording Failure**: Reinitialize I2S if needed
- **Playback Issues**: Check DAC/speaker connections
- **Buffer Overflow**: Implement proper buffer management

### Protocol Errors
- **Invalid JSON**: Log and continue
- **Unknown Message Types**: Ignore gracefully
- **Timeout**: Implement timeout handling

## Performance Optimization

### Audio Quality
- **Noise Reduction**: Implement basic noise filtering
- **Automatic Gain Control**: Adjust input levels
- **Echo Cancellation**: Prevent feedback loops

### Network Optimization
- **Compression**: Optional audio compression
- **Buffering**: Implement jitter buffers
- **Quality Adaptation**: Adjust quality based on connection

### Power Management
- **Sleep Modes**: Use deep sleep when inactive
- **WiFi Management**: Optimize power consumption
- **Audio Processing**: Minimize CPU usage

## Testing Commands

### Server Testing
```bash
# Start the audio server
python3 audio_server.py

# Test with client
python3 audio_client_test.py
```

### ESP32S3 Testing
```cpp
// Test connection
webSocket.sendTXT("{\"type\":\"ping\"}");

// Test audio configuration
webSocket.sendTXT("{\"type\":\"audio_config\",\"sample_rate\":16000,\"channels\":1}");
```

## Security Considerations

### Network Security
- **WiFi Security**: Use WPA2/WPA3 encryption
- **Server Access**: Consider authentication if needed
- **Data Encryption**: Optional TLS/SSL for sensitive data

### Audio Privacy
- **Local Processing**: Minimize cloud dependencies
- **Data Retention**: Implement automatic cleanup
- **User Control**: Provide mute/disable options

## Troubleshooting

### Common Issues
1. **No Audio**: Check I2S connections and configuration
2. **Poor Quality**: Verify sample rate and bit depth
3. **Connection Drops**: Implement robust reconnection
4. **High Latency**: Optimize buffer sizes and network

### Debug Tools
- **Serial Monitor**: For debugging ESP32S3
- **WebSocket Inspector**: For protocol debugging
- **Audio Analysis**: For quality verification

## Future Enhancements

### Advanced Features
- **Voice Commands**: Implement wake word detection
- **Multi-User**: Support multiple ESP32S3 devices
- **Offline Mode**: Cache responses for offline use
- **Custom Voices**: Support different TTS voices

### Integration Options
- **IoT Control**: Integrate with home automation
- **Sensor Data**: Include environmental sensors
- **Display**: Add visual feedback options