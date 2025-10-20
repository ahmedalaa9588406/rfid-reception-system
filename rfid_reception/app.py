"""Main entry point for RFID Reception System."""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import logging
from pathlib import Path
import sys

from rfid_reception.services.db_service import DatabaseService
from rfid_reception.services.serial_comm import SerialCommunicationService
from rfid_reception.reports import ReportsGenerator
from rfid_reception.scheduler import TaskScheduler
from rfid_reception.gui.main_window import MainWindow


# Configure logging
def setup_logging():
    """Setup logging configuration."""
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'rfid_reception.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )


def load_config():
    """Load configuration from file or create default."""
    config_file = Path('config/config.json')
    
    default_config = {
        'serial_port': 'COM3',
        'baud_rate': 115200,
        'employee_name': 'Receptionist',
        'backup_dir': 'backups',
        'backup_time': '23:59',
        'report_time': '23:55',
        'db_path': 'rfid_reception.db'
    }
    
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                # Merge with defaults for any missing keys
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        except Exception as e:
            logging.error(f"Error loading config: {e}")
            return default_config
    else:
        # Create default config file
        config_file.parent.mkdir(exist_ok=True)
        with open(config_file, 'w') as f:
            json.dump(default_config, f, indent=4)
        return default_config


def main():
    """Main application entry point."""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting RFID Reception System...")
    
    # Load configuration
    config = load_config()
    
    # Initialize services
    try:
        # Database service
        db_service = DatabaseService(config['db_path'])
        logger.info("Database service initialized")
        
        # Serial communication service
        serial_service = SerialCommunicationService(
            port=config.get('serial_port'),
            baudrate=config.get('baud_rate', 115200)
        )
        
        # Try to connect to Arduino (optional - can be configured in settings)
        try:
            if config.get('serial_port'):
                serial_service.connect()
                logger.info("Serial connection established")
        except Exception as e:
            logger.warning(f"Could not connect to serial port: {e}")
            logger.info("You can configure serial connection in Settings")
        
        # Reports generator
        reports_generator = ReportsGenerator(db_service, output_dir='reports')
        logger.info("Reports generator initialized")
        
        # Scheduler
        scheduler = TaskScheduler(
            db_service,
            reports_generator,
            db_path=config['db_path'],
            backup_dir=config['backup_dir']
        )
        scheduler.start(
            backup_time=config.get('backup_time', '23:59'),
            report_time=config.get('report_time', '23:55')
        )
        logger.info("Scheduler started")
        
        # Create GUI
        root = tk.Tk()
        
        # Set theme
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except:
            pass  # Use default theme if clam is not available
        
        # Create main window
        app = MainWindow(root, db_service, serial_service, reports_generator, scheduler, config)
        
        logger.info("Application started successfully")
        
        # Run main loop
        root.mainloop()
        
        # Cleanup
        scheduler.stop()
        serial_service.disconnect()
        logger.info("Application closed")
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        messagebox.showerror("Fatal Error", f"Application failed to start: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
