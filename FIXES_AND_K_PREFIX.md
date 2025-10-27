# Card Detection Fixes & K-Prefix Feature

## Issues Fixed

### 1. Card Detection Problems ✅
**Problem**: "No card detected" errors during read/write operations

**Solution**:
- Added soft reset (`mfrc522.PCD_Init()`) before each operation
- Increased timeouts (5s for read, 10s for write)
- Implemented multiple quick check loops (3 attempts per cycle)
- Added proper delay intervals between attempts
- Arduino now sends STATUS messages during waiting

**Changes**:
- `handleRead()`: Better timing, multiple attempts
- `handleWrite()`: Extended timeout, status updates
- Python serial service: Handles STATUS messages properly

### 2. K-Prefix Support ✅
**Feature**: Both buttons now support K-prefixed amounts (e.g., K50)

## Input Format Support

The input field now accepts **three formats**:

### 1. Regular Number
```
Input: 50
Result: 
- Database balance +50 EGP
- Card stores "50"
```

### 2. K-Prefixed Amount
```
Input: K50
Result:
- Database balance +50 EGP  
- Card stores "K50"
- Special indicator in transaction notes
```

### 3. Text String
```
Input: Ahmed
Result:
- Database balance unchanged
- Card stores "Ahmed"
- Only works with "Add to Balance" button
```

## Button Behavior

### ✓ Add to Balance Button
**Accepts**: Numbers, K-amounts, Text strings

| Input | Balance Update | Card Data | Notes |
|-------|---------------|-----------|-------|
| `50` | +50 EGP | "50" | Regular top-up |
| `K50` | +50 EGP | "K50" | K-amount top-up |
| `Ahmed` | None | "Ahmed" | String only (Arduino mode) |

### ✍ Set Balance Button
**Accepts**: Numbers, K-amounts only (NO text strings)

| Input | Balance Update | Card Data | Notes |
|-------|---------------|-----------|-------|
| `50` | Set to 50 EGP | "50" | Regular set |
| `K50` | Set to 50 EGP | "K50" | K-amount set |
| `Ahmed` | ❌ ERROR | N/A | Not allowed |

## Usage Examples

### Example 1: Regular Top-Up
```
1. Read card
2. Enter: 50
3. Click "Add to Balance"
Result: Balance +50, Card stores "50"
```

### Example 2: K-Amount Top-Up
```
1. Read card
2. Enter: K50
3. Click "Add to Balance"
Result: Balance +50, Card stores "K50"
Confirmation shows: "Add 50.00 EGP (K-Amount)"
```

### Example 3: Set Balance with K-Amount
```
1. Read card (current balance: 25 EGP)
2. Enter: K100
3. Click "Set Balance"
Result: Balance set to 100 (added 75), Card stores "K100"
```

### Example 4: Write Text String
```
1. Read card
2. Enter: VIP
3. Click "Add to Balance"
Result: Balance unchanged, Card stores "VIP"
Note: Arduino mode only
```

## Input Parsing Logic

The system automatically detects input type:

```python
def _parse_input(input_value):
    # Check for K-prefix
    if starts with 'K':
        return 'k_amount', numeric_value, original_input
    
    # Check for numeric
    if can parse as float:
        return 'numeric', numeric_value, string_value
    
    # Default to string
    return 'string', 0.0, input_value
```

**Examples**:
- `K50` → ('k_amount', 50.0, 'K50')
- `50` → ('numeric', 50.0, '50')
- `50.5` → ('numeric', 50.5, '50.5')
- `Ahmed` → ('string', 0.0, 'AHMED')

## Transaction Notes

The system now includes detailed notes:

**Regular amount**:
```
"Manual entry: 50"
"Arduino write: 50"
```

**K-amount**:
```
"Manual entry: K50"
"Arduino write: K50"
"Balance set to 50.00 (K50) - Arduino write"
```

**String**:
```
(No database transaction - card only)
```

## Confirmation Dialogs

### Regular Amount
```
Add 50.00 EGP to [UID]?
Mode: Arduino
```

### K-Amount
```
Add 50.00 EGP (K-Amount) to [UID]?
Card will store: 'K50'
Mode: Arduino
```

### String
```
Write 'AHMED' to card [UID]?
Mode: Arduino

Note: Balance will NOT be updated in database.
```

## UI Updates

### Input Field Label
```
💰 Top-Up Amount / Write Data
```

### Instruction Text
```
Enter: 50 (number) | K50 (K-amount) | Ahmed (text) - Max 11 chars
```

### Status Messages
```
✓ Successfully wrote 'K50' to card!
⏳ Writing 'K50' to card... Keep card on reader!
❌ Write failed: No card detected
```

## Arduino Improvements

### Better Card Detection
```cpp
// Soft reset before operation
mfrc522.PCD_Init();
delay(100);

// Multiple attempts with proper delays
for (int i = 0; i < 3; i++) {
  if (mfrc522.PICC_IsNewCardPresent()) {
    // Card found!
  }
  delay(20);
}
```

### Status Updates
```cpp
Serial.println("STATUS:Ready to write - place card now...");
Serial.println("STATUS:Still waiting for card...");
Serial.println("STATUS:Card detected, writing...");
```

### Response Format
```
OK:WROTE:<uid>:<data>
ERROR:<message>
STATUS:<info>
```

## Technical Details

### Modified Files

**1. arduino_example/rfid_reader_example.ino**
- Improved `handleRead()` with soft reset and multiple attempts
- Improved `handleWrite()` with extended timeout and status messages
- Better timing and delay management

**2. rfid_reception/gui/main_window.py**
- New `_parse_input()` method to detect input type
- Updated `_top_up()` to handle K-amounts
- Updated `_write_balance()` to support K-amounts
- Modified confirmation dialogs
- Updated status messages

**3. rfid_reception/services/serial_comm.py**
- Updated `write_card()` to handle STATUS messages
- Extended timeout with proper response waiting
- Better error handling

## Testing Checklist

Card Detection:
- [ ] Card reads successfully on first attempt
- [ ] Card reads after multiple attempts
- [ ] Card writes successfully
- [ ] STATUS messages appear during write
- [ ] Error messages clear when no card present

K-Prefix:
- [ ] Enter "K50" → Balance +50, Card stores "K50"
- [ ] Enter "K100.5" → Balance +100.5, Card stores "K100.5"
- [ ] Set Balance with "K50" works correctly
- [ ] Confirmation shows "K-Amount" label
- [ ] Transaction notes include K-prefix

Regular Numbers:
- [ ] Enter "50" → Works as before
- [ ] Enter "100.5" → Works with decimals
- [ ] Both buttons accept regular numbers

Text Strings:
- [ ] "Add to Balance" accepts text
- [ ] "Set Balance" rejects text with error
- [ ] Text strings only work in Arduino mode

## Error Messages

**Input validation**:
- Empty input → "Please enter a value"
- Too long → "Maximum 11 characters allowed"
- Invalid for Set Balance → "Set Balance only accepts numeric values or K-amounts"

**Card errors**:
- No Arduino → "Not connected to Arduino"
- No card → "No card detected after X attempts"
- Write failed → "Write failed - authentication issue"

## Troubleshooting

**Card not detected**:
1. Check Arduino connection (COM port)
2. Verify card is on reader
3. Try uploading Arduino sketch again
4. Check MFRC522 wiring

**K-prefix not working**:
1. Ensure you enter uppercase K or lowercase k
2. Must be followed by a number (K50, not K)
3. Check max 11 characters total

**String write fails**:
1. Only works in Arduino mode
2. "Set Balance" doesn't support strings
3. Use "Add to Balance" for strings

## Migration Notes

**No database migration needed**:
- All data stored as strings on cards
- Database continues using numeric balance
- K-prefix is just a display format
- Backward compatible with existing cards

## Examples Summary

| Input | Add Balance | Set Balance | Card Data | DB Balance |
|-------|------------|-------------|-----------|-----------|
| 50 | ✅ +50 | ✅ Set 50 | "50" | 50 |
| K50 | ✅ +50 | ✅ Set 50 | "K50" | 50 |
| 100.5 | ✅ +100.5 | ✅ Set 100.5 | "100.5" | 100.5 |
| K100.5 | ✅ +100.5 | ✅ Set 100.5 | "K100.5" | 100.5 |
| Ahmed | ✅ String only | ❌ Error | "AHMED" | Unchanged |
| VIP | ✅ String only | ❌ Error | "VIP" | Unchanged |
