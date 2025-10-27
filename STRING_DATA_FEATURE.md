# String Data Storage Feature

## Overview
The RFID card system now supports writing **both numeric and text data** to cards:
- **Numeric input** (e.g., `50`) → Updates database balance + writes to card
- **String input** (e.g., `Ahmed`) → Only writes to card (no database update)

## How It Works

### Input Field Behavior
The amount input field in the main window now accepts:
1. **Numbers** - Treated as balance amounts
2. **Text** - Treated as custom string data (max 11 characters)

### Arduino Card Storage
Cards store string data in block 4:
```cpp
struct CardData {
  char text[12];      // Up to 11 chars + null terminator
  uint32_t checksum;  // Data validation
};
```

## Usage Examples

### Writing Numeric Balance
1. Read or load a card
2. Enter: `50`
3. Click "Add to Balance"
4. **Result**: 
   - Database balance increased by 50 EGP
   - Card stores "50" as text

### Writing Custom Text
1. Read or load a card  
2. Enter: `Ahmed`
3. Click "Add to Balance"
4. **Result**:
   - Database balance unchanged
   - Card stores "Ahmed" as text
   - Note: Only works in Arduino mode (not Manual mode)

### Valid String Examples
- Names: `Ahmed`, `Mohamed`, `Sarah`
- IDs: `EMP001`, `Card123`
- Codes: `VIP`, `GOLD`, `A1B2C3`
- Numbers as text: `50`, `100.5`

### Restrictions
- **Maximum length**: 11 characters
- **Supported characters**: Letters, numbers, spaces, basic punctuation
- **Case sensitive**: `Ahmed` ≠ `AHMED`

## Technical Details

### Modified Files

**1. arduino_example/rfid_reader_example.ino**
- Changed `CardData` struct to store char array
- Updated `writeCardData()` to handle strings
- Modified `readCardData()` to return strings
- New checksum algorithm for text validation

**2. rfid_reception/gui/main_window.py**
- Input field now labeled "Top-Up Amount / Write Data"
- Added string detection logic in `_top_up()`
- New method `_arduino_write_string()` for string-only writes
- Numeric inputs still update database
- String inputs only write to card

**3. rfid_reception/services/serial_comm.py**
- Updated `write_card()` to accept any data type
- Command format: `WRITE:data\n`

### Arduino Protocol

**Write Command**
```
WRITE:<data>\n
```
- `<data>`: Any string up to 11 characters

**Examples:**
- `WRITE:50\n` → Writes "50" to card
- `WRITE:Ahmed\n` → Writes "Ahmed" to card
- `WRITE:VIP_123\n` → Writes "VIP_123" to card

**Response:**
```
OK:WROTE:<uid>:<data>\n
```
or
```
ERROR:<message>\n
```

### Modes of Operation

#### Arduino Mode (Default)
- **Numeric input**: Updates database + writes to card
- **String input**: Only writes to card
- Full card read/write functionality

#### Manual Mode
- **Numeric input**: Only updates database (card not written)
- **String input**: Not supported (shows info message)
- Database-only operations

## Data Validation

### Arduino Side
- Maximum 11 characters enforced
- Checksum validation on read
- Returns "INVALID" if checksum fails

### Python Side  
- Length check before sending to Arduino
- Clear error messages for invalid input
- Confirmation dialogs distinguish numeric vs string

## Use Cases

### 1. Employee ID Cards
```
Enter: EMP12345
Result: Card stores employee ID
```

### 2. Access Level Cards
```
Enter: ADMIN
Result: Card stores access level
```

### 3. Membership Cards
```
Enter: GOLD
Result: Card stores membership tier
```

### 4. Balance Cards
```
Enter: 100
Result: Database balance +100, card stores "100"
```

## Important Notes

1. **String writes don't update database**
   - Only physical card data changes
   - Balance remains unchanged
   - No transaction record created

2. **Numeric writes update both**
   - Database balance increased
   - Transaction logged
   - Card stores the amount as text

3. **Case sensitivity**
   - "Ahmed" and "AHMED" are different
   - Card stores exact text entered

4. **Character limit**
   - Hard limit of 11 characters
   - Enforced before sending to Arduino
   - Error shown if exceeded

5. **Manual mode limitation**
   - Strings only work in Arduino mode
   - Manual mode is database-only

## Testing Checklist

- [ ] Write numeric value (e.g., "50") → Updates balance and card
- [ ] Write string value (e.g., "Ahmed") → Only updates card
- [ ] Try string longer than 11 chars → Shows error
- [ ] Write empty string → Shows error
- [ ] Manual mode with string → Shows info message
- [ ] Arduino mode with string → Writes to card successfully
- [ ] Read card with string data → Verify data persists
- [ ] Checksum validation → Invalid data detected

## Examples

### Example 1: Student Card
```
Input: STUDENT01
Action: Write to card only
Result: Card contains "STUDENT01"
```

### Example 2: Balance Top-up
```
Input: 75.50
Action: Add to balance + write to card
Result: Balance +75.50, Card contains "75.50"
```

### Example 3: VIP Status
```
Input: VIP
Action: Write to card only  
Result: Card contains "VIP", balance unchanged
```

## Troubleshooting

**Problem**: String not writing to card
- **Solution**: Ensure Arduino mode is enabled (not Manual mode)

**Problem**: "Data too long" error
- **Solution**: Keep text to 11 characters or less

**Problem**: Card returns "INVALID" when reading
- **Solution**: Checksum failed, rewrite the card

**Problem**: Database balance not updating with text
- **Solution**: This is expected behavior - strings don't modify balance

## Future Enhancements

Potential improvements:
- Support longer strings (multi-block storage)
- Binary data support
- Multiple data fields per card
- String-based balance lookups
- Card data history/audit trail
