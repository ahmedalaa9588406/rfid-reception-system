# Arduino READ_HISTORY Command Support

## Overview
To support the "Cards History" feature in the Python GUI, the Arduino needs to respond to a `READ_HISTORY` command that reads blocks 9-15 from the RFID card and sends the history data back to the computer.

## What to Add to Your Arduino Code

### 1. Add String Buffer at the Top
Add this global variable after your existing globals:

```cpp
String serialCommand = "";
```

### 2. Add Command Handler Function
Add this function before `setup()`:

```cpp
void handleReadHistory() {
  // Wait for card
  if (!mfrc522.PICC_IsNewCardPresent() || !mfrc522.PICC_ReadCardSerial()) {
    Serial.println("ERROR:No card detected");
    return;
  }
  
  // Get card UID
  String uid = "";
  for (byte i = 0; i < mfrc522.uid.size; i++) {
    if (i > 0) uid += " ";
    if (mfrc522.uid.uidByte[i] < 0x10) uid += "0";
    uid += String(mfrc522.uid.uidByte[i], HEX);
  }
  uid.toUpperCase();
  
  // Send start marker
  Serial.print("HISTORY_START:");
  Serial.println(uid);
  
  // Read blocks 9-15 (history blocks)
  for (byte block = 9; block <= 15; block++) {
    byte buffer[18];
    byte size = sizeof(buffer);
    
    if (readBlock(block, buffer, size)) {
      // Convert buffer to string
      String blockData = "";
      for (int i = 0; i < 16; i++) {
        if (buffer[i] >= 32 && buffer[i] <= 126) {
          blockData += (char)buffer[i];
        } else if (buffer[i] == 0x00) {
          break; // Stop at null terminator
        }
      }
      
      // Send block data
      Serial.print("HISTORY_BLOCK:");
      Serial.print(block);
      Serial.print(":");
      Serial.println(blockData);
    }
  }
  
  // Send end marker
  Serial.println("HISTORY_END");
  
  cleanup();
}
```

### 3. Modify loop() Function
Replace your existing `loop()` function with this enhanced version that handles serial commands:

```cpp
void loop() {
  // Check for serial commands
  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c == '\n') {
      serialCommand.trim();
      
      if (serialCommand == "READ_HISTORY") {
        handleReadHistory();
      }
      // Add other command handlers here if needed
      
      serialCommand = "";
    } else {
      serialCommand += c;
    }
  }
  
  // Original card detection logic
  if (!mfrc522.PICC_IsNewCardPresent() || !mfrc522.PICC_ReadCardSerial()) return;

  byte buffer[18]; byte size = sizeof(buffer);
  if (!readBlock(TARGET_BLOCK, buffer, size)) return;

  String cardData = "";
  for (int i = 0; i < 16; i++) {
    if (buffer[i] >= 32 && buffer[i] <= 126)
      cardData += (char)buffer[i];
  }
  cardData.trim();
  Serial.println("Card Data: " + cardData);

  if (cardData.equalsIgnoreCase("master")) {
    displayMessage("Done");
    cleanup();
    return;
  }

  if (cardData.startsWith("k") || cardData.startsWith("K")) {
    int newPrice = cardData.substring(1).toInt();
    if (newPrice > 0) {
      savePriceToEEPROM(newPrice);
      GAME_PRICE = newPrice;
      displayPrice();
    }
    cleanup();
    return;
  }

  int balance = cardData.toInt();
  if (balance < GAME_PRICE) {
    displayMessage("Not enough");
  } else {
    int newVal = balance - GAME_PRICE;
    String newBal = String(newVal);
    byte newBuf[16];
    for (int i = 0; i < 16; i++) {
      if (i < newBal.length()) newBuf[i] = newBal[i];
      else newBuf[i] = 0x20;
    }
    if (writeBlock(TARGET_BLOCK, newBuf)) {
      appendHistory(GAME_ID, GAME_PRICE);
      displayMessage("Done");
    }
  }

  cleanup();
}
```

## How It Works

1. **Command Detection**: The Arduino listens for the `READ_HISTORY\n` command via serial
2. **Card Reading**: When received, it waits for a card to be present
3. **Block Reading**: Reads blocks 9-15 (where game history is stored)
4. **Data Transmission**: Sends history data in this format:
   ```
   HISTORY_START:<card_uid>
   HISTORY_BLOCK:9:<data_from_block_9>
   HISTORY_BLOCK:10:<data_from_block_10>
   ...
   HISTORY_BLOCK:15:<data_from_block_15>
   HISTORY_END
   ```

## History Data Format

Each block contains entries in the format: `GameID:Price#GameID:Price#`

Example: `A:50#B:30#C:25#`
- Game A cost 50 EGP
- Game B cost 30 EGP  
- Game C cost 25 EGP

## Testing

1. Upload the modified Arduino code
2. Place a card with history on the reader
3. In the Python GUI, click "📜 Cards History" button
4. The dialog will display all game history in a table format

## Notes

- The Python GUI already has the `read_history()` method in `serial_comm.py`
- The dialog displays history organized by block number, game ID, and price
- Empty blocks are automatically skipped
- Invalid entries are marked as "Invalid" in the display
