# Arduino Example for RFID Reception System

This directory contains a sample Arduino sketch that demonstrates the communication protocol expected by the RFID Reception System.

## Hardware Requirements

- Arduino board (Uno, Mega, Nano, etc.)
- RFID reader module (e.g., MFRC522)
- USB cable for connection to PC

## Protocol

The Python application communicates with Arduino using simple text-based commands over serial:

### Commands

1. **READ** - Request to read card UID
   - Send: `READ\n`
   - Success Response: `UID:<card_uid>\n`
   - Error Response: `ERROR:<message>\n`

2. **WRITE** - Request to write amount to card
   - Send: `WRITE:<amount>\n`
   - Success Response: `OK:WROTE:<uid>:<amount>\n`
   - Error Response: `ERROR:<message>\n`

3. **PING** - Connection test
   - Send: `PING\n`
   - Response: `PONG\n`

## Setup Instructions

1. Open `rfid_reader_example.ino` in Arduino IDE
2. Connect your Arduino to PC
3. Select correct board and port in Arduino IDE
4. Upload the sketch
5. Note the COM port (e.g., COM3)
6. Configure this port in the RFID Reception System settings

## Notes

- The example sketch uses mock data for demonstration
- In production, integrate with your actual RFID reader library
- Common RFID libraries: MFRC522, PN532, RDM6300
- Ensure baud rate matches (default: 115200)

## Customization

To integrate with real RFID hardware:

1. Include your RFID library
2. Initialize reader in `setup()`
3. Implement actual card reading in `handleRead()`
4. Implement actual card writing in `handleWrite()` (if supported)
