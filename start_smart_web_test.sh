#!/bin/bash

# Start Friday AI Smart Web Test Interface
# Automatically detects available ports and avoids conflicts

echo "🧠 Starting Friday AI Smart Web Test Interface..."

# Check if required packages are installed
echo "📦 Checking dependencies..."

# Install requirements if not present
if ! python3 -c "import websockets" 2>/dev/null; then
    echo "Installing smart web test requirements..."
    pip3 install websockets
fi

# Check if OpenAI API key is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  Warning: OPENAI_API_KEY not set in environment"
    echo "   Please set it in your .env file or export it"
    echo "   STT and TTS features will not work without it"
fi

# Create temp directories
mkdir -p smart_web_temp_audio
chmod 755 smart_web_temp_audio

# Set permissions for the smart web test server
chmod +x smart_web_test_server.py

# Display startup information
echo ""
echo "🧠 Friday AI Smart Web Test Interface"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 SMART PORT DETECTION: Automatically finds available ports"
echo "🛡️  CONFLICT AVOIDANCE: Avoids all existing services"
echo "🔄 AUTO FALLBACK: Multiple port options with intelligent switching"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✨ Smart Features:"
echo "   🎯 Automatic port detection and assignment"
echo "   🔄 Intelligent fallback if ports become unavailable"
echo "   🛡️  Conflict detection with existing services"
echo "   📊 Real-time port status monitoring"
echo "   🎤 Smart audio recording and playback"
echo "   💬 Intelligent text input and output"
echo "   🔊 Advanced speech-to-text processing"
echo "   🗣️  High-quality text-to-speech responses"
echo "   📈 Live connection and performance status"
echo "   🎚️  Smart audio level visualization"
echo ""
echo "🔧 Usage:"
echo "   1. Server will automatically detect the best available ports"
echo "   2. Web interface will be accessible via the displayed URL"
echo "   3. Allow microphone access when prompted"
echo "   4. Use text input or click the microphone button"
echo "   5. Experience intelligent audio/text conversations with Friday"
echo ""
echo "Press Ctrl+C to stop the smart server"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Start the smart web test server
python3 smart_web_test_server.py