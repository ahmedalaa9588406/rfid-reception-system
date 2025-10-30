/*
 * RFID Game Device - Balance Subtraction System
 * 
 * This sketch simulates a game device that subtracts 60 EGP from RFID cards.
 * Perfect for testing the auto-sync feature of the reception system.
 * 
 * Hardware Required:
 * - Arduino Uno/Nano/Mega
 * - MFRC522 RFID Reader Module
 * - ST7735 TFT Display (128x160 pixels)
 * - LED (optional, for status indication)
 * - Push Button (for manual game trigger)
 * - 220Ω Resistor (for LED)
 * - 10kΩ Resistor (for button pull-down)
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
 * TFT Display Connection (ST7735):
 * - TFT_CS  -> Pin 5
 * - TFT_DC  -> Pin 6
 * - TFT_RST -> Pin 7
 * - VCC -> 5V
 * - GND -> GND
 * 
 * LED Connection (optional):
 * - LED Anode (+) -> Pin 8 -> 220Ω Resistor -> LED Cathode (-) -> GND
 * 
 * Button Connection:
 * - One side -> Pin 2
 * - Other side -> GND
 * - 10kΩ Resistor between Pin 2 and 5V (pull-up)
 * 
 * Features:
 * - Automatic card detection
 * - Visual feedback on TFT display
 * - Subtracts 60 EGP per game
 * - Supports both numeric (50) and K-prefix (K50) formats
 * - Stores game history in blocks 9-15
 * - LED status indication
 * 
 * Game Cost: 60 EGP
 */

#include <SPI.h>
#include <MFRC522.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ST7735.h>

// Pin definitions
#define RST_PIN         9    // Reset pin for MFRC522
#define SS_PIN          10   // Slave Select pin for MFRC522
#define LED_PIN         8    // Status LED
#define BUTTON_PIN      2    // Game button (optional - card auto-triggers)

// TFT Display pins
#define TFT_CS          5    // TFT Chip Select
#define TFT_DC          6    // TFT Data/Command
#define TFT_RST         7    // TFT Reset

// Game settings
#define GAME_COST       60   // Cost per game in EGP
#define GAME_ID         "A"  // This game's ID (for history tracking)

// Create MFRC522 instance
MFRC522 mfrc522(SS_PIN, RST_PIN);

// Create TFT instance
Adafruit_ST7735 tft = Adafruit_ST7735(TFT_CS, TFT_DC, TFT_RST);

// Card data structure
struct CardData {
  char text[12];        // Text data (up to 11 chars + null terminator)
  uint32_t checksum;    // Checksum for validation
};

// Game state
bool cardPresent = false;
String lastCardUID = "";
unsigned long lastScanTime = 0;
const unsigned long SCAN_COOLDOWN = 3000; // 3 seconds between scans

// Function prototypes
void initSystem();
void initTFT();
void displayWelcomeScreen();
void displayBalance(String balance);
void displayInsufficientFunds();
void displaySuccess(String newBalance);
void displayError(String message);
void processCard();
String readCardBalance();
bool writeCardBalance(String balance);
bool addToHistory(String gameId, int price);
String getCardUID();
float parseBalance(String balanceStr);
String formatBalance(float balance, bool keepPrefix);
uint32_t calculateChecksum(const char* text);
void blinkLED(int times, int delayMs);
void setLED(bool state);

void setup() {
  // Initialize serial for debugging
  Serial.begin(115200);
  while (!Serial) { ; }
  
  // Initialize pins
  pinMode(LED_PIN, OUTPUT);
  pinMode(BUTTON_PIN, INPUT_PULLUP); // Internal pull-up
  digitalWrite(LED_PIN, LOW);
  
  // Initialize system
  initSystem();
  
  Serial.println("Game Device Ready - Cost: " + String(GAME_COST) + " EGP");
}

void loop() {
  // Check for card presence
  if (mfrc522.PICC_IsNewCardPresent() && mfrc522.PICC_ReadCardSerial()) {
    
    // Get current time
    unsigned long currentTime = millis();
    
    // Get card UID
    String uid = getCardUID();
    
    // Check cooldown (prevent multiple scans of same card)
    if (uid == lastCardUID && (currentTime - lastScanTime) < SCAN_COOLDOWN) {
      // Same card within cooldown period - ignore
      mfrc522.PICC_HaltA();
      mfrc522.PCD_StopCrypto1();
      delay(100);
      return;
    }
    
    // Update last scan info
    lastCardUID = uid;
    lastScanTime = currentTime;
    
    // Process the card
    setLED(true);
    processCard();
    setLED(false);
    
    // Halt card
    mfrc522.PICC_HaltA();
    mfrc522.PCD_StopCrypto1();
    
    // Wait before next scan
    delay(500);
  }
  
  delay(100); // Small delay to prevent overwhelming the reader
}

void initSystem() {
  // Initialize SPI
  SPI.begin();
  
  // Initialize RFID reader
  mfrc522.PCD_Init();
  delay(100);
  
  // Check RFID reader
  byte version = mfrc522.PCD_ReadRegister(mfrc522.VersionReg);
  if (version == 0x00 || version == 0xFF) {
    Serial.println("ERROR: MFRC522 not found!");
    while(1) {
      blinkLED(5, 100);
      delay(1000);
    }
  }
  
  Serial.println("MFRC522 Version: 0x" + String(version, HEX));
  
  // Initialize TFT
  initTFT();
  
  // Display welcome screen
  displayWelcomeScreen();
  
  // Blink LED to show ready
  blinkLED(3, 200);
}

void initTFT() {
  tft.initR(INITR_BLACKTAB);
  tft.setRotation(1);  // Landscape mode
  tft.fillScreen(ST77XX_BLACK);
  
  Serial.println("TFT Display initialized");
}

void displayWelcomeScreen() {
  tft.fillScreen(ST77XX_BLACK);
  
  // Game title
  tft.setTextColor(ST77XX_CYAN);
  tft.setTextSize(2);
  tft.setCursor(20, 10);
  tft.print("GAME DEVICE");
  
  // Separator line
  tft.drawFastHLine(0, 30, tft.width(), ST77XX_CYAN);
  
  // Game cost
  tft.setTextColor(ST77XX_YELLOW);
  tft.setTextSize(3);
  tft.setCursor(15, 45);
  tft.print("Cost:");
  tft.setTextSize(4);
  tft.setCursor(20, 75);
  tft.print(String(GAME_COST) + " EGP");
  
  // Instruction
  tft.setTextColor(ST77XX_GREEN);
  tft.setTextSize(1);
  tft.setCursor(15, 120);
  tft.print("Place card to play");
  
  Serial.println("Welcome screen displayed");
}

void displayBalance(String balance) {
  tft.fillScreen(ST77XX_BLACK);
  
  // Header
  tft.setTextColor(ST77XX_CYAN);
  tft.setTextSize(2);
  tft.setCursor(25, 10);
  tft.print("CARD FOUND");
  
  // Balance label
  tft.setTextColor(ST77XX_WHITE);
  tft.setTextSize(1);
  tft.setCursor(30, 45);
  tft.print("Current Balance:");
  
  // Balance value
  tft.setTextColor(ST77XX_GREEN);
  tft.setTextSize(3);
  
  // Center the balance text
  int16_t x1, y1;
  uint16_t w, h;
  tft.getTextBounds(balance, 0, 0, &x1, &y1, &w, &h);
  int xPos = (tft.width() - w) / 2;
  if (xPos < 0) xPos = 5;
  
  tft.setCursor(xPos, 70);
  tft.print(balance);
  
  // Processing message
  tft.setTextColor(ST77XX_YELLOW);
  tft.setTextSize(1);
  tft.setCursor(25, 110);
  tft.print("Processing...");
  
  Serial.println("Balance displayed: " + balance);
}

void displayInsufficientFunds() {
  tft.fillScreen(ST77XX_RED);
  
  // Error icon (X)
  tft.drawLine(40, 20, 120, 80, ST77XX_WHITE);
  tft.drawLine(120, 20, 40, 80, ST77XX_WHITE);
  tft.drawLine(41, 20, 121, 80, ST77XX_WHITE);
  tft.drawLine(121, 20, 41, 80, ST77XX_WHITE);
  
  // Error message
  tft.setTextColor(ST77XX_WHITE);
  tft.setTextSize(2);
  tft.setCursor(5, 100);
  tft.print("INSUFFICIENT");
  tft.setCursor(30, 120);
  tft.print("BALANCE!");
  
  Serial.println("Insufficient funds displayed");
  blinkLED(5, 100);
  
  delay(3000);
  displayWelcomeScreen();
}

void displaySuccess(String newBalance) {
  tft.fillScreen(ST77XX_GREEN);
  
  // Success icon (checkmark)
  tft.drawLine(40, 50, 60, 70, ST77XX_WHITE);
  tft.drawLine(60, 70, 120, 20, ST77XX_WHITE);
  tft.drawLine(40, 51, 60, 71, ST77XX_WHITE);
  tft.drawLine(60, 71, 120, 21, ST77XX_WHITE);
  
  // Success message
  tft.setTextColor(ST77XX_WHITE);
  tft.setTextSize(2);
  tft.setCursor(20, 90);
  tft.print("SUCCESS!");
  
  // New balance
  tft.setTextSize(1);
  tft.setCursor(15, 115);
  tft.print("New Balance: " + newBalance);
  
  Serial.println("Success! New balance: " + newBalance);
  blinkLED(3, 150);
  
  delay(3000);
  displayWelcomeScreen();
}

void displayError(String message) {
  tft.fillScreen(ST77XX_RED);
  
  tft.setTextColor(ST77XX_WHITE);
  tft.setTextSize(2);
  tft.setCursor(30, 30);
  tft.print("ERROR!");
  
  tft.setTextSize(1);
  tft.setCursor(10, 70);
  
  // Word wrap the message
  int lineY = 70;
  String word = "";
  for (unsigned int i = 0; i < message.length(); i++) {
    if (message[i] == ' ' || i == message.length() - 1) {
      if (i == message.length() - 1) word += message[i];
      tft.print(word);
      tft.print(" ");
      word = "";
      
      if (tft.getCursorX() > tft.width() - 20) {
        lineY += 15;
        tft.setCursor(10, lineY);
      }
    } else {
      word += message[i];
    }
  }
  
  Serial.println("Error: " + message);
  blinkLED(5, 100);
  
  delay(4000);
  displayWelcomeScreen();
}

void processCard() {
  Serial.println("Processing card...");
  
  // Read current balance
  String balanceStr = readCardBalance();
  
  if (balanceStr == "ERROR") {
    displayError("Cannot read card");
    return;
  }
  
  if (balanceStr == "INVALID" || balanceStr == "") {
    displayError("Invalid card data");
    return;
  }
  
  // Display current balance
  displayBalance(balanceStr);
  delay(1500);
  
  // Parse balance
  float currentBalance = parseBalance(balanceStr);
  bool hasKPrefix = balanceStr.startsWith("K") || balanceStr.startsWith("k");
  
  Serial.println("Current balance: " + String(currentBalance));
  Serial.println("Has K prefix: " + String(hasKPrefix ? "Yes" : "No"));
  
  // Check if sufficient funds
  if (currentBalance < GAME_COST) {
    displayInsufficientFunds();
    return;
  }
  
  // Calculate new balance
  float newBalance = currentBalance - GAME_COST;
  
  // Format new balance (keep K prefix if it was there)
  String newBalanceStr = formatBalance(newBalance, hasKPrefix);
  
  Serial.println("New balance: " + newBalanceStr);
  
  // Write new balance to card
  if (!writeCardBalance(newBalanceStr)) {
    displayError("Write failed! Try again");
    return;
  }
  
  // Add to game history
  if (!addToHistory(GAME_ID, GAME_COST)) {
    Serial.println("Warning: Could not add to history");
  }
  
  // Display success
  displaySuccess(newBalanceStr);
}

String readCardBalance() {
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
    Serial.println("Auth failed");
    return "ERROR";
  }
  
  // Read data
  byte buffer[18];
  byte size = sizeof(buffer);
  status = mfrc522.MIFARE_Read(blockAddr, buffer, &size);
  if (status != MFRC522::STATUS_OK) {
    Serial.println("Read failed");
    return "ERROR";
  }
  
  // Extract card data
  CardData cardData;
  memcpy(&cardData, buffer, sizeof(CardData));
  
  // Verify checksum
  if (cardData.checksum != calculateChecksum(cardData.text)) {
    Serial.println("Invalid checksum");
    return "INVALID";
  }
  
  cardData.text[sizeof(cardData.text) - 1] = '\0';
  return String(cardData.text);
}

bool writeCardBalance(String balance) {
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
    Serial.println("Auth failed for write");
    return false;
  }
  
  // Prepare data
  byte dataBlock[16];
  memset(dataBlock, 0, 16);
  
  CardData cardData;
  memset(cardData.text, 0, sizeof(cardData.text));
  strncpy(cardData.text, balance.c_str(), sizeof(cardData.text) - 1);
  cardData.checksum = calculateChecksum(cardData.text);
  
  memcpy(dataBlock, &cardData, sizeof(CardData));
  
  // Write data
  status = mfrc522.MIFARE_Write(blockAddr, dataBlock, 16);
  if (status != MFRC522::STATUS_OK) {
    Serial.println("Write failed");
    return false;
  }
  
  Serial.println("Balance written: " + balance);
  return true;
}

bool addToHistory(String gameId, int price) {
  // Find first available history block (blocks 9-15)
  for (byte block = 9; block <= 15; block++) {
    // Skip trailer blocks
    if (block == 11 || block == 15) continue;
    
    // Read existing data
    byte trailerBlock = (block / 4) * 4 + 3;
    
    MFRC522::MIFARE_Key key;
    for (byte i = 0; i < 6; i++) {
      key.keyByte[i] = 0xFF;
    }
    
    // Authenticate
    MFRC522::StatusCode status;
    status = mfrc522.PCD_Authenticate(MFRC522::PICC_CMD_MF_AUTH_KEY_A, trailerBlock, &key, &(mfrc522.uid));
    if (status != MFRC522::STATUS_OK) continue;
    
    // Read block
    byte buffer[18];
    byte size = sizeof(buffer);
    status = mfrc522.MIFARE_Read(block, buffer, &size);
    if (status != MFRC522::STATUS_OK) continue;
    
    // Convert to string
    String existing = "";
    for (int i = 0; i < 16; i++) {
      if (buffer[i] >= 32 && buffer[i] <= 126) {
        existing += (char)buffer[i];
      } else if (buffer[i] == 0) {
        break;
      }
    }
    
    // Create new entry
    String newEntry = gameId + ":" + String(price) + "#";
    
    // Check if we can append to this block
    if (existing.length() + newEntry.length() <= 16) {
      existing += newEntry;
      
      // Write updated data
      byte writeBuffer[16];
      memset(writeBuffer, 0, 16);
      existing.toCharArray((char*)writeBuffer, 16);
      
      status = mfrc522.MIFARE_Write(block, writeBuffer, 16);
      if (status == MFRC522::STATUS_OK) {
        Serial.println("History added to block " + String(block) + ": " + newEntry);
        return true;
      }
    }
  }
  
  Serial.println("No space for history entry");
  return false; // No space available
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

float parseBalance(String balanceStr) {
  // Remove K prefix if present
  if (balanceStr.startsWith("K") || balanceStr.startsWith("k")) {
    balanceStr = balanceStr.substring(1);
  }
  
  // Parse to float
  return balanceStr.toFloat();
}

String formatBalance(float balance, bool keepPrefix) {
  // Format with optional K prefix
  String result = "";
  
  if (keepPrefix) {
    result = "K";
  }
  
  // Add integer part
  result += String((int)balance);
  
  return result;
}

uint32_t calculateChecksum(const char* text) {
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
