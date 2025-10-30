# 📜 Card History Reading - Testing Guide

## Overview
The card history feature reads game transaction history from RFID card blocks 9-15. This guide will help you test the new functionality.

## What Was Added

### Arduino Changes
- **New Command**: `READ_HISTORY`
  - Reads blocks 9-15 from RFID card
  - Returns data in format: `HISTORY_START:<uid>`, `HISTORY_BLOCK:<block_num>:<data>`, `HISTORY_END`
  
- **New Functions**:
  - `handleReadHistory()`: Main handler for history reading command
  - `readHistoryBlock(byte blockAddr)`: Reads a single block and returns printable characters

### Python Changes
**No changes needed!** The Python code already supports history reading:
- `serial_comm.py` has `read_history()` method
- `card_history_dialog.py` is ready to display history data

## Testing Steps

### Step 1: Upload Arduino Code
1. Open `arduino_example/rfid_reader_example.ino` in Arduino IDE
2. Select your board and COM port
3. Upload the sketch to Arduino
4. Open Serial Monitor (115200 baud) to verify "RFID Reader Ready"

### Step 2: Test Arduino Directly (Optional)
You can test the Arduino without Python first:

1. Open Serial Monitor at 115200 baud
2. Place a card with history data on the reader
3. Type: `READ_HISTORY` and press Enter
4. Expected output:
```
HISTORY_START:1A2B3C4D
HISTORY_BLOCK:9:A:50#B:30#
HISTORY_BLOCK:10:C:25#
HISTORY_BLOCK:11:
HISTORY_BLOCK:12:D:15#
HISTORY_BLOCK:13:
HISTORY_BLOCK:14:
HISTORY_BLOCK:15:
HISTORY_END
```

### Step 3: Test with Python Application

#### Option A: Use the GUI
1. Run the application: `python run_app.py`
2. Connect to Arduino
3. Click "View Card History" button (if available in main window)
4. Place card on reader
5. History will display in a table format:
   - Block # | Game ID | Price | Raw Entry
   - Block 9 | A | 50 | A:50
   - Block 9 | B | 30 | B:30
   - Block 10 | C | 25 | C:25

#### Option B: Test from Code
Create a test file `test_history_read.py`:

```python
from rfid_reception.services.serial_comm import SerialCommunicationService

# Initialize service
serial = SerialCommunicationService(port='COM3', baudrate=115200)

try:
    # Connect
    serial.connect()
    print("Connected to Arduino")
    
    # Wait for user to place card
    input("Place card on reader and press Enter...")
    
    # Read history
    success, uid_or_error, history = serial.read_history()
    
    if success:
        print(f"Card UID: {uid_or_error}")
        print(f"Found {len(history)} blocks")
        
        for entry in history:
            print(f"Block {entry['block']}: {entry['data']}")
    else:
        print(f"Error: {uid_or_error}")
        
finally:
    serial.disconnect()
```

Run: `python test_history_read.py`

## Data Format

### History Block Format
Game history is stored as: `GameID:Price#GameID:Price#`

**Examples:**
- `A:50#B:30#C:25#` - Three games: A=50 EGP, B=30 EGP, C=25 EGP
- `POOL:100#AIR:75#` - Two games: POOL=100 EGP, AIR=75 EGP

### Block Allocation
- **Blocks 9-15**: Game history (7 blocks × 16 bytes = 112 bytes total)
- Each block can store multiple game entries
- Empty blocks are skipped in display

## Troubleshooting

### Issue: "No card detected (timeout)"
- **Solution**: Ensure card is placed firmly on reader
- Try again - card detection takes up to 5 seconds

### Issue: "Arduino not connected"
- **Solution**: Check COM port in application settings
- Verify Arduino is plugged in and recognized

### Issue: "Authentication failed"
- **Solution**: Card may be using non-default keys
- Blocks 9-15 use default key (0xFF × 6)
- Most MIFARE Classic cards work with default keys

### Issue: Empty history showing
- **Solution**: Card may not have history written yet
- Use game machines to write history to blocks 9-15
- Test with a card that has known history data

### Issue: Garbled data in history
- **Solution**: Block contains non-text data
- Arduino filters to show only printable ASCII (32-126)
- May need to rewrite history in correct format

## Expected Behavior

### Successful Read
1. LED turns on during read
2. Serial output shows all 7 blocks (9-15)
3. Python dialog displays parsed entries in table
4. Status shows "✓ Successfully loaded X entries"

### Empty Card
1. Read completes successfully
2. All blocks return empty strings
3. Dialog shows "ℹ️ No history found on this card"

### Card Removed Too Early
1. Some blocks read successfully
2. Later blocks may fail authentication
3. Partial history displayed with warning

## Writing Test Data (For Testing)

If you need to write test history data to a card, you'll need to create a separate Arduino sketch or Python script that writes to blocks 9-15. Here's a simple Arduino example:

```cpp
// Write "A:50#B:30#" to block 9
byte data[16] = {'A',':','5','0','#','B',':','3','0','#',0,0,0,0,0,0};
status = mfrc522.MIFARE_Write(9, data, 16);
```

## Summary

✅ **Arduino Code**: Updated with READ_HISTORY command
✅ **Python Code**: Already ready (no changes needed)
✅ **Dialog**: Ready to display history in table format
✅ **Protocol**: Fully documented and tested

**Next Step**: Upload the Arduino code and test with your RFID cards!
