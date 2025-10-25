# RFID Reception System - Employee Guide

## Overview
This guide explains how to use the RFID Reception System to read and write RFID cards, manage balances, and print receipts.

---

## Main Features

### 1. **Read RFID Card**
**Purpose**: Read card UID and current balance from an RFID card.

**Steps**:
1. Click the **"🔍 Read Card"** button
2. Place the RFID card near the reader
3. Wait for confirmation message showing:
   - Card UID
   - Current Balance
4. The card information will be displayed on screen

**Notes**:
- New cards are automatically created with 0.00 EGP balance
- Card read events are logged for audit purposes

---

### 2. **Add Balance (Top-Up)**
**Purpose**: Add money to a card's existing balance.

**Steps**:
1. Read or load a card first (see above)
2. Enter the amount to add in the **"💰 Top-Up Amount"** field
3. Or use **Quick Amount** buttons (10, 20, 50, 100 EGP)
4. Click **"✓ Add to Balance"** button
5. Confirm the transaction
6. Receipt will be automatically printed/saved

**Example**:
- Current Balance: 50.00 EGP
- Add Amount: 20.00 EGP
- New Balance: 70.00 EGP

---

### 3. **Set Balance (Write Balance)**
**Purpose**: Set the card balance to a specific amount (not add, but replace).

**Steps**:
1. Read or load a card first
2. Enter the desired final balance in the amount field
3. Click **"✍ Set Balance"** button
4. Review the change summary:
   - Shows if it will ADD or DEDUCT money
   - Shows current and new balance
5. Confirm the operation
6. Receipt will be automatically printed/saved

**Example 1 - Increase**:
- Current Balance: 30.00 EGP
- Set Balance To: 100.00 EGP
- Result: ADDS 70.00 EGP

**Example 2 - Decrease**:
- Current Balance: 100.00 EGP
- Set Balance To: 50.00 EGP
- Result: DEDUCTS 50.00 EGP

---

### 4. **Manual Mode**
**Purpose**: Work without Arduino hardware for testing or backup.

**Steps**:
1. Check **"Enable Manual Card Entry"** checkbox
2. Enter card UID manually in the text field
3. Click **"Load Card UID"** button
4. Proceed with top-up or balance write operations

**Important Notes**:
- ⚠️ Manual mode does NOT write to physical cards
- Only updates the database
- Useful for:
  - Testing the system
  - Data entry without hardware
  - Backup operations

---

### 5. **Receipt Printing**

**Automatic Printing**:
- Receipts are automatically generated after every transaction
- Saved as PDF in the `receipts/` folder
- Can be printed directly to a printer (Windows only)

**Print Last Receipt**:
1. Click **"🖨️ Print Last Receipt"** in Quick Actions
2. Receipt PDF will be saved
3. Option to open/view the PDF

**Print Card Summary**:
1. Load a card first
2. Click **"📄 Print Card Summary"**
3. Generates detailed report with:
   - Card information
   - Current balance
   - Transaction history
4. Saved as PDF

**Receipt Contents**:
- Transaction ID
- Date and Time
- Card UID
- Amount (Added/Deducted)
- New Balance
- Employee Name
- Company Information

---

## Quick Actions Panel

### 🎫 View All Cards
Shows a list of all cards in the system with their balances.

### 📅 Daily Report
Generate transaction report for a specific day.

### 🗓 Weekly Report
Generate weekly transaction summary.

### 📆 Monthly Report
Generate monthly transaction summary.

### 📈 Yearly Report
Generate yearly transaction summary.

---

## Connection Status

**Top Right Indicator**:
- **● Connected (COM3)**: Arduino is connected and ready
- **● Disconnected**: No Arduino connection (use Manual Mode)

---

## Troubleshooting

### Card Not Reading
1. Check connection status indicator
2. Ensure Arduino is properly connected
3. Try reading the card again
4. Use Manual Mode as fallback

### Receipt Not Printing
1. Check if printer is set as default (Windows)
2. Receipts are always saved as PDF in `receipts/` folder
3. Open PDF manually and print

### Balance Incorrect
1. Use **"🎫 View All Cards"** to verify balance in database
2. Use **"✍ Set Balance"** to correct the amount
3. Check transaction history for discrepancies

### Manual Mode Issues
1. Ensure card UID is correct format
2. Card will be created if it doesn't exist
3. Remember: Manual mode doesn't update physical cards

---

## Best Practices

1. **Always read the card first** before any operation
2. **Verify the balance** shown on screen before proceeding
3. **Keep receipts** for record-keeping
4. **Use Manual Mode** only when Arduino is unavailable
5. **Print card summaries** periodically for audit purposes
6. **Check transaction history** regularly in the reports

---

## Important Notes

⚠️ **Physical Card vs Database**:
- **Arduino Mode**: Updates both physical card AND database
- **Manual Mode**: Updates ONLY database (not physical card)

✅ **Receipt Storage**:
- All receipts are saved in the `receipts/` folder
- Named with transaction ID and timestamp
- Can be reprinted anytime

📊 **Audit Trail**:
- All card reads are logged
- All transactions are recorded
- Transaction history available in reports

---

## Support

For technical issues or questions, contact the system administrator.

---

**Last Updated**: 2025
**Version**: 2.0
