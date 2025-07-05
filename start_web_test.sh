#!/bin/bash

# Start Friday AI Web Test Interface
# This script starts both the web server and WebSocket server for browser testing

echo "🚀 Starting Friday AI Web Test Interface..."

# Check if required packages are installed
echo "📦 Checking dependencies..."

# Install requirements if not present
if ! python3 -c "import websockets" 2>/dev/null; then
    echo "Installing web test requirements..."
    pip3 install websockets
fi

# Check if OpenAI API key is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  Warning: OPENAI_API_KEY not set in environment"
    echo "   Please set it in your .env file or export it"
    echo "   STT and TTS features will not work without it"
fi

# Check for port conflicts
echo "🔍 Checking for port conflicts..."
if netstat -tlnp | grep -E ':8090|:8091' > /dev/null; then
    echo "⚠️  Warning: Ports 8090 or 8091 might be in use"
    echo "   If you encounter issues, check for conflicting services"
fi

# Create temp directories
mkdir -p web_temp_audio
chmod 755 web_temp_audio

# Set permissions for the web test server
chmod +x web_test_server.py

# Display access information
echo ""
echo "🌐 Friday AI Web Test Interface"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📱 Web Interface:    http://38.244.6.42:8090"
echo "🔌 WebSocket Server: ws://38.244.6.42:8091" 
echo "📁 Local Access:     http://localhost:8090"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✨ Features:"
echo "   🎤 Audio recording and playback"
echo "   💬 Text input and output"
echo "   🔊 Real-time speech-to-text"
echo "   🗣️  Text-to-speech responses"
echo "   📊 Live connection status"
echo "   🎚️  Audio level visualization"
echo ""
echo "🔧 Usage:"
echo "   1. Open the web interface in your browser"
echo "   2. Allow microphone access when prompted"
echo "   3. Use text input or click the microphone button"
echo "   4. Talk to Friday and get audio/text responses"
echo ""
echo "Press Ctrl+C to stop both servers"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Start the web test server
python3 web_test_server.py