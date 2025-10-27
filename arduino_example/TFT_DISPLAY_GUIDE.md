# TFT Display Integration Guide

## Overview

The Arduino code now includes **optional ST7735 TFT display support** that shows the card balance in real-time on a small LCD screen. This provides visual feedback directly on the hardware.

## What Was Added

### 1. **TFT Display Support**
- Shows "Balance" header
- Displays card value in large yellow text when read/written
- Centered text for better visibility
- Optional - works with or without display connected

### 2. **Display Features**
- **Screen Layout:**
  ```
  ┌─────────────────────┐
  │  Balance     (Cyan) │
  │                     │
  │    50 EGP  (Yellow) │
  │                     │
  └─────────────────────┘
  ```

- **Auto-updates:** Display updates automatically when card is read or written
- **Visual feedback:** See balance without checking computer screen

## Hardware Requirements

### Required (as before):
- Arduino Uno/Nano/Mega
- MFRC522 RFID Reader Module
- USB cable

### Optional (for display):
- **ST7735 TFT Display** (1.8" 128x160 pixels)
- Available on Amazon/AliExpress (~$5-10)

## Wiring Diagram

### MFRC522 (Required):
```
MFRC522 Pin → Arduino Pin
SDA         → Pin 10
SCK         → Pin 13
MOSI        → Pin 11
MISO        → Pin 12
RST         → Pin 9
GND         → GND
3.3V        → 3.3V (IMPORTANT: NOT 5V!)
```

### ST7735 TFT Display (Optional):
```
TFT Pin     → Arduino Pin
CS          → Pin 5
DC          → Pin 6
RST         → Pin 7
SDA/MOSI    → Pin 11 (shared with MFRC522)
SCK         → Pin 13 (shared with MFRC522)
VCC         → 5V
GND         → GND
```

**Note:** The TFT and MFRC522 share SPI bus (pins 11, 13) which is normal and works fine.

## Installation Steps

### Step 1: Install Required Libraries

Open Arduino IDE, go to **Tools → Manage Libraries**, then install:

1. **MFRC522** by GithubCommunity
   - Search: "MFRC522"
   - Click Install

2. **Adafruit GFX Library**
   - Search: "Adafruit GFX"
   - Click Install

3. **Adafruit ST7735 and ST7789 Library**
   - Search: "Adafruit ST7735"
   - Click Install
   - If prompted, install all dependencies (click "Install All")

### Step 2: Configure Display Usage

In the Arduino code, look for line 62:
```cpp
#define USE_TFT         true // Set to false to disable TFT display
```

**With Display:**
- Keep as `true`
- Wire the TFT display as shown above
- Upload code

**Without Display:**
- Change to `false`: `#define USE_TFT false`
- Upload code
- Display functions are disabled, no errors

### Step 3: Upload the Code

1. Open `rfid_reader_example.ino` in Arduino IDE
2. Select your board: **Tools → Board → Arduino Uno**
3. Select your port: **Tools → Port → COM3** (your port)
4. Click **Upload** (→ button)
5. Wait for "Done uploading"

### Step 4: Test the Display

1. Open **Tools → Serial Monitor** (115200 baud)
2. You should see:
   ```
   RFID Reader Ready
   MFRC522 Version: 0x92
   TFT Display initialized
   ```
3. Display should show:
   - "Balance" header in cyan
   - "Scan Card" message in white

## How It Works

### On Card Read:
1. Arduino reads card UID
2. Attempts to read stored data from card
3. If data found: displays on TFT and sends to Python
4. Format: `UID:AF11FC1C:50`

### On Card Write:
1. Python sends: `WRITE:50`
2. Arduino waits for card (10 seconds)
3. Writes "50" to card memory
4. **Displays "50" on TFT screen** ✨
5. Sends confirmation to Python

### Display Updates:
```cpp
displayWrittenData("50");  // Shows "50" in large yellow text
```

## Display Behavior

| Action | Display Shows |
|--------|---------------|
| Startup | "Scan Card" |
| Card Read | Card balance (e.g., "50 EGP") |
| Card Write | New value (e.g., "K100") |
| No Card | Previous value remains |

## Troubleshooting

### "TFT Display disabled" in Serial Monitor
- `USE_TFT` is set to `false`
- This is normal if you don't have a display
- System works fine without TFT

### Display Shows Garbage/Random Pixels
- Check wiring (especially CS, DC, RST pins)
- Try different `INITR_` mode:
  ```cpp
  tft.initR(INITR_BLACKTAB);  // Try: INITR_GREENTAB or INITR_REDTAB
  ```
- Check power supply (needs 5V)

### Display is Blank/White
- Check SPI connections (MOSI/pin 11, SCK/pin 13)
- Verify VCC is connected to 5V
- Try adjusting rotation:
  ```cpp
  tft.setRotation(1);  // Try 0, 1, 2, or 3
  ```

### Text is Off-Screen
- Adjust text size:
  ```cpp
  tft.setTextSize(3);  // Try smaller: 2 or 1
  ```

### Display Works but RFID Doesn't
- Check MFRC522 wiring
- MFRC522 **MUST use 3.3V**, not 5V!
- Verify MFRC522 SS pin (pin 10) is not shared with TFT

### "Compilation error: Adafruit_ST7735 not found"
- Install Adafruit ST7735 library (see Step 1)
- Restart Arduino IDE after installing

## Disabling Display (No Hardware)

If you don't have a TFT display, simply set:
```cpp
#define USE_TFT false
```

The code will:
- ✅ Skip all TFT initialization
- ✅ Skip all display updates
- ✅ Work normally with RFID only
- ✅ No compilation errors
- ✅ No runtime errors

## Benefits of TFT Display

1. **Visual Confirmation:** Employee sees balance immediately
2. **Independent Feedback:** Works even if PC crashes
3. **Customer View:** Card holder can see their balance
4. **Professional Look:** Makes system look more polished
5. **Debugging:** Easy to see if write succeeded

## Code Structure

### New Functions:
```cpp
void initTFT()                      // Initialize display
void displayWrittenData(String)     // Show value on screen
```

### Modified Functions:
```cpp
handleRead()    // Now displays card data
handleWrite()   // Now displays written value
setup()         // Calls initTFT()
```

### Conditional Compilation:
```cpp
#if USE_TFT
  // TFT code here
#endif
```
Only compiled if `USE_TFT` is `true`.

## Example Output

### Serial Monitor:
```
RFID Reader Ready
MFRC522 Version: 0x92
TFT Display initialized
UID:AF11FC1C:50
TFT Display updated: 50
OK:WROTE:AF11FC1C:50
TFT Display updated: 50
```

### TFT Screen:
```
┌─────────────────────┐
│  Balance            │
│                     │
│      50             │
│                     │
└─────────────────────┘
```

## Summary

- ✅ **Optional feature** - works with or without display
- ✅ **Easy to disable** - one line change
- ✅ **Shared SPI** - no extra pins needed
- ✅ **Auto-centering** - text always centered
- ✅ **Color coded** - header (cyan), value (yellow)
- ✅ **Low cost** - display is ~$5-10

The TFT display adds professional visual feedback without complicating the system. Perfect for customer-facing installations!
