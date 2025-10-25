# 🚀 Quick Start Guide - RFID Reception System

## Get Started in 5 Minutes!

---

## 📋 Prerequisites

✓ Python 3.8 or higher installed  
✓ Arduino RFID reader (optional - can use Manual Mode)  
✓ Windows/Linux/Mac OS  

---

## 🔧 Installation

### Step 1: Install Dependencies
```bash
cd rfid-reception-system
pip install -r requirements.txt
```

### Step 2: (Optional) Configure Arduino
If you have Arduino RFID hardware:
1. Upload `arduino_example/rfid_reader.ino` to your Arduino
2. Connect Arduino via USB
3. Note the COM port (e.g., COM3 on Windows)

---

## ▶️ Running the Application

### Option 1: Run Main Application
```bash
python -m rfid_reception.app
```

### Option 2: Run with Python
```bash
python rfid_reception/app.py
```

The GUI will open automatically!

---

## 🎮 First Time Setup

### 1. Configure Connection (If using Arduino)
- Click **Settings** menu
- Select your Arduino COM port
- Set baudrate (default: 115200)
- Click **Save**

### 2. Test the System
- Use **Manual Mode** for testing without hardware
- Check the box: **"Enable Manual Card Entry"**
- Enter a test UID: `TEST_CARD_001`
- Click **"Load Card UID"**

---

## 💳 Basic Operations

### Read a Card
1. Click **"🔍 Read Card"** button
2. Place RFID card near reader
3. View card UID and balance on screen

**Without Arduino**: Use Manual Mode (see above)

---

### Add Money (Top-Up)
1. Read or load a card first
2. Enter amount or click quick button (10, 20, 50, 100)
3. Click **"✓ Add to Balance"**
4. Confirm the transaction
5. Receipt automatically saved in `receipts/` folder

**Example**:
```
Current Balance: 50.00 EGP
Add Amount: 20.00 EGP
Result: 70.00 EGP
```

---

### Set Exact Balance
1. Read or load a card first
2. Enter the desired final balance
3. Click **"✍ Set Balance"**
4. Review the confirmation (shows ADD or DEDUCT)
5. Confirm and receipt is generated

**Example**:
```
Current Balance: 30.00 EGP
Set Balance To: 100.00 EGP
System will: ADD 70.00 EGP
```

---

## 🖨️ Working with Receipts

### Auto-Print
Receipts are automatically generated after every transaction and saved as PDF in the `receipts/` folder.

### Reprint Receipt
1. Load the card
2. Click **"🖨️ Print Last Receipt"** in Quick Actions
3. PDF opens automatically

### Card Summary
1. Load the card
2. Click **"📄 Print Card Summary"**
3. View complete transaction history

---

## 📊 Generate Reports

### Daily Report
1. Click **"📅 Daily Report"** in Quick Actions
2. Enter date or leave blank for today
3. Choose save location
4. PDF report generated

### Weekly/Monthly Reports
Same process for:
- **"🗓 Weekly Report"**
- **"📆 Monthly Report"**
- **"📈 Yearly Report"**

---

## 🎯 Common Tasks

### Task 1: Setup New Employee Card
```
1. Read new RFID card (or use Manual Mode)
2. System creates card with 0.00 balance
3. Enter initial allowance (e.g., 200.00)
4. Click "Set Balance"
5. Done! Receipt printed.
```

### Task 2: Daily Top-Up
```
1. Read employee's card
2. See current balance
3. Enter top-up amount
4. Click "Add to Balance"
5. Hand receipt to employee
```

### Task 3: Check All Cards
```
1. Click "View All Cards" in Quick Actions
2. See list of all cards and balances
3. Search, filter, or export as needed
```

### Task 4: Fix Incorrect Balance
```
1. Read the card
2. Enter correct balance in amount field
3. Click "Set Balance"
4. System shows difference to be added/deducted
5. Confirm correction
```

---

## 🔍 Testing Without Hardware

### Using Manual Mode
Perfect for testing or when Arduino is unavailable:

1. **Enable Manual Mode**:
   - Check "Enable Manual Card Entry"
   
2. **Create Test Cards**:
   - Enter UID: `TEST_001`, `TEST_002`, etc.
   - Click "Load Card UID"
   
3. **Test Operations**:
   - Add balance
   - Set balance
   - Print receipts
   - Generate reports

4. **Run Test Script**:
   ```bash
   python test_complete_system.py
   ```

---

## 📱 User Interface Overview

```
┌─────────────────────────────────────────────────────┐
│  🎫 RFID Reception System     ● Connected (COM3)   │
├──────────────────────┬──────────────────────────────┤
│  💳 Card Operations  │  🎯 Quick Actions            │
│                      │                              │
│  Card UID: [...]     │  [🎫 View All Cards]         │
│  Balance: 50.00 EGP  │  [🖨️ Print Last Receipt]    │
│                      │  [📄 Print Card Summary]     │
│  [🔍 Read Card]      │  [✏️ Insert Card Manual]    │
│                      │  [📅 Daily Report]           │
│  Top-Up: [____] EGP  │  [🗓 Weekly Report]          │
│  [10][20][50][100]   │  [📆 Monthly Report]         │
│                      │  [📈 Yearly Report]          │
│  [✓ Add][✍ Set]      │                              │
│                      │                              │
│  ⚙ Manual Mode       │                              │
│  ☐ Enable Manual     │                              │
│  [____________]       │                              │
│  [Load Card UID]     │                              │
└──────────────────────┴──────────────────────────────┘
│  Status: Ready                                       │
└─────────────────────────────────────────────────────┘
```

---

## ❓ Troubleshooting

### Arduino Not Connecting
- Check USB cable connection
- Verify correct COM port in Settings
- Try unplugging and replugging Arduino
- **Workaround**: Use Manual Mode

### Card Not Reading
- Ensure card is close to reader
- Check Arduino serial monitor for errors
- Try reading the card again
- **Workaround**: Use Manual Mode with card UID

### Receipt Not Printing
- Receipts are always saved as PDF in `receipts/` folder
- Open PDF manually and print if needed
- Check printer settings in Windows

### Balance Incorrect
- Use "Set Balance" to correct the amount
- Print card summary to review transaction history
- Check reports for discrepancies

---

## 📚 More Information

- **Employee Guide**: `EMPLOYEE_GUIDE.md`
- **Enhanced Features**: `ENHANCED_FEATURES.md`
- **Receipt Printing**: `RECEIPT_PRINTING_GUIDE.md`
- **Full Documentation**: `README.md`

---

## 🎓 Video Tutorial Steps

### For Training New Staff:

**5-Minute Training Plan**:
1. **Minute 1**: Show interface overview
2. **Minute 2**: Demonstrate card reading (manual mode)
3. **Minute 3**: Show add balance operation
4. **Minute 4**: Show set balance operation
5. **Minute 5**: Generate and view a receipt

**Practice Exercise**:
```
1. Create test card: TEST_EMPLOYEE_001
2. Set initial balance: 100.00 EGP
3. Simulate purchase: Add -15.00 EGP
4. Top-up: Add 50.00 EGP
5. Print card summary
```

---

## ✅ Success Checklist

After setup, you should be able to:
- [ ] Launch the application
- [ ] Read a card (or use manual mode)
- [ ] Add balance to a card
- [ ] Set exact balance on a card
- [ ] Generate and view receipts
- [ ] View all cards in system
- [ ] Generate daily/weekly reports
- [ ] Print card summaries

---

## 🚀 You're Ready!

The system is now fully operational. Start with manual mode to get familiar with the interface, then connect your Arduino for full hardware integration.

**Need Help?**  
Refer to the detailed guides in the documentation folder or contact your system administrator.

---

**Version**: 2.0  
**Last Updated**: October 2025  
**Status**: Production Ready ✅
