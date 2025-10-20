# Quick Start Guide - RFID Reception System

This guide will help you get the RFID Reception System up and running quickly.

## Prerequisites

- Python 3.10 or higher installed
- Arduino board with RFID reader (optional for testing)
- Windows PC (for production deployment)

## Installation (5 minutes)

### Step 1: Clone the Repository

```bash
git clone https://github.com/ahmedalaa9588406/rfid-reception-system.git
cd rfid-reception-system
```

### Step 2: Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Run the Application

```bash
python -m rfid_reception.app
```

That's it! The application should launch with the main GUI window.

## First Time Setup

When you first run the application:

1. **Configure Serial Connection** (if you have Arduino):
   - Click "Settings" button
   - Enter your COM port (e.g., COM3 on Windows, /dev/ttyUSB0 on Linux)
   - Set baud rate (default: 115200)
   - Click "Test Connection" to verify
   - Click "Save"

2. **Configure Without Arduino** (for testing):
   - The app will work without Arduino connection
   - You won't be able to read/write actual cards
   - All other features (database, reports) will work

## Basic Usage

### Top-Up a Card

1. Connect Arduino with RFID reader (or skip if testing)
2. Click "Read Card" button
3. Place RFID card near reader
4. Enter amount or use quick amount buttons (10, 20, 50, 100 EGP)
5. Click "Top-Up" button
6. Confirm the transaction

### View Transactions

1. Click "View Transactions" button
2. Adjust date filters if needed
3. Click "Refresh" to see transactions
4. View total amount at the bottom

### Generate Reports

1. Click "Generate Report" button
2. Select report type (Daily, Weekly, or Monthly)
3. Select date
4. Click "Generate"
5. Find the report in the `reports/` folder

### Backup Database

Backups are automatic at 23:59 daily. To manually backup:

1. Navigate to Settings
2. Note the backup folder location
3. Copy the `rfid_reception.db` file manually
4. Or wait for automatic backup

## Testing Without Hardware

You can test the application without Arduino:

1. Run the application
2. Use the GUI to:
   - View the main interface
   - Check Settings dialog
   - View Transactions (will be empty initially)
   - Generate Reports (will create empty reports)

3. To test with data:
   ```bash
   # Run the unit tests
   python -m pytest rfid_reception/tests/test_db.py -v
   ```

## Arduino Setup (Optional)

If you have Arduino with RFID reader:

1. Open `arduino_example/rfid_reader_example.ino` in Arduino IDE
2. Upload to your Arduino board
3. Note the COM port
4. Configure the port in application Settings
5. The example uses mock data - customize for your RFID hardware

## Project Structure

```
rfid-reception-system/
├── rfid_reception/         # Main application code
│   ├── app.py             # Entry point
│   ├── gui/               # GUI components
│   ├── services/          # Database and serial services
│   ├── models/            # Database models
│   └── tests/             # Unit tests
├── arduino_example/       # Arduino example sketch
├── requirements.txt       # Python dependencies
├── setup.py              # Package installer
└── README.md             # Full documentation
```

## File Locations

After running the application:

- **Database**: `rfid_reception.db` (in current directory)
- **Logs**: `logs/rfid_reception.log`
- **Backups**: `backups/backup_YYYY-MM-DD_HH-MM-SS.db`
- **Reports**: `reports/*.csv`
- **Config**: `config/config.json`

## Troubleshooting

### Application won't start
- Ensure Python 3.10+ is installed: `python --version`
- Install dependencies: `pip install -r requirements.txt`

### Can't connect to Arduino
- Check COM port in Device Manager (Windows)
- Verify Arduino is connected via USB
- Ensure correct baud rate (115200)
- Try different USB ports

### Database errors
- Check file permissions in application directory
- Close other programs that might be using the database
- Delete `rfid_reception.db` to start fresh

### GUI doesn't show
- On Linux: Install tkinter with `sudo apt-get install python3-tk`
- Ensure you're not running in headless environment

## Next Steps

1. Read the full [README.md](README.md) for detailed documentation
2. Customize Arduino sketch for your RFID hardware
3. Configure employee name in Settings
4. Set up automatic backup schedule
5. Test with real RFID cards
6. Package as .exe for distribution (see README.md)

## Support

For issues or questions:
- Check [README.md](README.md) for detailed information
- Review [arduino_example/README.md](arduino_example/README.md) for Arduino setup
- Check logs in `logs/rfid_reception.log` for errors

## License

MIT License - See [LICENSE](LICENSE) file
