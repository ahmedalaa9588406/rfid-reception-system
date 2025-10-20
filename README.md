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

## Installation & Setup

### Prerequisites

- Python 3.10 or higher
- Arduino with RFID reader (for hardware integration)
- Windows OS (for .exe packaging)

### Installation Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ahmedalaa9588406/rfid-reception-system.git
   cd rfid-reception-system
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   python -m rfid_reception.app
   ```

   Or if installed via setup.py:
   ```bash
   python setup.py install
   rfid-reception
   ```

### Configuration

On first run, a default configuration file is created at `config/config.json`. You can modify:

- **serial_port**: COM port for Arduino (e.g., "COM3", "/dev/ttyUSB0")
- **baud_rate**: Serial communication speed (default: 115200)
- **employee_name**: Default employee name for transactions
- **backup_dir**: Directory for database backups
- **backup_time**: Time for automatic daily backup (HH:MM format)
- **report_time**: Time for automatic daily report (HH:MM format)

You can also configure these settings through the GUI Settings menu.

## Usage

### Starting the Application

1. Launch the application
2. Configure serial port in Settings if not automatically connected
3. Click "Read Card" to detect an RFID card
4. Enter amount or use quick amount buttons
5. Click "Top-Up" to add balance to the card

### Features

- **Real-time Card Reading**: Communicate with Arduino to read RFID cards
- **Manual Entry Mode**: Enter card UIDs manually when Arduino is not available
- **Balance Management**: Top-up cards with customizable amounts
- **Transaction History**: View all transactions with date filters
- **Reports**: Generate daily, weekly, or monthly CSV reports
- **Automatic Backups**: Scheduled database backups at configured time
- **Offline Operation**: Works completely offline, no internet required
- **Dual Mode Operation**: Switch between Arduino mode and manual entry mode seamlessly

### Testing

Run the test suite:
```bash
python -m pytest rfid_reception/tests/
```

Or run specific tests:
```bash
python -m unittest rfid_reception.tests.test_db
```

## Packaging to .exe

To create a standalone Windows executable:

1. **Install PyInstaller** (if not already installed):
   ```bash
   pip install pyinstaller
   ```

2. **Create the executable:**
   ```bash
   pyinstaller --onefile --windowed --name "RFID Reception" rfid_reception/app.py
   ```

3. **Find the executable:**
   The .exe file will be in the `dist/` directory.

### Advanced Packaging Options

For a more complete package with all resources:
```bash
pyinstaller --onedir --windowed --name "RFID Reception" --add-data "config;config" rfid_reception/app.py
```

## Arduino Protocol

The application expects the Arduino to respond to the following commands:

### READ Command
- **Send**: `READ\n`
- **Response**: `UID:<card_uid>\n` or `ERROR:<message>\n`

### WRITE Command
- **Send**: `WRITE:<amount>\n`
- **Response**: `OK:WROTE:<uid>:<amount>\n` or `ERROR:<message>\n`

### PING Command
- **Send**: `PING\n`
- **Response**: Any response indicates connection is alive

## Project Structure (Actual Implementation)

```
rfid-reception-system/
├── rfid_reception/
│   ├── __init__.py
│   ├── app.py                  # Main entry point
│   ├── gui/
│   │   ├── __init__.py
│   │   ├── main_window.py      # Main GUI window
│   │   └── dialogs.py          # Settings, reports, transactions dialogs
│   ├── services/
│   │   ├── __init__.py
│   │   ├── db_service.py       # Database CRUD operations
│   │   └── serial_comm.py      # Arduino serial communication
│   ├── models/
│   │   ├── __init__.py
│   │   └── schema.py           # SQLAlchemy models
│   ├── reports.py              # CSV report generation
│   ├── scheduler.py            # Automatic backups and reports
│   ├── config/
│   │   └── config.json         # Configuration file
│   └── tests/
│       ├── __init__.py
│       └── test_db.py          # Database tests
├── requirements.txt
├── setup.py
└── README.md
```

## Troubleshooting

### Serial Connection Issues

- Verify the COM port in Device Manager (Windows)
- Ensure Arduino is connected and drivers are installed
- Check baud rate matches Arduino sketch (default: 115200)
- Try different USB ports

### Database Locked Error

- Close any other applications accessing the database
- Check file permissions in the application directory

### GUI Not Showing

- Ensure tkinter is installed with Python
- On Linux: `sudo apt-get install python3-tk`

## License

This project is open source and available under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.