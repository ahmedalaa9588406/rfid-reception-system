# Complete Arduino RFID System for RFID Reception System

This directory contains a **production-ready** Arduino sketch with full MFRC522 RFID integration.

## 📋 Hardware Requirements

### Required Components
- **Arduino Uno, Nano, or Mega** (any Arduino with SPI support)
- **MFRC522 RFID Reader Module** (13.56 MHz)
- **USB Cable** (Type A to Type B for Uno/Mega, or Type A to Mini-B for Nano)
- **RFID Cards/Tags** (MIFARE Classic 1K or compatible)

### Optional Components
- **LED** (any color, for status indication)
- **220Ω Resistor** (for LED)
- **Breadboard and Jumper Wires**

## 🔌 Wiring Diagram

### MFRC522 to Arduino Connections

| MFRC522 Pin | Arduino Uno/Nano Pin | Arduino Mega Pin | Description |
|-------------|---------------------|------------------|-------------|
| SDA (SS)    | 10                  | 53               | Slave Select |
| SCK         | 13                  | 52               | Serial Clock |
| MOSI        | 11                  | 51               | Master Out Slave In |
| MISO        | 12                  | 50               | Master In Slave Out |
| IRQ         | Not connected       | Not connected    | Interrupt (optional) |
| GND         | GND                 | GND              | Ground |
| RST         | 9                   | 5                | Reset |
| 3.3V        | 3.3V                | 3.3V             | Power Supply |

⚠️ **IMPORTANT**: MFRC522 operates at **3.3V**. Do NOT connect to 5V or you may damage the module!

### Optional LED Connection
- **LED Anode (+)** → Pin 8 → 220Ω Resistor → **LED Cathode (-)** → GND

## 📥 Software Installation

### Step 1: Install Arduino IDE
1. Download from [arduino.cc/en/software](https://www.arduino.cc/en/software)
2. Install the Arduino IDE (version 1.8.19 or newer recommended)

### Step 2: Install MFRC522 Library
1. Open Arduino IDE
2. Go to **Tools** → **Manage Libraries...**
3. Search for "MFRC522"
4. Install **MFRC522 by GithubCommunity** (version 1.4.10 or newer)

### Step 3: Upload the Sketch
1. Open `rfid_reader_example.ino` in Arduino IDE
2. Connect your Arduino to PC via USB
3. Select your board: **Tools** → **Board** → **Arduino Uno** (or your model)
4. Select the correct port: **Tools** → **Port** → **COM3** (or your port)
5. Click **Upload** button (→)
6. Wait for "Done uploading" message

### Step 4: Verify Installation
1. Open **Tools** → **Serial Monitor**
2. Set baud rate to **115200**
3. You should see:
   ```
   RFID Reader Ready
   MFRC522 Version: 0x92
   ```
4. The LED should blink 3 times indicating system is ready

## 🔧 Testing the System

### Test 1: Check Connection
1. In Serial Monitor, type: `PING` and press Enter
2. Expected response: `PONG`

### Test 2: Read a Card
1. Type: `READ` and press Enter
2. Place an RFID card near the reader within 3 seconds
3. Expected response: `UID:A1B2C3D4` (your card's unique ID)
4. LED blinks 2 times on success

### Test 3: Write to a Card
1. Type: `WRITE:100.50` and press Enter
2. Place an RFID card near the reader within 3 seconds
3. Expected response: `OK:WROTE:A1B2C3D4:100.50`
4. LED blinks 3 times on success

## 📡 Communication Protocol

The Python application communicates with Arduino using text-based commands over serial (115200 baud).

### Commands

| Command | Format | Response (Success) | Response (Error) |
|---------|--------|-------------------|------------------|
| READ    | `READ\n` | `UID:<card_uid>\n` | `ERROR:<message>\n` |
| WRITE   | `WRITE:<amount>\n` | `OK:WROTE:<uid>:<amount>\n` | `ERROR:<message>\n` |
| PING    | `PING\n` | `PONG\n` | - |
| RESET   | `RESET\n` | `OK:RESET\n` | - |

### Examples
```
> READ
< UID:04A1B2C3D4E5F6

> WRITE:250.75
< OK:WROTE:04A1B2C3D4E5F6:250.75

> PING
< PONG
```

## 🐍 Python Integration

The Arduino system is designed to work seamlessly with the Python application. Here's how the integration works:

### In Your Python Code:
```python
from rfid_reception.services.serial_comm import SerialCommunicationService

# Initialize serial connection
serial_service = SerialCommunicationService(port='COM3', baudrate=115200)
serial_service.connect()

# Read a card
success, uid = serial_service.read_card()
if success:
    print(f"Card UID: {uid}")

# Write amount to card
success, uid, message = serial_service.write_card(100.50)
if success:
    print(f"Successfully wrote to card {uid}")
```

The existing `serial_comm.py` service already handles all communication!

## 💾 Card Data Storage

### Data Written to Card
The Arduino stores the following on each RFID card:
- **Amount** (float, 4 bytes)
- **Checksum** (uint32_t, 4 bytes) - for data integrity

Data is written to **Block 4** (Sector 1) of MIFARE Classic cards.

### Database Storage
The Python application stores:
- Card UID
- Balance history
- Transaction logs
- Timestamps
- Employee information

## ⚠️ Troubleshooting

### "MFRC522 not found! Check wiring"
- Verify all connections match the wiring diagram
- Ensure MFRC522 is connected to **3.3V**, not 5V
- Check that SPI pins are correct for your Arduino model
- LED will blink rapidly (5 times) repeatedly

### "No card detected (timeout)"
- Ensure card is placed close to the reader (within 3cm)
- Check that you're using MIFARE Classic 1K cards (13.56 MHz)
- Some cards may be damaged or incompatible

### "Failed to write to card"
- Card may be write-protected
- Try using the default authentication key (0xFFFFFFFFFFFF)
- Some cards use different keys - check card documentation

### Serial Port Issues
- **Windows**: Check Device Manager → Ports (COM & LPT)
- **Linux/Mac**: Look for `/dev/ttyUSB0` or `/dev/ttyACM0`
- Ensure no other application is using the port

## 🎯 Features

✅ **Full MFRC522 Integration** - Complete SPI communication  
✅ **Card UID Reading** - Unique identification  
✅ **Data Writing** - Store amounts on cards  
✅ **Checksum Validation** - Data integrity checks  
✅ **LED Feedback** - Visual status indication  
✅ **Error Handling** - Comprehensive error messages  
✅ **Timeout Protection** - 3-second timeouts prevent hanging  
✅ **Python Compatible** - Works with existing serial_comm.py  

## 📦 Supported RFID Cards

- ✅ MIFARE Classic 1K (most common)
- ✅ MIFARE Classic 4K
- ✅ MIFARE Ultralight (read-only)
- ❌ MIFARE DESFire (different protocol)
- ❌ EM4100 (125 kHz, incompatible)

## 🔐 Security Notes

- Default authentication key is used (`0xFFFFFFFFFFFF`)
- For production systems, consider changing card sector keys
- Card data includes checksum for integrity verification
- Physical access to cards is required for reading/writing

## 📞 Need Help?

1. Check the wiring diagram carefully
2. Verify MFRC522 library is installed
3. Test with Serial Monitor first
4. Check the troubleshooting section
5. Consult MFRC522 datasheet for advanced features

## 📝 Notes

- Baud rate: **115200** (must match Python settings)
- Timeout: **3 seconds** for card detection
- Max read distance: **~3-5 cm** (depends on antenna size)
- Card memory: Block 4 used for storage (Sector 1)
- Serial buffer: 200 bytes reserved
