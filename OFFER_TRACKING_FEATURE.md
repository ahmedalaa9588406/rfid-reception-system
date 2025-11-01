# 💰 Offer Tracking Feature - Complete Implementation

## Overview
Added comprehensive offer tracking to the RFID Reception System. The system now tracks and displays:
- **Original payment amount** (before offer bonus)
- **Offer bonus amount** (calculated from offer percentage)
- **Total amount** (original + bonus)

This allows you to see exactly how much a customer paid and how much bonus they received from promotional offers.

---

## 🎯 What's New

### 1. **Database Schema Updates** (`schema.py`)

#### Added to Transaction Model:
- `amount_before_offer` (REAL) - Original payment amount before offer bonus
- `offer_amount` (REAL) - Bonus amount from offer  
- `offer_percent` (REAL) - Offer percentage that was applied

**Example Transaction:**
- Customer pays: **50 EGP** (`amount_before_offer`)
- Offer: **10%** (`offer_percent`)
- Bonus: **5 EGP** (`offer_amount`)
- Total added to card: **55 EGP** (`amount`)

---

### 2. **Database Service Updates** (`db_service.py`)

#### Updated `top_up()` Method:
```python
def top_up(self, card_uid, amount, employee=None, notes=None, 
           amount_before_offer=None, offer_amount=None, offer_percent=None):
```

**New Parameters:**
- `amount_before_offer` - Original payment (e.g., 50 EGP)
- `offer_amount` - Calculated bonus (e.g., 5 EGP)
- `offer_percent` - Offer percentage (e.g., 10%)

#### Updated `get_transactions()` Method:
Now returns offer fields in transaction dictionaries.

---

### 3. **Main Window Updates** (`main_window.py`)

#### Modified Top-Up Functions:
- `_manual_top_up()` - Now passes offer details to `db_service.top_up()`
- `_arduino_top_up()` - Now passes offer details to `db_service.top_up()`

**Calculation Example:**
```python
amount = 50.0              # User enters 50
offer_percent = 10.0       # 10% offer set
offer_amount = 5.0         # Calculated: 50 * 10% = 5
total_amount = 55.0        # Total: 50 + 5 = 55

# Stored in transaction:
amount_before_offer = 50.0
offer_amount = 5.0
offer_percent = 10.0
amount = 55.0              # Total added to card
```

---

### 4. **View All Cards Dialog Updates** (`view_all_cards_dialog.py`)

#### New Column: "آخر مبلغ مدفوع" (Last Amount Paid)
Displays the original payment amount from the most recent transaction (before offer bonus).

#### Updated Table Columns:
```
| معرّف البطاقة | الرصيد | نسبة العرض % | آخر مبلغ مدفوع | الموظف | الحالة |
|--------------|--------|------------|---------------|---------|-------|
| Card UID     | Balance| Offer %    | Last Paid     | Employee| Status|
```

#### Enhanced `_enrich_cards_with_offer_data()`:
Now fetches:
- Card's current offer percentage
- Last transaction's `amount_before_offer`
- Last transaction's `offer_amount`
- Last transaction's `offer_percent`

---

### 5. **Database Migration Script** (`migrate_add_offer_tracking.py`)

**Purpose:** Adds new columns to existing databases

**How to Run:**
```bash
python migrate_add_offer_tracking.py
```

**What it Does:**
1. Checks if columns exist
2. Adds missing columns:
   - `amount_before_offer`
   - `offer_amount`  
   - `offer_percent`
3. Verifies migration success
4. Safe to run multiple times

---

## 📊 Usage Examples

### Example 1: Customer Pays 100 EGP with 15% Offer

**Input:**
- Amount: 100
- Offer %: 15

**Database Storage:**
```python
Transaction {
    amount_before_offer: 100.0,
    offer_amount: 15.0,
    offer_percent: 15.0,
    amount: 115.0,          # Total added
    balance_after: 215.0    # Assuming previous balance was 100
}
```

**View All Cards Display:**
- **الرصيد**: 215.00 جنيه
- **نسبة العرض %**: 15%
- **آخر مبلغ مدفوع**: 100.00 ج

---

### Example 2: Customer Pays 50 EGP with No Offer

**Input:**
- Amount: 50
- Offer %: 0

**Database Storage:**
```python
Transaction {
    amount_before_offer: 50.0,
    offer_amount: 0.0,
    offer_percent: 0.0,
    amount: 50.0,
    balance_after: 150.0
}
```

**View All Cards Display:**
- **الرصيد**: 150.00 جنيه
- **نسبة العرض %**: 0%
- **آخر مبلغ مدفوع**: 50.00 ج

---

## 🔧 Technical Details

### Data Flow

```
User Input (50 EGP, 10% offer)
    ↓
Calculate Offer (5 EGP bonus)
    ↓
Total Amount (55 EGP)
    ↓
Call db_service.top_up(
    amount=55,
    amount_before_offer=50,
    offer_amount=5,
    offer_percent=10
)
    ↓
Store in transactions table
    ↓
Display in View All Cards
```

### Database Schema

**transactions table:**
```sql
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY,
    card_uid TEXT,
    type TEXT,
    amount REAL,                    -- Total (including offer)
    amount_before_offer REAL,       -- Original payment (NEW)
    offer_amount REAL,              -- Bonus from offer (NEW)
    offer_percent REAL,             -- Offer % applied (NEW)
    balance_after REAL,
    employee TEXT,
    timestamp DATETIME,
    notes TEXT
);
```

---

## 🚀 How to Use

### For End Users:

1. **View Last Payment Amount:**
   - Open "عرض جميع البطاقات" (View All Cards)
   - Check "آخر مبلغ مدفوع" column
   - See original amount paid (before offer bonus)

2. **See Offer Details:**
   - Column shows actual payment
   - Compare with balance to see total bonus received

### For Administrators:

1. **Run Migration (One Time Only):**
   ```bash
   python migrate_add_offer_tracking.py
   ```

2. **Verify Migration:**
   - Check console output
   - Look for "✓ Migration completed successfully!"

3. **Use As Normal:**
   - All future top-ups will automatically track offer details
   - Old transactions will have NULL values (shown as "غير متاح")

---

## 📝 Important Notes

### Backward Compatibility
- ✅ Old transactions continue to work
- ✅ New fields are optional (NULL allowed)
- ✅ System works with or without migration
- ✅ Migration is safe to run multiple times

### Data Display
- **New transactions:** Show actual paid amount
- **Old transactions:** Show "غير متاح" (Not Available)
- **No offer:** Show "0%" and original amount

### Calculations
```python
# Offer calculation
offer_amount = round(amount * (offer_percent / 100.0), 2)
total_amount = round(amount + offer_amount, 2)

# Example:
# amount = 75
# offer_percent = 20
# offer_amount = 15.00
# total_amount = 90.00
```

---

## 📂 Modified Files

### Core System:
1. `rfid_reception/models/schema.py` - Added transaction fields
2. `rfid_reception/services/db_service.py` - Updated top_up method
3. `rfid_reception/gui/main_window.py` - Pass offer details

### Dialogs:
4. `rfid_reception/gui/dialogs/view_all_cards_dialog.py` - Display offers

### Scripts:
5. `migrate_add_offer_tracking.py` - **NEW** - Database migration

### Documentation:
6. `OFFER_TRACKING_FEATURE.md` - **THIS FILE**

---

## 🎨 UI Changes

### Before:
```
| Card UID | Balance | Offer % | Employee | Status |
```

### After:
```
| Card UID | Balance | Offer % | Last Paid | Employee | Status |
|----------|---------|---------|-----------|----------|--------|
| ABC123   | 215.00  | 15%     | 100.00 ج  | Ahmed    | ✓ نشط |
```

**New Column**: "آخر مبلغ مدفوع" shows what customer actually paid.

---

## 🔍 Troubleshooting

### Issue: "Last Paid" shows "غير متاح"
**Cause:** Transaction was created before migration
**Solution:** Normal behavior for old transactions

### Issue: Offer not calculating
**Cause:** Check offer percentage field
**Solution:** Ensure offer_var has valid number

### Issue: Migration fails
**Cause:** Database in use or locked
**Solution:** 
1. Close application
2. Run migration again
3. Check logs for specific error

---

## 📈 Benefits

### For Business:
- ✅ Track actual revenue vs. promotional giveaways
- ✅ Understand customer payment patterns
- ✅ Analyze offer effectiveness
- ✅ Better financial reporting

### For Users:
- ✅ See transparent pricing
- ✅ Understand offer benefits
- ✅ Clear payment history
- ✅ Trust in system accuracy

### For Auditing:
- ✅ Complete transaction history
- ✅ Offer tracking per transaction
- ✅ Verifiable calculations
- ✅ Detailed logs

---

## 🎯 Future Enhancements

Potential improvements:
- [ ] Show offer history chart
- [ ] Total offers given per card
- [ ] Most popular offer percentages
- [ ] Offer redemption analytics
- [ ] Export offer reports

---

**Version**: 1.0  
**Date**: November 2025  
**Feature**: Complete Offer Tracking System
