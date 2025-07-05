# Friday AI Web Test Interface

## Overview

A comprehensive web-based testing interface for the Friday AI audio system. This allows you to test all audio and text communication protocols before implementing them on ESP32S3 hardware.

## 🌐 Access Information

- **Web Interface**: `http://38.244.6.42:8090`
- **WebSocket Server**: `ws://38.244.6.42:8091`
- **Local Access**: `http://localhost:8090`

## 🚀 Quick Start

### Start the Web Test Interface
```bash
./start_web_test.sh
```

### Access the Interface
1. Open your browser
2. Navigate to `http://38.244.6.42:8090`
3. Allow microphone access when prompted
4. Start testing!

## ✨ Features

### 🎤 Audio Interface
- **Real-time Recording**: Click microphone button to record voice
- **Audio Level Visualization**: See live audio input levels
- **Playback Controls**: Listen to Friday's audio responses
- **STT Integration**: Automatic speech-to-text conversion
- **TTS Integration**: Text-to-speech responses from Friday

### 💬 Text Interface
- **Direct Text Input**: Type messages directly to Friday
- **Audio Response Option**: Toggle audio generation for text responses
- **Real-time Communication**: Instant WebSocket-based messaging
- **Message History**: Track conversation flow

### 📊 Status & Monitoring
- **Connection Status**: Live connection indicator
- **Server Status**: Real-time server health monitoring
- **Error Handling**: Clear error messages and recovery
- **Performance Metrics**: Response time tracking

## 🎯 Testing Capabilities

### Protocol Testing
- **WebSocket Communication**: Test all message types
- **Audio Streaming**: Verify audio upload/download
- **Error Scenarios**: Test connection drops and recovery
- **Concurrent Sessions**: Multiple browser sessions

### Audio Quality Testing
- **Recording Quality**: Test microphone input
- **Playback Quality**: Verify speaker output
- **Latency Testing**: Measure end-to-end response time
- **Format Compatibility**: Test audio format handling

### Friday AI Integration
- **Memory System**: Test conversation context
- **MCP Integration**: Email and calendar functionality
- **Error Handling**: Graceful failure scenarios
- **Response Quality**: Verify AI response accuracy

## 🔧 Technical Details

### Port Configuration
- **Web Server**: Port 8090 (HTTP)
- **WebSocket Server**: Port 8091 (WS)
- **No Conflicts**: Carefully selected to avoid existing services

### Audio Specifications
- **Sample Rate**: 16,000 Hz
- **Channels**: 1 (Mono)
- **Format**: WAV/WebM
- **Encoding**: Base64 for WebSocket transmission

### Browser Compatibility
- **Chrome/Chromium**: Full support
- **Firefox**: Full support
- **Safari**: Partial support (audio limitations)
- **Edge**: Full support

## 🎮 Usage Guide

### Recording Audio
1. Click the red microphone button
2. Speak clearly (3-5 seconds recommended)
3. Click again to stop recording
4. Wait for processing and response

### Text Input
1. Type your message in the text input field
2. Optionally check "Generate audio response"
3. Click "Send Message" or press Enter
4. View response in the chat area

### Status Monitoring
- **Green Dot**: Connected and ready
- **Red Dot**: Disconnected
- **Orange Dot**: Processing request

## 🧪 Test Scenarios

### Basic Functionality
```
Text: "Hello Friday, how are you?"
Expected: Polite greeting response with Friday's characteristic tone
```

### MCP Integration
```
Text: "What's on my calendar today?"
Expected: Friday accesses Day Management MCP and reports calendar events
```

### Audio Quality
```
Voice: "Friday, send an email to John about the meeting"
Expected: STT correctly transcripts, Friday responds with email confirmation
```

### Error Handling
```
Disconnect internet → Reconnect
Expected: Status shows offline, then automatically reconnects
```

## 🐛 Troubleshooting

### Connection Issues
- **Can't connect**: Check if server is running (`./start_web_test.sh`)
- **Port conflicts**: Verify ports 8090/8091 are free
- **Firewall**: Ensure ports are open for external access

### Audio Issues
- **No recording**: Check microphone permissions in browser
- **No playback**: Verify browser audio settings
- **Poor quality**: Test with different browsers

### Performance Issues
- **High latency**: Check network connection and server load
- **Memory usage**: Restart server if responses slow down
- **Browser crashes**: Use Chrome/Firefox for best performance

## 📱 Mobile Testing

### Mobile Browser Support
- **iOS Safari**: Limited audio support
- **Android Chrome**: Full functionality
- **Mobile Firefox**: Good compatibility

### Touch Interface
- **Large buttons**: Optimized for touch screens
- **Responsive design**: Adapts to screen size
- **Gesture support**: Tap to record/stop

## 🔒 Security Considerations

### Network Security
- **Local Network**: Safe for testing on local network
- **Public Access**: Consider firewall rules for public servers
- **API Keys**: Never expose OpenAI keys in browser

### Audio Privacy
- **Local Processing**: Audio processed on server, not stored
- **Temporary Files**: Automatically cleaned up
- **User Control**: Clear audio controls and permissions

## 🔄 Development & Debugging

### Server Logs
```bash
# View real-time logs
tail -f friday_web_test.log

# Check WebSocket connections
netstat -an | grep 8091
```

### Browser Developer Tools
- **Console**: Check JavaScript errors
- **Network**: Monitor WebSocket traffic
- **Application**: Check local storage usage

### Testing Commands
```bash
# Test WebSocket directly
wscat -c ws://38.244.6.42:8091

# Check server health
curl http://38.244.6.42:8090

# Monitor port usage
netstat -tlnp | grep -E '8090|8091'
```

## 🌟 Advanced Features

### Multi-User Testing
- **Concurrent Sessions**: Multiple browsers can connect
- **Session Isolation**: Each browser has independent conversation
- **Resource Sharing**: Shared Friday AI instance

### Protocol Simulation
- **ESP32S3 Simulation**: Mimics ESP32S3 communication patterns
- **Message Validation**: Ensures protocol compatibility
- **Performance Benchmarking**: Measures response times

### Custom Testing
- **Message Injection**: Send custom WebSocket messages
- **Audio File Upload**: Test with pre-recorded audio
- **Batch Testing**: Automated test sequences

## 📊 Performance Metrics

### Typical Response Times
- **Text Processing**: 1-3 seconds
- **Audio STT**: 2-4 seconds
- **Audio TTS**: 3-5 seconds
- **Total Round Trip**: 5-12 seconds

### Resource Usage
- **CPU**: Moderate during audio processing
- **Memory**: ~50-100MB per session
- **Network**: ~10KB per text message, ~100KB per audio

## 🚀 Future Enhancements

### Planned Features
- **Audio Recording History**: Save and replay recordings
- **Performance Analytics**: Detailed timing metrics
- **Custom Voice Selection**: Choose different TTS voices
- **Batch Testing**: Automated test suites

### ESP32S3 Preparation
- **Protocol Validation**: Ensure ESP32S3 compatibility
- **Performance Optimization**: Optimize for embedded systems
- **Error Recovery**: Robust reconnection logic

## 📚 Files Structure

```
Friday/
├── web_test_server.py          # Main web test server
├── friday_web_test.html        # Web interface HTML
├── start_web_test.sh          # Startup script
├── WEB_TEST_INTERFACE_README.md # This documentation
└── web_temp_audio/            # Temporary audio files
```

## 📝 API Reference

### WebSocket Messages

#### Client → Server
```json
{
  "type": "text_input",
  "text": "Hello Friday",
  "want_audio": true
}
```

#### Server → Client
```json
{
  "type": "friday_response",
  "text": "Hello sir, how may I assist you?",
  "input_text": "Hello Friday"
}
```

### Audio Messages
```json
{
  "type": "audio_data",
  "audio": "base64-encoded-audio-data"
}
```

## 🎉 Success Indicators

### Working Correctly
- ✅ Green connection status
- ✅ Audio level visualization responds to sound
- ✅ Text messages get Friday responses
- ✅ Audio recording produces STT results
- ✅ TTS audio plays clearly

### Common Issues
- ❌ Red connection status → Check server
- ❌ No audio level → Check microphone permissions
- ❌ No STT results → Check OpenAI API key
- ❌ No audio playback → Check browser audio settings

---

**🌐 This web interface provides complete testing of the Friday AI audio system without requiring ESP32S3 hardware, enabling full protocol development and validation through a modern browser interface!**