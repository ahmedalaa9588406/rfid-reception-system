# K-Balance Feature Implementation

## Overview
This document describes the dual-balance system that allows storing two separate balance types on RFID cards:
- **Regular Balance**: Standard balance (e.g., entering "50")
- **K-Balance**: K-prefixed balance (e.g., entering "K50")

## How It Works

### User Input
When adding balance in the main window, you can now enter:
- **50** → Adds to Regular Balance
- **K50** → Adds to K-Balance

### Database Changes
Added `k_balance` column to the Card model:
```python
class Card(Base):
    balance = Column(Float, default=0.0)      # Regular balance
    k_balance = Column(Float, default=0.0)    # K-prefixed balance
```

### Arduino Card Storage
The RFID card now stores BOTH balances in block 4:
```cpp
struct CardData {
  float regular_balance;    // Regular balance
  float k_balance;          // K-prefixed balance  
  uint32_t checksum;        // Data integrity
};
```

## Usage Examples

### Adding Regular Balance
1. Read or load a card
2. Enter amount: `50`
3. Click "Add to Balance"
4. **Result**: 50 EGP added to Regular Balance

### Adding K-Balance
1. Read or load a card
2. Enter amount: `K50`
3. Click "Add to Balance"
4. **Result**: 50 EGP added to K-Balance

### Viewing Both Balances
- **Main Window**: Shows two separate balance displays
  - 💵 Regular Balance
  - 🔹 K Balance
- **View All Cards Dialog**: Shows both columns
  - Balance
  - K Balance

## Technical Details

### Modified Files

1. **rfid_reception/models/schema.py**
   - Added `k_balance` column to Card model

2. **rfid_reception/services/db_service.py**
   - Updated `top_up()` with `is_k_balance` parameter
   - Modified `create_or_get_card()` to return k_balance
   - Updated `get_all_cards()` to include k_balance

3. **rfid_reception/gui/main_window.py**
   - Added `_parse_amount_input()` to detect K-prefix
   - Updated balance display to show both balances
   - Modified `_top_up()` to route to correct balance
   - Updated `_manual_top_up()` and `_arduino_top_up()`
   - Added `current_k_balance` tracking

4. **rfid_reception/services/serial_comm.py**
   - Updated `write_card()` with `is_k_balance` parameter
   - Sends balance type to Arduino (0=regular, 1=k_balance)

5. **arduino_example/rfid_reader_example.ino**
   - Modified CardData structure for dual balance
   - Updated `handleWrite()` to accept balance type
   - Modified `writeCardData()` to preserve existing balances
   - Updated `readCardData()` to return both balances
   - Changed checksum calculation for dual values

6. **rfid_reception/gui/dialogs/view_all_cards_dialog.py**
   - Added "K Balance" column to table
   - Updated statistics to show total K-Balance
   - Modified status logic to consider both balances

## Arduino Protocol

### Write Command
```
WRITE:amount:type\n
```
- `amount`: Float value to write
- `type`: 0 = regular balance, 1 = K-balance

**Examples:**
- `WRITE:50.00:0\n` → Write 50 to regular balance
- `WRITE:50.00:1\n` → Write 50 to K-balance

### Response
```
OK:WROTE:uid:amount:type\n
```

## Database Migration

If you have existing cards, the system will automatically:
1. Initialize `k_balance` to 0.0 for existing cards
2. Preserve existing `balance` values
3. Run the migration when you first start the updated application

## Notes

- Both balances are independent
- Writing to one balance preserves the other
- Cards without data will return 0.0 for both balances
- The system is backward compatible with existing cards
- Transaction types: `topup` (regular) and `k_topup` (K-balance)

## Testing Checklist

- [ ] Enter regular amount (e.g., "50") and verify it updates Regular Balance
- [ ] Enter K-prefixed amount (e.g., "K50") and verify it updates K-Balance
- [ ] Read a card and verify both balances are displayed
- [ ] Write to Arduino and verify card stores both balances correctly
- [ ] View All Cards dialog shows both balance columns
- [ ] Statistics show total for both balance types
- [ ] Manual mode works for both balance types
- [ ] Receipt printing includes correct balance type in notes

## Support

If you encounter issues:
1. Check Arduino serial monitor for error messages
2. Verify card authentication is successful
3. Ensure database has been migrated (k_balance column exists)
4. Test with manual mode first before using Arduino

## Future Enhancements

Potential improvements:
- Separate transaction history for each balance type
- Balance transfer between regular and K-balance
- Different color coding for K-balance transactions
- Export reports with balance type breakdown
