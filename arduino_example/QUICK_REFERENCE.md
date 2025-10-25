# 🚀 Quick Reference Card - RFID System

## Hardware Wiring (MFRC522 → Arduino Uno)

```
SDA  → Pin 10    SCK  → Pin 13
MOSI → Pin 11    MISO → Pin 12
RST  → Pin 9     GND  → GND
3.3V → 3.3V      LED  → Pin 8 (optional)
```

**⚠️ WARNING: Use 3.3V NOT 5V!**

---

## Serial Commands

| Command | Example | Response | Description |
|---------|---------|----------|-------------|
| `READ` | `READ\n` | `UID:04A1B2C3D4\n` | Read card UID |
| `WRITE` | `WRITE:100.50\n` | `OK:WROTE:04A1B2:100.50\n` | Write amount to card |
| `PING` | `PING\n` | `PONG\n` | Test connection |
| `RESET` | `RESET\n` | `OK:RESET\n` | Reset MFRC522 |

**Baud Rate**: 115200  
**Timeout**: 3 seconds  
**Format**: Text-based, newline terminated

---

## LED Indicators

| Pattern | Meaning |
|---------|---------|
| 3 blinks at startup | System ready |
| Solid ON | Waiting for card |
| 2 quick blinks | Card read success |
| 3 medium blinks | Card write success |
| 5 fast blinks (repeat) | MFRC522 error |

---

## Python Quick Usage

### Connect and Read Card
```python
from rfid_reception.services.serial_comm import SerialCommunicationService

serial = SerialCommunicationService(port='COM3', baudrate=115200)
serial.connect()

# Read card
success, uid = serial.read_card()
print(f"Card: {uid}")
```

### Write to Card
```python
# Write amount
success, uid, msg = serial.write_card(100.50)
print(f"Written: {uid} → ${msg}")
```

### Save to Database
```python
from rfid_reception.services.db_service import DatabaseService

db = DatabaseService()
balance, txn_id = db.top_up(
    card_uid=uid,
    amount=100.50,
    employee="John Doe"
)
print(f"New balance: ${balance}")
```

---

## Common Errors

| Error Message | Fix |
|--------------|-----|
| `MFRC522 not found` | Check wiring, verify 3.3V |
| `No card detected` | Place card closer (<3cm) |
| `Failed to write` | Try different card |
| `Port already in use` | Close Serial Monitor |
| `Permission denied` | Run as admin / check port |

---

## Port Configuration

### Windows
- Check: Device Manager → Ports (COM & LPT)
- Format: `COM3`, `COM4`, etc.

### Linux
- Check: `ls /dev/ttyUSB* /dev/ttyACM*`
- Format: `/dev/ttyUSB0`, `/dev/ttyACM0`
- Permissions: `sudo usermod -a -G dialout $USER`

### macOS
- Check: `ls /dev/tty.*`
- Format: `/dev/tty.usbserial-XXXX`

---

## Database Schema

### Cards Table
- `id` (Primary Key)
- `card_uid` (Unique)
- `balance` (Float)
- `created_at` (DateTime)
- `last_topped_at` (DateTime)

### Transactions Table
- `id` (Primary Key)
- `card_uid` (Foreign Key)
- `type` (read/topup)
- `amount` (Float)
- `balance_after` (Float)
- `employee` (String)
- `timestamp` (DateTime)
- `notes` (String)

---

## File Locations

```
rfid-reception-system/
├── arduino_example/
│   ├── rfid_reader_example.ino    ← Upload this
│   ├── README.md                   ← Full docs
│   ├── SETUP_GUIDE.md             ← Setup instructions
│   ├── QUICK_REFERENCE.md         ← This file
│   └── python_integration_example.py
├── rfid_reception/
│   ├── services/
│   │   ├── serial_comm.py         ← Arduino communication
│   │   └── db_service.py          ← Database operations
│   └── app.py                     ← Main GUI application
└── rfid_reception.db              ← SQLite database
```

---

## Testing Checklist

- [ ] Arduino powers on (LED lights)
- [ ] Upload sketch succeeds
- [ ] Serial Monitor shows "RFID Reader Ready"
- [ ] LED blinks 3 times
- [ ] `PING` command works
- [ ] Can read card UID
- [ ] Can write to card
- [ ] Python connects successfully
- [ ] Database saves transactions

---

## Support Card Types

✅ **Supported**
- MIFARE Classic 1K (most common)
- MIFARE Classic 4K
- MIFARE Ultralight (read-only)

❌ **Not Supported**
- MIFARE DESFire (different crypto)
- EM4100 (125 kHz frequency)
- HID cards (different protocol)

---

## Pinout Reference

### Arduino Uno
```
        ┌─────────────┐
    RST─┤1          28├─A5
     RX─┤2          27├─A4
     TX─┤3          26├─A3
        ┤            ├
  LED 8─┤8          19├
 RST  9─┤9          18├
 SS  10─┤10         17├
MOSI 11─┤11         16├
MISO 12─┤12         15├
 SCK 13─┤13         14├
        └─────┬─┬────┘
            3.3V GND
```

---

## Emergency Commands

### Reset Everything
```bash
# Arduino: Press physical reset button
# Python: Ctrl+C to stop, restart script
# Database: Backup first, then delete .db file
```

### Clear Serial Buffer
```python
serial_service.connection.reset_input_buffer()
serial_service.connection.reset_output_buffer()
```

### Re-initialize MFRC522
Send `RESET` command or power cycle Arduino

---

## Performance Specs

- **Read Time**: ~500ms
- **Write Time**: ~1000ms
- **Max Distance**: 3-5cm
- **Card Capacity**: Sector 1, Block 4 (16 bytes)
- **Concurrent Cards**: 1 at a time
- **Serial Baud**: 115200 bps

---

**Last Updated**: October 2025  
**Version**: 1.0  
**Compatibility**: Arduino Uno/Nano/Mega + MFRC522
