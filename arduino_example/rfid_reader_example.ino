/*
 * COMPLETE RFID Reader System for RFID Reception System
 * 
 * This sketch provides full MFRC522 RFID integration with the Python application.
 * 
 * Hardware Required:
 * - Arduino Uno/Nano/Mega
 * - MFRC522 RFID Reader Module
 * - ST7735 TFT Display (optional, for visual feedback)
 * - LED (optional, for status indication)
 * - 220Ω Resistor (for LED)
 * 
 * Wiring for MFRC522 (SPI Interface):
 * - SDA  -> Pin 10
 * - SCK  -> Pin 13
 * - MOSI -> Pin 11
 * - MISO -> Pin 12
 * - IRQ  -> Not connected
 * - GND  -> GND
 * - RST  -> Pin 9
 * - 3.3V -> 3.3V (IMPORTANT: Do not connect to 5V!)
 * 
 * LED Connection (optional):
 * - LED Anode (+) -> Pin 8 -> 220Ω Resistor -> LED Cathode (-) -> GND
 * 
 * TFT Display Connection (optional):
 * - TFT_CS  -> Pin 5
 * - TFT_DC  -> Pin 6
 * - TFT_RST -> Pin 7
 * - VCC -> 5V
 * - GND -> GND
 * 
 * Protocol:
 * - READ\n -> Returns UID:<card_uid>\n or ERROR:<message>\n (card is halted after read)
 * - READ_KEEP\n -> Returns UID:<card_uid>\n or ERROR:<message>\n (card stays active for immediate write)
 * - WRITE:<amount>\n -> Returns OK:WROTE:<uid>:<amount>\n or ERROR:<message>\n
 * - READ_HISTORY\n -> Returns HISTORY_START:<uid>\n, HISTORY_BLOCK:<block>:<data>\n (for blocks 9-15), HISTORY_END\n
 * - CLEAR_HISTORY\n -> Returns OK:HISTORY_CLEARED:<uid>\n or ERROR:<message>\n (clears blocks 9-15)
 * - PING\n -> Returns PONG\n
 * 
 * Installation:
 * 1. Install MFRC522 library: Tools -> Manage Libraries -> Search "MFRC522" -> Install
 * 2. Install Adafruit GFX library: Search "Adafruit GFX" -> Install
 * 3. Install Adafruit ST7735 library: Search "Adafruit ST7735" -> Install
 * 4. Upload this sketch to your Arduino
 * 5. Note the COM port in Tools -> Port
 * 6. Configure this port in your Python application
 */

#include <SPI.h>
#include <MFRC522.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ST7735.h>

// Pin definitions
#define RST_PIN         9    // Reset pin for MFRC522
#define SS_PIN          10   // Slave Select pin for MFRC522
#define LED_PIN         8    // Status LED (optional)

// TFT Display pins (optional - comment out if not using)
#define TFT_CS          5    // TFT Chip Select
#define TFT_DC          6    // TFT Data/Command
#define TFT_RST         7    // TFT Reset
#define USE_TFT         true // Set to false to disable TFT display

// Create MFRC522 instance
MFRC522 mfrc522(SS_PIN, RST_PIN);

// Create TFT instance (optional)
#if USE_TFT
Adafruit_ST7735 tft = Adafruit_ST7735(TFT_CS, TFT_DC, TFT_RST);
#endif

// Communication variables
String inputString = "";
boolean stringComplete = false;

// Card data structure for writing
struct CardData {
  char text[12];        // Text data (up to 11 chars + null terminator)
  uint32_t checksum;    // Checksum for validation
};

// Function prototypes
void processCommand(String command);
void handleRead();
void handleReadKeep();
void handleWrite(String data);
void handleReadHistory();
void handleClearHistory();
String getCardUID();
bool writeCardData(String data);
String readCardData();
String readHistoryBlock(byte blockAddr);
uint32_t calculateChecksum(const char* text);
void blinkLED(int times, int delayMs);
void setLED(bool state);
void displayWrittenData(String value);
void initTFT();

void setup() {
  // Initialize serial communication
  Serial.begin(115200);
  while (!Serial) {
    ; // Wait for serial port to connect (needed for native USB)
  }
  
  // Initialize LED pin (optional)
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
  
  // Initialize SPI bus
  SPI.begin();
  
  // Initialize MFRC522 RFID reader
  mfrc522.PCD_Init();
  delay(100);
  
  // Check MFRC522 version
  byte version = mfrc522.PCD_ReadRegister(mfrc522.VersionReg);
  if (version == 0x00 || version == 0xFF) {
    Serial.println("ERROR:MFRC522 not found! Check wiring.");
    // Blink LED rapidly to indicate error
    while(1) {
      blinkLED(5, 100);
      delay(1000);
    }
  }
  
  // Initialize TFT Display (optional)
  initTFT();
  
  // Reserve memory for input string
  inputString.reserve(200);
  
  // Signal ready
  Serial.println("RFID Reader Ready");
  Serial.print("MFRC522 Version: 0x");
  Serial.println(version, HEX);
  
  // Blink LED to indicate ready
  blinkLED(3, 200);
}

void loop() {
  // Read serial input
  while (Serial.available()) {
    char inChar = (char)Serial.read();
    inputString += inChar;
    
    if (inChar == '\n') {
      stringComplete = true;
    }
  }
  
  // Process complete commands
  if (stringComplete) {
    processCommand(inputString);
    inputString = "";
    stringComplete = false;
  }
}

void processCommand(String command) {
  command.trim();
  
  // Ignore empty commands
  if (command.length() == 0) {
    return;
  }
  
  // Convert to uppercase for case-insensitive matching
  String cmdUpper = command;
  cmdUpper.toUpperCase();
  
  if (cmdUpper.equals("READ")) {
    handleRead();
  }
  else if (cmdUpper.equals("READ_KEEP")) {
    handleReadKeep();
  }
  else if (cmdUpper.startsWith("WRITE:")) {
    // Extract data after "WRITE:"
    String data = command.substring(6);
    data.trim();
    
    if (data.length() == 0) {
      Serial.println("ERROR:Empty data");
    } else if (data.length() > 11) {
      Serial.println("ERROR:Data too long (max 11 chars)");
    } else {
      handleWrite(data);
    }
  }
  else if (cmdUpper.equals("READ_HISTORY")) {
    handleReadHistory();
  }
  else if (cmdUpper.equals("CLEAR_HISTORY")) {
    handleClearHistory();
  }
  else if (cmdUpper.equals("PING")) {
    Serial.println("PONG");
  }
  else if (cmdUpper.equals("RESET")) {
    mfrc522.PCD_Init();
    Serial.println("OK:RESET");
  }
  else {
    // Log unknown command for debugging
    Serial.print("ERROR:Unknown command: ");
    Serial.println(command);
  }
}

void handleRead() {
  setLED(true);
  
  // Soft reset to ensure clean state
  mfrc522.PCD_Init();
  delay(100);
  
  // Wait for card with multiple attempts
  unsigned long startTime = millis();
  const unsigned long timeout = 5000; // 5 second timeout
  int attempts = 0;
  
  while (millis() - startTime < timeout) {
    attempts++;
    
    // Multiple quick checks
    for (int i = 0; i < 3; i++) {
      // Look for new cards
      if (mfrc522.PICC_IsNewCardPresent()) {
        delay(10);
        // Select one of the cards
        if (mfrc522.PICC_ReadCardSerial()) {
          // Card detected successfully
          String uid = getCardUID();
          
          // Try to read card data
          String cardData = readCardData();
          if (cardData != "" && cardData != "ERROR" && cardData != "INVALID") {
            // Display on TFT if available
            displayWrittenData(cardData);
            Serial.println("UID:" + uid + ":" + cardData);
          } else {
            Serial.println("UID:" + uid);
          }
          
          // Halt PICC
          mfrc522.PICC_HaltA();
          mfrc522.PCD_StopCrypto1();
          
          setLED(false);
          blinkLED(2, 100);
          return;
        }
      }
      delay(20);
    }
    delay(50);
  }
  
  // Timeout reached
  setLED(false);
  Serial.println("ERROR:No card detected (timeout)");
}

void handleReadKeep() {
  // Read card but keep it active for subsequent operations (e.g., immediate write)
  setLED(true);
  
  // Soft reset to ensure clean state
  mfrc522.PCD_Init();
  delay(100);
  
  // Wait for card with multiple attempts
  unsigned long startTime = millis();
  const unsigned long timeout = 5000; // 5 second timeout
  int attempts = 0;
  
  while (millis() - startTime < timeout) {
    attempts++;
    
    // Multiple quick checks
    for (int i = 0; i < 3; i++) {
      // Look for new cards
      if (mfrc522.PICC_IsNewCardPresent()) {
        delay(10);
        // Select one of the cards
        if (mfrc522.PICC_ReadCardSerial()) {
          // Card detected successfully
          String uid = getCardUID();
          Serial.println("UID:" + uid);
          
          // DO NOT halt PICC - keep it active for immediate write
          // mfrc522.PICC_HaltA();  // Commented out
          // mfrc522.PCD_StopCrypto1();  // Commented out
          
          setLED(false);
          blinkLED(2, 100);
          return;
        }
      }
      delay(20);
    }
    delay(50);
  }
  
  // Timeout reached
  setLED(false);
  Serial.println("ERROR:No card detected (timeout)");
}

void handleWrite(String data) {
  setLED(true);
  Serial.println("STATUS:Ready to write - place card now...");
  
  // HARD reset to ensure card detection works even after previous halt
  // This is critical when card was previously read and halted
  mfrc522.PCD_Reset();      // Hardware reset
  delay(50);
  mfrc522.PCD_Init();       // Re-initialize
  delay(150);               // Longer delay for full initialization
  mfrc522.PCD_AntennaOn();  // Ensure antenna is on
  delay(50);
  
  // Wait for card with multiple attempts
  unsigned long startTime = millis();
  const unsigned long timeout = 10000; // 10 seconds for writing
  unsigned long lastStatusTime = millis();
  int attempts = 0;
  
  while (millis() - startTime < timeout) {
    attempts++;
    
    // Send status update every 2 seconds
    if (millis() - lastStatusTime > 2000) {
      Serial.println("STATUS:Still waiting for card...");
      lastStatusTime = millis();
      blinkLED(1, 50);
    }
    
    // More aggressive card detection - try multiple times per loop
    for (int i = 0; i < 5; i++) {  // Increased from 3 to 5 attempts
      // Look for new cards (PICC_IsNewCardPresent will wake up halted cards)
      if (mfrc522.PICC_IsNewCardPresent()) {
        delay(10);
        // Select one of the cards
        if (mfrc522.PICC_ReadCardSerial()) {
          // Card detected
          Serial.println("STATUS:Card detected, writing...");
          String uid = getCardUID();
          
          // Attempt to write data
          if (writeCardData(data)) {
            Serial.println("OK:WROTE:" + uid + ":" + data);
            displayWrittenData(data);  // Display on TFT
            blinkLED(3, 150);
          } else {
            Serial.println("ERROR:Write failed - authentication issue");
            blinkLED(5, 100);
          }
          
          // Halt PICC
          mfrc522.PICC_HaltA();
          mfrc522.PCD_StopCrypto1();
          
          setLED(false);
          return;
        }
      }
      delay(15);  // Slightly longer delay between attempts
    }
    delay(30);  // Shorter delay between loop cycles
  }
  
  // Timeout reached
  setLED(false);
  Serial.println("ERROR:No card detected after " + String(attempts) + " attempts");
}

String getCardUID() {
  String uid = "";
  for (byte i = 0; i < mfrc522.uid.size; i++) {
    if (mfrc522.uid.uidByte[i] < 0x10) {
      uid += "0";
    }
    uid += String(mfrc522.uid.uidByte[i], HEX);
  }
  uid.toUpperCase();
  return uid;
}

bool writeCardData(String data) {
  // We'll write to block 4 (sector 1, block 0)
  // Note: Blocks 0-3 are in sector 0, blocks 4-7 in sector 1, etc.
  // Block 0 contains manufacturer data and should not be written
  // We use block 4 which is the first block of sector 1
  
  byte sector = 1;
  byte blockAddr = 4;
  byte trailerBlock = 7;
  
  // Default key for authentication (most cards use this)
  MFRC522::MIFARE_Key key;
  for (byte i = 0; i < 6; i++) {
    key.keyByte[i] = 0xFF; // Default key
  }
  
  // Authenticate using key A
  MFRC522::StatusCode status;
  status = mfrc522.PCD_Authenticate(MFRC522::PICC_CMD_MF_AUTH_KEY_A, trailerBlock, &key, &(mfrc522.uid));
  if (status != MFRC522::STATUS_OK) {
    return false;
  }
  
  // Prepare data to write (16 bytes per block)
  byte dataBlock[16];
  memset(dataBlock, 0, 16); // Clear buffer
  
  // Create card data structure
  CardData cardData;
  memset(cardData.text, 0, sizeof(cardData.text));
  strncpy(cardData.text, data.c_str(), sizeof(cardData.text) - 1);
  cardData.checksum = calculateChecksum(cardData.text);
  
  // Copy data to block
  memcpy(dataBlock, &cardData, sizeof(CardData));
  
  // Write data to block
  status = mfrc522.MIFARE_Write(blockAddr, dataBlock, 16);
  if (status != MFRC522::STATUS_OK) {
    return false;
  }
  
  return true;
}

String readCardData() {
  byte sector = 1;
  byte blockAddr = 4;
  byte trailerBlock = 7;
  
  MFRC522::MIFARE_Key key;
  for (byte i = 0; i < 6; i++) {
    key.keyByte[i] = 0xFF;
  }
  
  // Authenticate
  MFRC522::StatusCode status;
  status = mfrc522.PCD_Authenticate(MFRC522::PICC_CMD_MF_AUTH_KEY_A, trailerBlock, &key, &(mfrc522.uid));
  if (status != MFRC522::STATUS_OK) {
    return "ERROR";
  }
  
  // Read data from block
  byte buffer[18];
  byte size = sizeof(buffer);
  status = mfrc522.MIFARE_Read(blockAddr, buffer, &size);
  if (status != MFRC522::STATUS_OK) {
    return "ERROR";
  }
  
  // Extract card data
  CardData cardData;
  memcpy(&cardData, buffer, sizeof(CardData));
  
  // Verify checksum
  if (cardData.checksum != calculateChecksum(cardData.text)) {
    return "INVALID"; // Invalid data
  }
  
  // Ensure null termination
  cardData.text[sizeof(cardData.text) - 1] = '\0';
  return String(cardData.text);
}

void handleReadHistory() {
  setLED(true);
  
  // Soft reset to ensure clean state
  mfrc522.PCD_Init();
  delay(100);
  
  // Wait for card with multiple attempts
  unsigned long startTime = millis();
  const unsigned long timeout = 5000; // 5 second timeout
  
  while (millis() - startTime < timeout) {
    // Look for new cards
    if (mfrc522.PICC_IsNewCardPresent()) {
      delay(10);
      // Select one of the cards
      if (mfrc522.PICC_ReadCardSerial()) {
        // Card detected successfully
        String uid = getCardUID();
        
        // Send history start marker with UID
        Serial.print("HISTORY_START:");
        Serial.println(uid);
        
        // Read blocks 9 to 15 (history blocks)
        for (byte block = 9; block <= 15; block++) {
          String blockData = readHistoryBlock(block);
          
          // Send block data even if empty (Python will filter)
          Serial.print("HISTORY_BLOCK:");
          Serial.print(block);
          Serial.print(":");
          Serial.println(blockData);
        }
        
        // Send history end marker
        Serial.println("HISTORY_END");
        
        // Halt PICC
        mfrc522.PICC_HaltA();
        mfrc522.PCD_StopCrypto1();
        
        setLED(false);
        blinkLED(2, 100);
        return;
      }
    }
    delay(50);
  }
  
  // Timeout reached
  setLED(false);
  Serial.println("ERROR:No card detected (timeout)");
}

String readHistoryBlock(byte blockAddr) {
  // Determine trailer block for authentication (every 4th block is trailer)
  byte trailerBlock = (blockAddr / 4) * 4 + 3;
  
  // Default key for authentication
  MFRC522::MIFARE_Key key;
  for (byte i = 0; i < 6; i++) {
    key.keyByte[i] = 0xFF;
  }
  
  // Authenticate using key A
  MFRC522::StatusCode status;
  status = mfrc522.PCD_Authenticate(MFRC522::PICC_CMD_MF_AUTH_KEY_A, trailerBlock, &key, &(mfrc522.uid));
  if (status != MFRC522::STATUS_OK) {
    return ""; // Return empty string on auth error
  }
  
  // Read data from block
  byte buffer[18];
  byte size = sizeof(buffer);
  status = mfrc522.MIFARE_Read(blockAddr, buffer, &size);
  if (status != MFRC522::STATUS_OK) {
    return ""; // Return empty string on read error
  }
  
  // Convert buffer to readable string (filter printable characters)
  String result = "";
  for (int i = 0; i < 16; i++) {
    if (buffer[i] >= 32 && buffer[i] <= 126) {
      result += (char)buffer[i];
    } else if (buffer[i] == 0) {
      // Stop at null terminator
      break;
    }
  }
  
  return result;
}

void handleClearHistory() {
  setLED(true);
  Serial.println("STATUS:Ready to clear history - place card now...");
  
  // Hard reset to ensure card detection works
  mfrc522.PCD_Reset();
  delay(50);
  mfrc522.PCD_Init();
  delay(150);
  mfrc522.PCD_AntennaOn();
  delay(50);
  
  // Wait for card with timeout
  unsigned long startTime = millis();
  const unsigned long timeout = 8000; // 8 second timeout
  unsigned long lastStatusTime = millis();
  
  while (millis() - startTime < timeout) {
    // Send status update every 2 seconds
    if (millis() - lastStatusTime > 2000) {
      Serial.println("STATUS:Still waiting for card...");
      lastStatusTime = millis();
      blinkLED(1, 50);
    }
    
    // Check for card multiple times
    for (int i = 0; i < 5; i++) {
      if (mfrc522.PICC_IsNewCardPresent()) {
        delay(10);
        if (mfrc522.PICC_ReadCardSerial()) {
          // Card detected
          Serial.println("STATUS:Card detected, clearing history...");
          String uid = getCardUID();
          
          // Default key for authentication
          MFRC522::MIFARE_Key key;
          for (byte i = 0; i < 6; i++) {
            key.keyByte[i] = 0xFF;
          }
          
          // Empty block data (16 bytes of zeros)
          byte emptyBlock[16];
          memset(emptyBlock, 0, 16);
          
          bool allSuccess = true;
          
          // Clear blocks 9-15 (history blocks)
          for (byte block = 9; block <= 15; block++) {
            // Determine trailer block for authentication
            byte trailerBlock = (block / 4) * 4 + 3;
            
            // Authenticate
            MFRC522::StatusCode status = mfrc522.PCD_Authenticate(
              MFRC522::PICC_CMD_MF_AUTH_KEY_A, 
              trailerBlock, 
              &key, 
              &(mfrc522.uid)
            );
            
            if (status != MFRC522::STATUS_OK) {
              Serial.print("ERROR:Auth failed for block ");
              Serial.println(block);
              allSuccess = false;
              break;
            }
            
            // Write empty data to block
            status = mfrc522.MIFARE_Write(block, emptyBlock, 16);
            if (status != MFRC522::STATUS_OK) {
              Serial.print("ERROR:Write failed for block ");
              Serial.println(block);
              allSuccess = false;
              break;
            }
            
            Serial.print("STATUS:Cleared block ");
            Serial.println(block);
          }
          
          // Halt PICC
          mfrc522.PICC_HaltA();
          mfrc522.PCD_StopCrypto1();
          
          setLED(false);
          
          if (allSuccess) {
            Serial.println("OK:HISTORY_CLEARED:" + uid);
            blinkLED(3, 200);
          } else {
            Serial.println("ERROR:Failed to clear some blocks");
            blinkLED(5, 100);
          }
          
          return;
        }
      }
      delay(15);
    }
    delay(30);
  }
  
  // Timeout reached
  setLED(false);
  Serial.println("ERROR:No card detected (timeout)");
}

uint32_t calculateChecksum(const char* text) {
  // Simple checksum: sum of all characters XOR with magic number
  uint32_t sum = 0;
  for (int i = 0; text[i] != '\0' && i < 12; i++) {
    sum += (uint32_t)text[i] * (i + 1);
  }
  return sum ^ 0xDEADBEEF;
}

void blinkLED(int times, int delayMs) {
  for (int i = 0; i < times; i++) {
    digitalWrite(LED_PIN, HIGH);
    delay(delayMs);
    digitalWrite(LED_PIN, LOW);
    delay(delayMs);
  }
}

void setLED(bool state) {
  digitalWrite(LED_PIN, state ? HIGH : LOW);
}

void initTFT() {
  #if USE_TFT
  // Initialize TFT display
  tft.initR(INITR_BLACKTAB);
  tft.setRotation(1);  // Landscape mode
  tft.fillScreen(ST77XX_BLACK);
  
  // Display header
  tft.setTextColor(ST77XX_CYAN);
  tft.setTextSize(3);
  tft.setCursor(15, 20);
  tft.print("Balance");
  
  // Display initial message
  tft.setTextColor(ST77XX_WHITE);
  tft.setTextSize(2);
  tft.setCursor(10, 70);
  tft.print("Scan Card");
  
  Serial.println("TFT Display initialized");
  #else
  Serial.println("TFT Display disabled");
  #endif
}

void displayWrittenData(String value) {
  #if USE_TFT
  // Clear the data area (keep header)
  tft.fillRect(0, 70, tft.width(), 60, ST77XX_BLACK);
  
  // Display the value in large yellow text
  tft.setTextColor(ST77XX_YELLOW);
  tft.setTextSize(4);
  
  // Calculate center position for text
  int16_t x1, y1;
  uint16_t w, h;
  tft.getTextBounds(value, 0, 0, &x1, &y1, &w, &h);
  int xPos = (tft.width() - w) / 2;
  if (xPos < 0) xPos = 5;  // Ensure text is visible
  
  tft.setCursor(xPos, 90);
  tft.print(value);
  
  Serial.println("TFT Display updated: " + value);
  #endif
}