#!/bin/bash

# Start Friday AI Audio Server
# This script starts the audio server for ESP32S3 communication

echo "Starting Friday AI Audio Server..."

# Check if required packages are installed
echo "Checking dependencies..."

# Install audio requirements if not present
if ! python3 -c "import websockets" 2>/dev/null; then
    echo "Installing audio requirements..."
    pip3 install -r audio_requirements.txt
fi

# Check if OpenAI API key is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "Warning: OPENAI_API_KEY not set in environment"
    echo "Please set it in your .env file or export it"
    # Don't exit, let the server handle the error
fi

# Create temp audio directory if it doesn't exist
mkdir -p temp_audio

# Set permissions for audio server
chmod +x audio_server.py

# Start the server
echo "Starting audio server on 0.0.0.0:8080..."
echo "Server will be accessible at: ws://38.244.6.42:8080"
echo "Press Ctrl+C to stop the server"

python3 audio_server.py