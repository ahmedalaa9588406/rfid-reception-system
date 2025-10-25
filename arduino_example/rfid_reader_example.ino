/*
 * COMPLETE RFID Reader System for RFID Reception System
 * 
 * This sketch provides full MFRC522 RFID integration with the Python application.
 * 
 * Hardware Required:
 * - Arduino Uno/Nano/Mega
 * - MFRC522 RFID Reader Module
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
 * Protocol:
 * - READ\n -> Returns UID:<card_uid>\n or ERROR:<message>\n
 * - WRITE:<amount>\n -> Returns OK:WROTE:<uid>:<amount>\n or ERROR:<message>\n
 * - PING\n -> Returns PONG\n
 * 
 * Installation:
 * 1. Install MFRC522 library: Tools -> Manage Libraries -> Search "MFRC522" -> Install
 * 2. Upload this sketch to your Arduino
 * 3. Note the COM port in Tools -> Port
 * 4. Configure this port in your Python application
 */

#include <SPI.h>
#include <MFRC522.h>

// Pin definitions
#define RST_PIN         9    // Reset pin for MFRC522
#define SS_PIN          10   // Slave Select pin for MFRC522
#define LED_PIN         8    // Status LED (optional)

// Create MFRC522 instance
MFRC522 mfrc522(SS_PIN, RST_PIN);

// Communication variables
String inputString = "";
boolean stringComplete = false;

// Card data structure for writing
struct CardData {
  float amount;
  uint32_t checksum;
};

// Function prototypes
void processCommand(String command);
void handleRead();
void handleWrite(float amount);
String getCardUID();
bool writeCardData(float amount);
float readCardData();
uint32_t calculateChecksum(float amount);
void blinkLED(int times, int delayMs);
void setLED(bool state);

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
  
  if (command.equals("READ")) {
    handleRead();
  }
  else if (command.startsWith("WRITE:")) {
    String amountStr = command.substring(6);
    float amount = amountStr.toFloat();
    if (amount <= 0) {
      Serial.println("ERROR:Invalid amount");
    } else {
      handleWrite(amount);
    }
  }
  else if (command.equals("PING")) {
    Serial.println("PONG");
  }
  else if (command.equals("RESET")) {
    mfrc522.PCD_Init();
    Serial.println("OK:RESET");
  }
  else {
    Serial.println("ERROR:Unknown command");
  }
}

void handleRead() {
  setLED(true); // Turn on LED
  
  // Wait for card (with timeout)
  unsigned long startTime = millis();
  const unsigned long timeout = 3000; // 3 second timeout
  
  while (millis() - startTime < timeout) {
    // Look for new cards
    if (!mfrc522.PICC_IsNewCardPresent()) {
      delay(50);
      continue;
    }
    
    // Select one of the cards
    if (!mfrc522.PICC_ReadCardSerial()) {
      delay(50);
      continue;
    }
    
    // Card detected successfully
    String uid = getCardUID();
    Serial.println("UID:" + uid);
    
    // Halt PICC
    mfrc522.PICC_HaltA();
    mfrc522.PCD_StopCrypto1();
    
    setLED(false);
    blinkLED(2, 100); // Success indication
    return;
  }
  
  // Timeout reached
  setLED(false);
  Serial.println("ERROR:No card detected (timeout)");
}

void handleWrite(float amount) {
  setLED(true);
  
  // Wait for card (with timeout)
  unsigned long startTime = millis();
  const unsigned long timeout = 3000;
  
  while (millis() - startTime < timeout) {
    // Look for new cards
    if (!mfrc522.PICC_IsNewCardPresent()) {
      delay(50);
      continue;
    }
    
    // Select one of the cards
    if (!mfrc522.PICC_ReadCardSerial()) {
      delay(50);
      continue;
    }
    
    // Card detected, get UID
    String uid = getCardUID();
    
    // Attempt to write data
    if (writeCardData(amount)) {
      Serial.println("OK:WROTE:" + uid + ":" + String(amount, 2));
      blinkLED(3, 150); // Success indication
    } else {
      Serial.println("ERROR:Failed to write to card");
      blinkLED(5, 100); // Error indication
    }
    
    // Halt PICC
    mfrc522.PICC_HaltA();
    mfrc522.PCD_StopCrypto1();
    
    setLED(false);
    return;
  }
  
  // Timeout reached
  setLED(false);
  Serial.println("ERROR:No card detected for writing (timeout)");
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

bool writeCardData(float amount) {
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
  cardData.amount = amount;
  cardData.checksum = calculateChecksum(amount);
  
  // Copy data to block
  memcpy(dataBlock, &cardData, sizeof(CardData));
  
  // Write data to block
  status = mfrc522.MIFARE_Write(blockAddr, dataBlock, 16);
  if (status != MFRC522::STATUS_OK) {
    return false;
  }
  
  return true;
}

float readCardData() {
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
    return -1.0;
  }
  
  // Read data from block
  byte buffer[18];
  byte size = sizeof(buffer);
  status = mfrc522.MIFARE_Read(blockAddr, buffer, &size);
  if (status != MFRC522::STATUS_OK) {
    return -1.0;
  }
  
  // Extract card data
  CardData cardData;
  memcpy(&cardData, buffer, sizeof(CardData));
  
  // Verify checksum
  if (cardData.checksum != calculateChecksum(cardData.amount)) {
    return -1.0; // Invalid data
  }
  
  return cardData.amount;
}

uint32_t calculateChecksum(float amount) {
  // Simple checksum: multiply by 1000 and XOR with magic number
  uint32_t temp = (uint32_t)(amount * 1000);
  return temp ^ 0xDEADBEEF;
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
