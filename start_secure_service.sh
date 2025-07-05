#!/bin/bash

# Start Friday AI Secure Smart Web Test Interface
# Complete credential security with automatic port detection

echo "🔒 Starting Friday AI Secure Smart Web Test Interface..."

# Security check - ensure we're not exposing credentials
echo "🛡️  Running security checks..."

# Check if .env file has proper permissions (should not be world readable)
if [ -f ".env" ]; then
    PERM=$(stat -c "%a" .env)
    if [ "$PERM" != "600" ] && [ "$PERM" != "640" ]; then
        echo "⚠️  Warning: .env file permissions are not secure, fixing..."
        chmod 600 .env
        echo "✅ .env file permissions secured"
    fi
fi

# Ensure no credential files are accidentally exposed
echo "🔍 Checking for exposed credential files..."
find . -name "*.json" -path "*/MCP_Servers/*" -exec chmod 600 {} \; 2>/dev/null
find . -name "*credentials*" -exec chmod 600 {} \; 2>/dev/null
find . -name "*token*" -exec chmod 600 {} \; 2>/dev/null

# Check if required packages are installed
echo "📦 Checking dependencies..."

# Install requirements if not present
if ! python3 -c "import websockets" 2>/dev/null; then
    echo "Installing secure web test requirements..."
    pip3 install websockets
fi

# Security validation - ensure OpenAI API key is set but not logged
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  Warning: OPENAI_API_KEY not set in environment"
    echo "   Please set it in your .env file or export it"
    echo "   STT and TTS features will not work without it"
    echo "   SECURITY: API key will be stored server-side only"
else
    echo "✅ OpenAI API key detected (details redacted for security)"
fi

# Create secure temp directories
mkdir -p secure_web_temp_audio
chmod 700 secure_web_temp_audio  # Only owner can access

# Set permissions for the secure web test server
chmod +x secure_smart_web_test_server.py

# Display security information
echo ""
echo "🔒 Friday AI Secure Smart Web Test Interface"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🛡️  SECURITY FEATURES ENABLED:"
echo "   🔐 NO API keys or credentials exposed to client"
echo "   🚫 Sensitive data filtering in all communications"
echo "   📝 Secure logging with credential redaction"
echo "   🧹 Client message sanitization"
echo "   🔒 Server-side only credential storage"
echo "   🎯 Input validation and length limits"
echo "   📁 Secure temporary file management"
echo "   🔄 Automatic credential cleanup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 SMART PORT DETECTION: Automatically finds available ports"
echo "🛡️  CONFLICT AVOIDANCE: Avoids all existing services"
echo "🔄 AUTO FALLBACK: Multiple port options with intelligent switching"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✨ Features:"
echo "   🎯 Automatic secure port detection and assignment"
echo "   🔄 Intelligent fallback if ports become unavailable"
echo "   🛡️  Conflict detection with existing services"
echo "   📊 Real-time port status monitoring"
echo "   🎤 Secure audio recording and playback"
echo "   💬 Secure text input and output"
echo "   🔊 Secure speech-to-text processing"
echo "   🗣️  Secure text-to-speech responses"
echo "   📈 Live connection and performance status"
echo "   🎚️  Audio level visualization"
echo "   🔒 Complete credential protection"
echo ""
echo "🔧 Security Usage:"
echo "   1. Server automatically detects secure available ports"
echo "   2. All credentials stored server-side only"
echo "   3. Web interface has no access to sensitive data"
echo "   4. Allow microphone access when prompted"
echo "   5. Enjoy secure audio/text conversations with Friday"
echo ""
echo "Press Ctrl+C to stop the secure server"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Start the secure smart web test server
python3 secure_smart_web_test_server.py