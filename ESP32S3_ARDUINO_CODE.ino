/*
 * Friday AI ESP32S3 Audio Client
 * Connects to Friday AI Audio Server via WebSocket
 * Handles audio input/output and communication
 */

#include <WiFi.h>
#include <WebSocketsClient.h>
#include <ArduinoJson.h>
#include <driver/i2s.h>

// WiFi credentials
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// Server configuration
const char* server_ip = "38.244.6.42";
const int server_port = 8080;

// Audio configuration
#define SAMPLE_RATE 16000
#define CHANNELS 1
#define BITS_PER_SAMPLE 16
#define AUDIO_BUFFER_SIZE 1024
#define RECORDING_DURATION 3000  // 3 seconds in milliseconds

// I2S pins - adjust based on your hardware
#define I2S_WS 15
#define I2S_SCK 14
#define I2S_SD_IN 32
#define I2S_SD_OUT 25

// Button pin for recording
#define RECORD_BUTTON_PIN 0

// LED pin for status
#define STATUS_LED_PIN 2

// Global variables
WebSocketsClient webSocket;
bool isRecording = false;
bool isPlaying = false;
bool serverConnected = false;
uint8_t audioBuffer[AUDIO_BUFFER_SIZE];
uint8_t playbackBuffer[8192];
size_t playbackBufferSize = 0;
size_t playbackPosition = 0;

void setup() {
    Serial.begin(115200);
    Serial.println("Friday AI ESP32S3 Audio Client");
    
    // Initialize pins
    pinMode(RECORD_BUTTON_PIN, INPUT_PULLUP);
    pinMode(STATUS_LED_PIN, OUTPUT);
    digitalWrite(STATUS_LED_PIN, LOW);
    
    // Initialize WiFi
    setupWiFi();
    
    // Initialize I2S
    setupI2S();
    
    // Initialize WebSocket
    setupWebSocket();
    
    Serial.println("Setup complete");
}

void loop() {
    webSocket.loop();
    
    // Handle button press for recording
    if (digitalRead(RECORD_BUTTON_PIN) == LOW && !isRecording && serverConnected) {
        startRecording();
    }
    
    // Handle audio playback
    if (isPlaying) {
        playAudio();
    }
    
    delay(10);
}

void setupWiFi() {
    Serial.print("Connecting to WiFi");
    WiFi.begin(ssid, password);
    
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    
    Serial.println();
    Serial.print("WiFi connected. IP address: ");
    Serial.println(WiFi.localIP());
}

void setupI2S() {
    // I2S configuration for recording
    i2s_config_t i2s_config_in = {
        .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
        .sample_rate = SAMPLE_RATE,
        .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
        .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
        .communication_format = I2S_COMM_FORMAT_I2S,
        .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
        .dma_buf_count = 8,
        .dma_buf_len = AUDIO_BUFFER_SIZE,
        .use_apll = false,
        .tx_desc_auto_clear = false,
        .fixed_mclk = 0
    };
    
    // I2S pin configuration for recording
    i2s_pin_config_t pin_config_in = {
        .bck_io_num = I2S_SCK,
        .ws_io_num = I2S_WS,
        .data_out_num = I2S_PIN_NO_CHANGE,
        .data_in_num = I2S_SD_IN
    };
    
    // Install I2S driver for recording
    i2s_driver_install(I2S_NUM_0, &i2s_config_in, 0, NULL);
    i2s_set_pin(I2S_NUM_0, &pin_config_in);
    
    // I2S configuration for playback
    i2s_config_t i2s_config_out = {
        .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_TX),
        .sample_rate = SAMPLE_RATE,
        .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
        .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
        .communication_format = I2S_COMM_FORMAT_I2S,
        .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
        .dma_buf_count = 8,
        .dma_buf_len = AUDIO_BUFFER_SIZE,
        .use_apll = false,
        .tx_desc_auto_clear = true,
        .fixed_mclk = 0
    };
    
    // I2S pin configuration for playback
    i2s_pin_config_t pin_config_out = {
        .bck_io_num = I2S_SCK,
        .ws_io_num = I2S_WS,
        .data_out_num = I2S_SD_OUT,
        .data_in_num = I2S_PIN_NO_CHANGE
    };
    
    // Install I2S driver for playback
    i2s_driver_install(I2S_NUM_1, &i2s_config_out, 0, NULL);
    i2s_set_pin(I2S_NUM_1, &pin_config_out);
    
    Serial.println("I2S initialized");
}

void setupWebSocket() {
    webSocket.begin(server_ip, server_port, "/");
    webSocket.onEvent(webSocketEvent);
    webSocket.setReconnectInterval(5000);
    Serial.println("WebSocket configured");
}

void webSocketEvent(WStype_t type, uint8_t * payload, size_t length) {
    switch(type) {
        case WStype_DISCONNECTED:
            Serial.println("WebSocket Disconnected");
            serverConnected = false;
            digitalWrite(STATUS_LED_PIN, LOW);
            break;
            
        case WStype_CONNECTED:
            Serial.printf("WebSocket Connected to: %s\n", payload);
            serverConnected = true;
            digitalWrite(STATUS_LED_PIN, HIGH);
            
            // Send initial ping
            webSocket.sendTXT("{\"type\":\"ping\"}");
            break;
            
        case WStype_TEXT:
            Serial.printf("Received text: %s\n", payload);
            handleTextMessage((char*)payload);
            break;
            
        case WStype_BIN:
            Serial.printf("Received binary data: %d bytes\n", length);
            handleBinaryMessage(payload, length);
            break;
            
        case WStype_ERROR:
            Serial.printf("WebSocket Error: %s\n", payload);
            break;
            
        default:
            break;
    }
}

void handleTextMessage(const char* message) {
    DynamicJsonDocument doc(1024);
    deserializeJson(doc, message);
    
    const char* type = doc["type"];
    
    if (strcmp(type, "welcome") == 0) {
        Serial.println("Welcome message received");
        const char* msg = doc["message"];
        Serial.println(msg);
        
        // Send audio configuration
        sendAudioConfig();
        
    } else if (strcmp(type, "stt_result") == 0) {
        const char* text = doc["text"];
        Serial.printf("STT Result: %s\n", text);
        
    } else if (strcmp(type, "friday_response") == 0) {
        const char* text = doc["text"];
        Serial.printf("Friday: %s\n", text);
        
    } else if (strcmp(type, "audio_response") == 0) {
        int size = doc["size"];
        Serial.printf("Audio response incoming: %d bytes\n", size);
        
        // Prepare for audio reception
        playbackBufferSize = 0;
        playbackPosition = 0;
        
    } else if (strcmp(type, "status") == 0) {
        const char* msg = doc["message"];
        Serial.printf("Status: %s\n", msg);
        
    } else if (strcmp(type, "error") == 0) {
        const char* msg = doc["message"];
        Serial.printf("Error: %s\n", msg);
        
    } else if (strcmp(type, "pong") == 0) {
        Serial.println("Pong received");
    }
}

void handleBinaryMessage(uint8_t* data, size_t length) {
    // Handle incoming audio data
    if (length > 0 && length <= sizeof(playbackBuffer)) {
        memcpy(playbackBuffer, data, length);
        playbackBufferSize = length;
        playbackPosition = 0;
        
        // Skip WAV header (44 bytes) if present
        if (length > 44 && 
            data[0] == 'R' && data[1] == 'I' && 
            data[2] == 'F' && data[3] == 'F') {
            playbackPosition = 44;
        }
        
        Serial.printf("Audio data received: %d bytes\n", length);
        startPlayback();
    }
}

void startRecording() {
    Serial.println("Starting recording...");
    isRecording = true;
    
    // Blink LED to indicate recording
    for (int i = 0; i < 3; i++) {
        digitalWrite(STATUS_LED_PIN, LOW);
        delay(100);
        digitalWrite(STATUS_LED_PIN, HIGH);
        delay(100);
    }
    
    // Record audio
    recordAudio();
    
    Serial.println("Recording finished");
    isRecording = false;
}

void recordAudio() {
    const int totalSamples = SAMPLE_RATE * RECORDING_DURATION / 1000;
    const int bufferSize = totalSamples * 2; // 16-bit samples
    uint8_t* recordingBuffer = (uint8_t*)malloc(bufferSize);
    
    if (recordingBuffer == NULL) {
        Serial.println("Failed to allocate recording buffer");
        return;
    }
    
    size_t bytesRead = 0;
    size_t totalBytesRead = 0;
    
    // Clear I2S buffer
    i2s_zero_dma_buffer(I2S_NUM_0);
    
    Serial.println("Recording audio...");
    
    while (totalBytesRead < bufferSize) {
        size_t bytesToRead = min(AUDIO_BUFFER_SIZE, bufferSize - totalBytesRead);
        
        i2s_read(I2S_NUM_0, recordingBuffer + totalBytesRead, bytesToRead, &bytesRead, portMAX_DELAY);
        totalBytesRead += bytesRead;
        
        // Visual feedback
        if (totalBytesRead % (bufferSize / 10) == 0) {
            digitalWrite(STATUS_LED_PIN, !digitalRead(STATUS_LED_PIN));
        }
    }
    
    digitalWrite(STATUS_LED_PIN, HIGH);
    
    // Send recorded audio to server
    Serial.printf("Sending %d bytes of audio data\n", totalBytesRead);
    webSocket.sendBIN(recordingBuffer, totalBytesRead);
    
    free(recordingBuffer);
}

void startPlayback() {
    if (playbackBufferSize > 0) {
        Serial.println("Starting audio playback...");
        isPlaying = true;
        
        // Clear I2S buffer
        i2s_zero_dma_buffer(I2S_NUM_1);
    }
}

void playAudio() {
    if (playbackPosition < playbackBufferSize) {
        size_t bytesToWrite = min(AUDIO_BUFFER_SIZE, playbackBufferSize - playbackPosition);
        size_t bytesWritten = 0;
        
        i2s_write(I2S_NUM_1, playbackBuffer + playbackPosition, bytesToWrite, &bytesWritten, 0);
        playbackPosition += bytesWritten;
        
        // Visual feedback
        digitalWrite(STATUS_LED_PIN, !digitalRead(STATUS_LED_PIN));
    } else {
        // Playback finished
        isPlaying = false;
        digitalWrite(STATUS_LED_PIN, HIGH);
        Serial.println("Playback finished");
    }
}

void sendAudioConfig() {
    DynamicJsonDocument doc(256);
    doc["type"] = "audio_config";
    doc["sample_rate"] = SAMPLE_RATE;
    doc["channels"] = CHANNELS;
    
    String message;
    serializeJson(doc, message);
    
    webSocket.sendTXT(message);
    Serial.println("Audio config sent");
}

void sendPing() {
    webSocket.sendTXT("{\"type\":\"ping\"}");
}

// Utility function to check WiFi connection
void checkWiFi() {
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("WiFi connection lost. Reconnecting...");
        WiFi.begin(ssid, password);
        
        while (WiFi.status() != WL_CONNECTED) {
            delay(1000);
            Serial.print(".");
        }
        
        Serial.println("\nWiFi reconnected");
    }
}