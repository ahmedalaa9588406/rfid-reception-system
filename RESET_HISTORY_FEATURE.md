# 🗑️ Reset Card History Feature

## Overview
Added a new feature to reset/clear the game history stored on RFID cards. This allows you to delete all game entries from the card's history blocks (9-15).

## What's New

### 1. **Reset History Button**
- Added "🗑️ مسح السجل" (Reset History) button in the Card History Dialog
- Located on the right side of the button panel
- Bright red color (#FF6B6B) to indicate it's a destructive action

### 2. **New Serial Command**
- Added `clear_history()` method to `SerialCommunicationService`
- Sends `CLEAR_HISTORY` command to Arduino
- Arduino must respond with `OK:HISTORY_CLEARED:<uid>` or `ERROR:<message>`

### 3. **Safety Features**
- **Confirmation Dialog**: User must confirm before resetting
- **Warning Message**: Clear warning that action cannot be undone
- **Arduino Connection Check**: Verifies connection before attempting reset
- **Visual Feedback**: Status updates during the process

## How to Use

### From the GUI
1. Open the Card History dialog (from main window: "📜 سجل البطاقات")
2. Place the RFID card on the reader
3. Click "🗑️ مسح السجل" (Reset History) button
4. Read the warning message carefully
5. Click "Yes" to confirm or "No" to cancel
6. Wait for the operation to complete
7. Card history will be cleared and display updated

### Confirmation Dialog
```
⚠️ تحذير!

هل أنت متأكد من أنك تريد مسح سجل الألعاب بالكامل من البطاقة؟

هذا الإجراء لا يمكن التراجع عنه!
سيتم مسح جميع البيانات المحفوظة في الكتل 9-15.
```

## Technical Details

### Python Implementation

#### New Method in `serial_comm.py`
```python
def clear_history(self, retries=3) -> Tuple[bool, str]:
    """
    Request Arduino to clear/reset game history from card blocks 9-15.
    
    Returns:
        Tuple[bool, str]: (success, uid_or_error_message)
    """
```

#### New Method in `card_history_dialog.py`
```python
def _reset_history(self):
    """Reset/clear all game history from card blocks 9-15."""
```

### Communication Protocol

**Command**: `CLEAR_HISTORY\n`

**Expected Responses**:
- Success: `OK:HISTORY_CLEARED:<card_uid>`
- Error: `ERROR:<error_message>`
- Status: `STATUS:<informational_message>` (optional)

**Timeout**: 10 seconds

### Arduino Implementation Required

**IMPORTANT**: You must update your Arduino code to handle the `CLEAR_HISTORY` command!

Add this code to your Arduino sketch:

```cpp
void clearHistory() {
  // Check for card presence
  if (!rfid.PICC_IsNewCardPresent() || !rfid.PICC_ReadCardSerial()) {
    Serial.println("ERROR:No card detected");
    return;
  }
  
  // Get UID
  String uid = "";
  for (byte i = 0; i < rfid.uid.size; i++) {
    if (rfid.uid.uidByte[i] < 0x10) uid += "0";
    uid += String(rfid.uid.uidByte[i], HEX);
  }
  uid.toUpperCase();
  
  // Clear blocks 9-15 (history blocks)
  byte emptyBlock[16] = {0};  // All zeros
  bool allSuccess = true;
  
  for (byte block = 9; block <= 15; block++) {
    // Authenticate
    MFRC522::StatusCode status = rfid.PCD_Authenticate(
      MFRC522::PICC_CMD_MF_AUTH_KEY_A, 
      block, 
      &key, 
      &(rfid.uid)
    );
    
    if (status != MFRC522::STATUS_OK) {
      Serial.print("ERROR:Auth failed for block ");
      Serial.println(block);
      rfid.PICC_HaltA();
      rfid.PCD_StopCrypto1();
      return;
    }
    
    // Write empty data
    status = rfid.MIFARE_Write(block, emptyBlock, 16);
    if (status != MFRC522::STATUS_OK) {
      allSuccess = false;
      break;
    }
  }
  
  rfid.PICC_HaltA();
  rfid.PCD_StopCrypto1();
  
  if (allSuccess) {
    Serial.print("OK:HISTORY_CLEARED:");
    Serial.println(uid);
  } else {
    Serial.println("ERROR:Failed to clear some blocks");
  }
}

// In your main loop's command handler:
void loop() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    
    if (command == "CLEAR_HISTORY") {
      clearHistory();
    }
    // ... other commands ...
  }
}
```

## Files Modified

### 1. `rfid_reception/services/serial_comm.py`
- Added `clear_history()` method
- Handles communication with Arduino for clearing history

### 2. `rfid_reception/gui/dialogs/card_history_dialog.py`
- Added "🗑️ مسح السجل" button
- Added `_reset_history()` method
- Includes confirmation dialog and error handling

## User Interface

### Button Layout
```
[✖ إغلاق]  [🔄 تحديث السجل]        [🗑️ مسح السجل]
   Left        Left                     Right
```

### Status Messages

**During Reset**:
```
⏳ جاري مسح سجل البطاقة... يرجى إبقاء البطاقة على القارئ...
```

**Success**:
```
✓ تم مسح سجل البطاقة بنجاح! جميع بيانات الألعاب تم حذفها.
```

**Error**:
```
❌ فشل في مسح السجل: <error_message>
```

## Testing Checklist

- [ ] Arduino updated with CLEAR_HISTORY command handler
- [ ] Button appears in Card History Dialog
- [ ] Confirmation dialog shows before reset
- [ ] Can cancel reset operation
- [ ] Arduino connection is checked before reset
- [ ] Status updates during reset process
- [ ] Success message shows after reset
- [ ] Treeview clears after successful reset
- [ ] Error handling works correctly
- [ ] Card UID displayed after reset

## Logging

All reset operations are logged:

```python
# Success
logger.info(f"Card history cleared successfully: {uid}")

# Cancelled
logger.info("History reset cancelled by user")

# Error
logger.error(f"Failed to clear history: {error_message}")
```

Check logs at: `logs/rfid_reception.log`

## Safety Considerations

1. **Non-Reversible**: Once history is cleared, it cannot be recovered
2. **Confirmation Required**: User must explicitly confirm the action
3. **Warning Message**: Clear warning about consequences
4. **Visual Cues**: Red button color indicates danger
5. **No Auto-Execute**: Always requires manual user action

## Common Issues

### Issue 1: Arduino Doesn't Respond
**Problem**: Timeout waiting for Arduino response
**Solution**: 
- Verify Arduino is connected
- Check Arduino code includes CLEAR_HISTORY handler
- Ensure card is on reader during operation

### Issue 2: Authentication Failed
**Problem**: Arduino reports authentication failure
**Solution**:
- Check RFID card type (must be MIFARE Classic)
- Verify correct key is being used
- Ensure card is properly positioned on reader

### Issue 3: Partial Clear
**Problem**: Some blocks cleared, others failed
**Solution**:
- Keep card stable on reader throughout operation
- Check card isn't damaged
- Try again with better card positioning

## Future Enhancements

Potential improvements:
- [ ] Option to clear specific blocks instead of all
- [ ] Backup history before clearing
- [ ] Clear history for multiple cards in batch
- [ ] Schedule automatic history clearing
- [ ] Export history before clearing

---

**Version**: 1.0
**Date**: November 2025
**Feature**: Reset Card History
