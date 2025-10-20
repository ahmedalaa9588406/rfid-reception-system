# RFID Reception System

## Project Overview

I want to build a Python-based offline reception system for an RFID amusement park card system.

The concept:

A customer pays an amount (e.g., 50 EGP).

The receptionist enters this value in the GUI and presses "Top-Up".

Two things happen:

The value is sent to the Arduino via serial communication to write the amount on the RFID card.

The same transaction is saved locally in a SQLite database (offline).

At the end of each day/week/month, the system should generate CSV (and optional PDF) reports showing all top-ups and totals.

Finally, I want the app to be packaged as an .exe so it can run on Windows computers without Python installed.

## Key Requirements

Main Goals:

- Offline operation (no internet needed)
- GUI for receptionist to top-up RFID cards
- Communication with Arduino via serial (USB)
- Local database storage (SQLite)
- Daily, weekly, and monthly reports
- Option to back up database
- Packaged into a single .exe file

## Tech Stack

- Language: Python 3.10+
- Database: SQLite (local .db file)
- ORM (optional): SQLAlchemy (or sqlite3 directly)
- GUI: Tkinter (simple and built-in)
- Serial communication: pyserial
- Scheduling: APScheduler or internal timers
- Logging: Python's built-in logging with rotating log files
- Packaging to .exe: PyInstaller

## Project Structure
```
rfid_reception/
├─ app.py                     # Main entry point – runs the GUI and connects services
├─ gui/
│  ├─ main_window.py          # Tkinter main interface
│  └─ dialogs.py              # Sub-windows for settings, reports, etc.
├─ services/
│  ├─ serial_comm.py          # Handles Arduino serial communication
│  └─ db_service.py           # SQLite database CRUD
├─ reports.py                 # Generates CSV/PDF reports
├─ scheduler.py               # Manages automatic report/backup scheduling
├─ models/
│  └─ schema.py               # Database table definitions
├─ tests/
│  └─ test_db.py              # Unit tests for database functions
├─ config/
│  └─ config.json             # Stores COM port, baud rate, backup folder, etc.
├─ requirements.txt
└─ README.md
```

## Database Schema (SQLite)

**Table: cards**

| Field | Type | Notes |
|-------|------|-------|
| id | INTEGER (PK) | Auto increment |
| card_uid | TEXT | Unique RFID card ID |
| balance | REAL | Current balance |
| created_at | DATETIME | Default CURRENT_TIMESTAMP |
| last_topped_at | DATETIME | Nullable |

**Table: transactions**

| Field | Type | Notes |
|-------|------|-------|
| id | INTEGER (PK) | Auto increment |
| card_uid | TEXT | FK → cards.card_uid |
| type | TEXT | e.g. 'topup', 'refund', 'adjust' |
| amount | REAL | Transaction amount |
| balance_after | REAL | Balance after transaction |
| employee | TEXT | Optional |
| timestamp | DATETIME | Default CURRENT_TIMESTAMP |
| notes | TEXT | Optional |

## Core Functionalities

### Serial Communication (serial_comm.py)

- `connect(port, baudrate=115200)` → opens serial connection
- `read_card()` → requests Arduino to read current card UID
  - Response: `UID:<hexuid>` or `ERROR:<message>`
- `write_card(amount)` → sends top-up command
  - Command sent: `WRITE:<amount>\n`
  - Response: `OK:WROTE:<uid>:<amount>` or `ERROR:<message>`
- Handle retries, timeouts, and connection loss gracefully.

### Database Service (db_service.py)

- `create_or_get_card(card_uid)` → creates a new record if not found
- `top_up(card_uid, amount, employee=None, notes=None)` → adds balance and logs transaction
- `get_transactions(start_date, end_date, card_uid=None)` → retrieves filtered transactions

### Reports (reports.py)

- `generate_daily_report(date)` → CSV of all transactions that day
- `generate_weekly_report(week_start)` → same for weekly
- `generate_monthly_report(month, year)` → same for monthly
- Include total amounts and transaction counts at the top of each report

### GUI (main_window.py)

Main screen:

- Text box showing card_uid
- Input for amount
- Buttons for quick top-ups: 10 / 20 / 50 / 100 EGP
- "Top-Up" button (sends data to Arduino and DB)
- "Transactions" button (shows history)
- "Generate Report" button
- "Settings" (select COM port, backup folder, etc.)
- All buttons show success/failure popups.
- GUI auto-refreshes balance display after each operation.

### Scheduler (scheduler.py)

- Automatically generate daily backups and daily reports at a specified time.

### Backup Function

- Copies the .db file to a backup folder with a timestamp.
- Example: `backup_2025-10-20_23-59.db`