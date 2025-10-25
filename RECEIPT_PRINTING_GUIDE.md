# 🖨️ Receipt Printing Guide - RFID Reception System

Complete guide for the receipt printing functionality that works with all printers.

---

## 📋 Overview

The RFID Reception System now includes **automatic receipt printing** after every top-up transaction. The system supports:

✅ **Auto-print after top-up** (configurable)  
✅ **Manual receipt reprint** (for last transaction)  
✅ **Card summary reports** (complete history)  
✅ **PDF generation** (universal compatibility)  
✅ **Direct printer support** (Windows with pywin32)  
✅ **Professional thermal receipt format**  

---

## 🎯 Features

### 1. Auto-Print After Top-Up
When an employee completes a top-up transaction, a receipt is automatically generated with:
- Transaction ID
- Date and time
- Card UID
- Amount added
- New balance
- Employee name
- Company information

### 2. Manual Receipt Printing
Two new buttons in the Quick Actions panel:
- **🖨️ Print Last Receipt**: Reprints the most recent transaction
- **📄 Print Card Summary**: Generates complete card history report

### 3. Cross-Platform Support
- **Windows**: Direct printing to default printer (optional)
- **All Platforms**: PDF generation in `receipts/` folder
- **Thermal Printers**: Optimized 80mm thermal receipt format
- **Standard Printers**: A4 format for detailed summaries

---

## 🔧 Installation

### Step 1: Install Required Packages

```bash
# Navigate to project directory
cd rfid-reception-system

# Install core receipt dependencies
pip install Pillow>=10.0.0

# For Windows users who want direct printing (optional)
pip install pywin32>=306
```

### Step 2: Configure Settings

Edit your configuration file to enable/customize receipt printing:

```python
# In config file or settings
{
    'auto_print_receipts': True,  # Enable auto-print
    'company_name': 'Your Company Name',
    'company_address': '123 Main St, City',
    'company_phone': '+20 123 456 7890'
}
```

---

## 📊 Receipt Formats

### Transaction Receipt (80mm Thermal)

```
================================
    YOUR COMPANY NAME
    123 Main St, City
    Tel: +20 123 456 7890
================================

   TRANSACTION RECEIPT

Transaction ID: #123
Date: 2025-10-23
Time: 13:45:30

Card UID: 04A1B2C3D4E5F6

╔══════════════════════════╗
║ Top-Up Amount:  100.50 EGP ║
║ New Balance:    150.50 EGP ║
╚══════════════════════════╝

Served by: Ahmed Hassan
________________________________

       Thank You!
 Keep this receipt for your records
   For support, contact reception
```

### Card Summary Report (A4 Full Page)

```
YOUR COMPANY NAME
Card Summary Report
Generated: 2025-10-23 13:45:30

Card Information
  Card UID: 04A1B2C3D4E5F6
  Current Balance: 150.50 EGP
  Created: 2025-10-01 09:00:00
  Last Top-up: 2025-10-23 13:45:30

Recent Transactions
  2025-10-23 13:45:30 | TOPUP: 100.50 EGP | Balance: 150.50 EGP
  2025-10-22 10:30:15 | TOPUP: 50.00 EGP  | Balance: 50.00 EGP
  2025-10-21 14:20:45 | READ: 0.00 EGP    | Balance: 0.00 EGP
  ...
```

---

## 🎮 How to Use

### For Employees (Daily Operations)

#### Auto-Print Workflow
1. **Read Card**: Click "🔍 Read Card" → Scan RFID card
2. **Enter Amount**: Type amount or click quick amount button
3. **Confirm Top-Up**: Click "✓ Confirm Top-Up"
4. **Receipt Prints**: Receipt automatically generates
5. **Hand to Customer**: Give printed receipt to customer

#### Manual Reprint
1. **Select Card**: Ensure card is loaded (shows in panel)
2. **Click**: "🖨️ Print Last Receipt" in Quick Actions
3. **Open**: Choose to open PDF automatically
4. **Print**: Use system print dialog (Ctrl+P)

#### Card Summary
1. **Select Card**: Load the card you want to summarize
2. **Click**: "📄 Print Card Summary" in Quick Actions
3. **Review**: PDF shows complete transaction history
4. **Archive**: Save for records or print for customer

---

## 🖨️ Printer Configuration

### Windows - Direct Printing

For **direct printing** to thermal or standard printers:

1. **Install pywin32**:
   ```bash
   pip install pywin32
   ```

2. **Set Default Printer**:
   - Open Windows Settings → Devices → Printers & scanners
   - Click your thermal/receipt printer
   - Click "Manage" → "Set as default"

3. **Test Printing**:
   - Run a test top-up transaction
   - Receipt should print immediately

### All Platforms - PDF Method

If direct printing is not available (or preferred):

1. **Receipts Save Location**: `receipts/` folder in project directory
2. **Auto-Open**: System asks to open PDF after generation
3. **Manual Print**: 
   - Open PDF with any viewer
   - Press Ctrl+P
   - Select your printer
   - Print

### Thermal Printer Settings

For **80mm thermal printers** (POS/receipt printers):

**Recommended Settings**:
- Paper width: 80mm (3.15 inches)
- Paper type: Thermal
- Print speed: Medium
- Darkness: Medium
- Auto-cut: Enable (if supported)

**Compatible Printers**:
- ✅ Epson TM-T20
- ✅ Star TSP143
- ✅ Citizen CT-S310
- ✅ Bixolon SRP-350
- ✅ Any ESC/POS compatible thermal printer

### Standard Printer Settings

For **A4/Letter paper printers**:

**For Transaction Receipts**:
- Print multiple receipts per page
- Cut along dotted lines
- Hand to customers

**For Card Summaries**:
- Full A4/Letter page
- Standard margins
- Color or black & white

---

## 📂 File Organization

### Receipt Files Location

```
rfid-reception-system/
├── receipts/                          ← All receipts saved here
│   ├── receipt_123_20251023_134530.pdf
│   ├── receipt_124_20251023_140215.pdf
│   ├── card_summary_04A1B2_20251023.pdf
│   └── ...
├── rfid_reception/
│   └── services/
│       ├── receipt_printer.py         ← Receipt printing service
│       └── ...
└── RECEIPT_PRINTING_GUIDE.md          ← This file
```

### File Naming Convention

- **Transaction Receipts**: `receipt_[ID]_[TIMESTAMP].pdf`
  - Example: `receipt_123_20251023_134530.pdf`
  
- **Card Summaries**: `card_summary_[UID]_[TIMESTAMP].pdf`
  - Example: `card_summary_04A1B2C3D4E5F6_20251023_140000.pdf`

---

## ⚙️ Configuration Options

### In Main Application Settings

```python
# config.json or settings file
{
    # Receipt Printing
    "auto_print_receipts": true,           # Auto-print after top-up
    
    # Company Information (appears on receipts)
    "company_name": "ABC Company Ltd.",
    "company_address": "123 Main Street, Cairo, Egypt",
    "company_phone": "+20 123 456 7890",
    "employee_name": "Ahmed Hassan",       # Default employee name
    
    # Printer Settings (optional)
    "default_printer": "Epson TM-T20",     # Windows only
    "receipt_format": "thermal",           # "thermal" or "standard"
}
```

### Programmatic Configuration

```python
from rfid_reception.services.receipt_printer import ReceiptPrinter

# Initialize with custom settings
receipt_printer = ReceiptPrinter(
    company_name="Your Company",
    company_info={
        'address': '123 Main St',
        'phone': '+20 123 456 7890',
        'email': 'info@company.com',
        'website': 'www.company.com'
    }
)

# Print a receipt
success, result = receipt_printer.print_receipt(
    card_uid="04A1B2C3D4E5F6",
    amount=100.50,
    balance_after=150.50,
    transaction_id=123,
    employee="Ahmed Hassan",
    auto_print=True  # True for direct print, False for PDF
)
```

---

## 🔍 Troubleshooting

### Receipt Not Printing

**Problem**: Receipt doesn't print after top-up

**Solutions**:
1. Check `auto_print_receipts` is set to `True` in config
2. Verify printer is connected and turned on
3. Check receipts folder - PDF should be generated
4. Look at status bar for error messages

### Direct Printing Failed

**Problem**: "Direct printing failed" message

**Solutions**:
1. Install pywin32: `pip install pywin32`
2. Set default printer in Windows settings
3. Check printer is online and has paper
4. System will auto-fallback to PDF generation

### PDF Not Opening

**Problem**: PDF generates but won't open

**Solutions**:
1. Install PDF reader (Adobe Acrobat, Foxit, etc.)
2. Check file permissions in `receipts/` folder
3. Manually navigate to receipts folder and open
4. Right-click PDF → Open with → Choose PDF reader

### Printer Shows Error

**Problem**: Printer displays error light or message

**Solutions**:
1. Check paper level (thermal paper roll)
2. Check paper jam
3. Restart printer
4. Check printer cable connection
5. Update printer drivers

### Text Appears Garbled

**Problem**: Receipt text is corrupted or unreadable

**Solutions**:
1. Ensure UTF-8 encoding is supported
2. Check printer font support
3. Use English characters for testing
4. Update printer firmware

---

## 📈 Usage Statistics

Track receipt printing in your logs:

```python
# Logs show receipt activity
INFO: Receipt printed to Epson TM-T20
INFO: Receipt saved to: receipts/receipt_123_20251023.pdf
ERROR: Direct printing failed: Printer offline - falling back to PDF
```

---

## 🎓 Advanced Features

### Custom Receipt Templates

Modify `receipt_printer.py` to customize receipt appearance:

```python
def _draw_receipt_pdf(self, c, receipt_data):
    # Add your company logo
    # Change colors and fonts
    # Add barcodes or QR codes
    # Include promotional messages
    pass
```

### Email Receipts

Extend functionality to email receipts to customers:

```python
def email_receipt(self, email_address, receipt_path):
    # Send PDF via email
    pass
```

### Receipt Numbering

Receipts use transaction IDs for unique identification:
- Each receipt is numbered sequentially
- Transaction ID links to database record
- Easy to lookup and verify transactions

---

## 🔒 Security & Compliance

### Data Privacy
- Receipts stored locally only
- No sensitive data transmitted
- Card UIDs displayed for verification

### Audit Trail
- All receipts saved in `receipts/` folder
- Transaction IDs link to database
- Timestamps for accountability

### Backup Recommendations
- Regularly backup `receipts/` folder
- Archive old receipts monthly
- Keep digital copies for tax purposes

---

## 📞 Support

### Common Questions

**Q: Can I disable auto-printing?**  
A: Yes, set `auto_print_receipts: false` in config

**Q: Can I change receipt format?**  
A: Yes, modify templates in `receipt_printer.py`

**Q: What paper size do I need?**  
A: 80mm (3.15") for thermal, A4/Letter for standard

**Q: Can I add a logo?**  
A: Yes, modify `_draw_receipt_pdf()` to include images

**Q: Does it work on Linux/Mac?**  
A: Yes, PDF generation works on all platforms

---

## ✅ Quick Checklist

Before going live with receipt printing:

- [ ] Install Pillow: `pip install Pillow`
- [ ] Install pywin32 (Windows): `pip install pywin32` (optional)
- [ ] Configure company information in settings
- [ ] Set default printer (Windows)
- [ ] Test print a receipt
- [ ] Load thermal paper (if using thermal printer)
- [ ] Verify receipts folder is created
- [ ] Train employees on receipt handling
- [ ] Keep backup paper rolls available

---

## 🎉 You're All Set!

Your RFID Reception System now has **professional receipt printing**!

- ✅ Auto-print after every transaction
- ✅ Manual reprint capability
- ✅ Card summary reports
- ✅ Works with all printers
- ✅ PDF fallback for compatibility

**Happy printing!** 🖨️
