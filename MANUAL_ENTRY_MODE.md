# Manual Entry Mode Feature Documentation

## Overview

The Manual Entry Mode is a fallback feature that allows receptionists to process card top-up transactions without requiring an Arduino connection. This is particularly useful when:

- Arduino is not connected or unavailable
- The RFID reader is malfunctioning
- Processing corrections or manual adjustments
- Working offline without hardware

## How It Works

### Enabling Manual Entry Mode

1. Open the RFID Reception System application
2. In the main window, locate the "Manual Entry Mode" section
3. Check the "Use Manual Entry" checkbox

When enabled:
- The "Read Card" button becomes disabled
- A card UID entry field becomes active
- The "Load Card" button becomes active

### Using Manual Entry Mode

#### Step 1: Enter Card UID
In the Manual Entry Mode section, enter the card UID in the text field. The UID can be:
- Alphanumeric characters (A-Z, 0-9)
- Hyphens (-) for separation
- Underscores (_) for separation

Examples of valid UIDs:
- `CARD-123-456`
- `USER_789_ABC`
- `RFID12345678`
- `TEST-CARD-001`

#### Step 2: Load Card
Click the "Load Card" button to:
- Validate the entered UID format
- Check if the card exists in the database
- Display the current balance
- Load the card for top-up operations

If the card doesn't exist in the database, it will be automatically created with a zero balance.

#### Step 3: Perform Top-Up
Once the card is loaded:
1. Enter the top-up amount or use quick amount buttons (10, 20, 50, 100 EGP)
2. Click the "Top-Up" button
3. A confirmation dialog will show:
   - Card UID
   - Amount to be added
   - Current mode (Manual Mode)
4. Confirm the transaction
5. The transaction is saved to the database with a "Manual entry mode" note

### Key Differences from Arduino Mode

| Feature | Arduino Mode | Manual Entry Mode |
|---------|-------------|-------------------|
| Card Detection | Automatic via RFID reader | Manual UID entry |
| Physical Card Write | Yes - card is updated | No - database only |
| Arduino Required | Yes | No |
| Transaction Notes | None or custom | "Manual entry mode" |
| Typical Use Case | Standard operations | Fallback/corrections |

## Transaction Tracking

All manual mode transactions are marked in the database with:
- **Type**: `topup`
- **Notes**: `Manual entry mode`
- **Employee**: Current configured employee name
- **Timestamp**: Date and time of transaction
- **Card UID**: As entered by the user
- **Amount**: Top-up amount
- **Balance After**: New balance after top-up

This allows you to:
- Distinguish manual transactions from Arduino transactions in reports
- Track which transactions were processed without hardware
- Audit manual entries for compliance or review

## Validation

### UID Validation Rules
- Must not be empty
- Must contain only alphanumeric characters, hyphens, and underscores
- Special validation: `uid.replace('-', '').replace('_', '').isalnum()`

Invalid UIDs will show an error message: "Invalid UID format. Use alphanumeric characters only."

### Amount Validation
- Must be a valid number
- Must be greater than 0
- Same validation as Arduino mode

## Use Cases

### 1. Arduino Malfunction
**Scenario**: Arduino stops responding during business hours
**Solution**: Enable manual mode and continue processing transactions using card UIDs from customer cards (printed or recorded)

### 2. Offline Corrections
**Scenario**: A transaction was processed incorrectly and needs adjustment
**Solution**: Use manual mode to add or adjust balance for specific card UID

### 3. Remote Transactions
**Scenario**: Process a top-up for a customer who is calling in
**Solution**: Get card UID from customer, use manual mode to process transaction

### 4. Testing and Development
**Scenario**: Testing the system without Arduino hardware
**Solution**: Use manual mode to simulate transactions for testing

### 5. Backup Reception Station
**Scenario**: Setting up a backup reception station without RFID reader
**Solution**: Use manual mode as primary input method

## Switching Between Modes

You can switch between modes at any time:

### From Arduino to Manual Mode:
1. Check "Use Manual Entry" checkbox
2. Read Card button is disabled
3. Manual entry fields are enabled
4. Any currently loaded card remains loaded

### From Manual to Arduino Mode:
1. Uncheck "Use Manual Entry" checkbox
2. Manual entry fields are disabled
3. Read Card button is enabled
4. Any currently loaded card remains loaded

**Note**: You can have the same card loaded in either mode and top it up. The system tracks which mode was used for each transaction.

## Reports and Analytics

Manual mode transactions appear in all standard reports:
- Daily reports
- Weekly reports
- Monthly reports
- Transaction history view

You can identify manual transactions by:
- Checking the "Notes" column for "Manual entry mode"
- Filtering transactions in the database query
- Using report analysis tools

## Security Considerations

### Best Practices:
1. **Verification**: Always verify card UID before processing manual transactions
2. **Documentation**: Keep records of why manual mode was used
3. **Employee Tracking**: System automatically records which employee processed each transaction
4. **Audit Trail**: All manual transactions are permanently logged in the database

### Risks to Be Aware Of:
- Manual entry could lead to typos in card UIDs
- No physical card verification in manual mode
- Requires trust that the correct UID is being entered

### Recommended Controls:
1. Train staff on proper UID entry
2. Implement double-check procedures for manual entries
3. Regular reconciliation of manual vs. Arduino transactions
4. Review manual transaction logs periodically

## Troubleshooting

### Issue: "Invalid UID format" error
**Solution**: Ensure UID contains only letters, numbers, hyphens, and underscores

### Issue: Manual mode is grayed out
**Solution**: This shouldn't happen. Check that you have the latest version of the application

### Issue: Card balance doesn't match
**Solution**: 
1. Check transaction history for the card
2. Verify all transactions were processed correctly
3. Sum up all transactions to verify total

### Issue: Can't switch back to Arduino mode
**Solution**: 
1. Uncheck "Use Manual Entry" checkbox
2. Ensure Arduino is properly connected
3. Test connection in Settings

## Technical Details

### Database Schema
Manual mode uses the same database tables as Arduino mode:

**Cards Table**: Stores card information
- `card_uid`: The entered UID
- `balance`: Current balance
- `last_topped_at`: Last transaction timestamp

**Transactions Table**: Stores all transactions
- `card_uid`: Foreign key to cards
- `type`: 'topup'
- `amount`: Transaction amount
- `notes`: 'Manual entry mode' for manual transactions
- `employee`: Employee who processed it
- `timestamp`: When it occurred

### Code Implementation
The manual mode is implemented in `rfid_reception/gui/main_window.py`:

- `_toggle_manual_mode()`: Switches between modes
- `_load_manual_card()`: Loads card from manual UID entry
- `_top_up()`: Processes top-up in either mode

Key logic:
```python
if self.manual_mode:
    # Skip Arduino write, only update database
    new_balance, transaction_id = self.db_service.top_up(
        self.current_card_uid, 
        amount,
        employee=self.config.get('employee_name'),
        notes='Manual entry mode'
    )
else:
    # Arduino mode: write to card and update database
    success, uid, message = self.serial_service.write_card(amount)
    # ... then update database
```

## Testing

The feature includes comprehensive test coverage:

- `test_manual_mode.py`: Unit tests for manual mode operations
- `test_manual_mode_integration.py`: Integration tests for complete workflows

Run tests with:
```bash
python -m pytest rfid_reception/tests/test_manual_mode*.py -v
```

## Future Enhancements

Potential improvements for future versions:
1. Barcode scanner support for quick UID entry
2. Card UID history/autocomplete from recent transactions
3. Batch manual entry mode for multiple transactions
4. Export/import of manual transaction batches
5. Enhanced validation with checksum verification
6. Integration with external card management systems

## Support

For questions or issues with manual entry mode:
1. Check this documentation first
2. Review the logs in `logs/rfid_reception.log`
3. Test with a known card UID in a safe environment
4. Contact system administrator or developer
