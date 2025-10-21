"""Scheduler for automatic report generation and database backups."""

import logging
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)


class TaskScheduler:
    """Scheduler for automatic tasks like backups and reports."""
    
    def __init__(self, db_service, reports_generator, db_path='rfid_reception.db', backup_dir='backups'):
        """Initialize the scheduler."""
        self.db_service = db_service
        self.reports_generator = reports_generator
        self.db_path = Path(db_path)
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        
        self.scheduler = BackgroundScheduler()
        self.is_running = False
    
    def backup_database(self):
        """Create a backup of the database file."""
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            backup_filename = f"backup_{timestamp}.db"
            backup_path = self.backup_dir / backup_filename
            
            if self.db_path.exists():
                shutil.copy2(self.db_path, backup_path)
                logger.info(f"Database backup created: {backup_path}")
                
                # Clean up old backups (keep last 30)
                self._cleanup_old_backups(keep=30)
                return str(backup_path)
            else:
                logger.warning(f"Database file not found: {self.db_path}")
                return None
        except Exception as e:
            logger.error(f"Error creating database backup: {e}")
            raise
    
    def _cleanup_old_backups(self, keep=30):
        """Remove old backups, keeping only the specified number of recent ones."""
        try:
            backups = sorted(self.backup_dir.glob('backup_*.db'), 
                           key=lambda x: x.stat().st_mtime, 
                           reverse=True)
            
            for old_backup in backups[keep:]:
                old_backup.unlink()
                logger.info(f"Removed old backup: {old_backup}")
        except Exception as e:
            logger.error(f"Error cleaning up old backups: {e}")
    
    def generate_daily_report_task(self):
        """Task to generate daily report."""
        try:
            report_path = self.reports_generator.generate_daily_report()
            logger.info(f"Automated daily report generated: {report_path}")
        except Exception as e:
            logger.error(f"Error generating automated daily report: {e}")
    
    def generate_weekly_report_task(self):
        """Task to generate last week's report (Mon-Sun)."""
        try:
            today = datetime.now().date()
            this_monday = today - timedelta(days=today.weekday())
            last_monday = this_monday - timedelta(days=7)
            report_path = self.reports_generator.generate_weekly_report(last_monday)
            logger.info(f"Automated weekly report generated: {report_path}")
        except Exception as e:
            logger.error(f"Error generating automated weekly report: {e}")
    
    def generate_monthly_report_task(self):
        """Task to generate last month's report."""
        try:
            now = datetime.now()
            month = now.month - 1
            year = now.year
            if month == 0:
                month = 12
                year -= 1
            report_path = self.reports_generator.generate_monthly_report(month, year)
            logger.info(f"Automated monthly report generated: {report_path}")
        except Exception as e:
            logger.error(f"Error generating automated monthly report: {e}")
    
    def start(self, backup_time='23:59', report_time='23:55',
              weekly_day_of_week='mon', weekly_time='00:10',
              monthly_day=1, monthly_time='00:15'):
        """
        Start the scheduler with daily tasks.
        
        Args:
            backup_time: Time to run daily backup (HH:MM format)
            report_time: Time to run daily report (HH:MM format)
            weekly_day_of_week: Day of week to run weekly report (mon..sun)
            weekly_time: Time to run weekly report (HH:MM)
            monthly_day: Day of month to run monthly report (1-31)
            monthly_time: Time to run monthly report (HH:MM)
        """
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        # Parse times
        backup_hour, backup_minute = map(int, backup_time.split(':'))
        report_hour, report_minute = map(int, report_time.split(':'))
        weekly_hour, weekly_minute = map(int, weekly_time.split(':'))
        monthly_hour, monthly_minute = map(int, monthly_time.split(':'))
        
        # Schedule daily backup
        self.scheduler.add_job(
            self.backup_database,
            trigger=CronTrigger(hour=backup_hour, minute=backup_minute),
            id='daily_backup',
            name='Daily Database Backup',
            replace_existing=True
        )
        
        # Schedule daily report
        self.scheduler.add_job(
            self.generate_daily_report_task,
            trigger=CronTrigger(hour=report_hour, minute=report_minute),
            id='daily_report',
            name='Daily Report Generation',
            replace_existing=True
        )
        
        # Schedule weekly report
        self.scheduler.add_job(
            self.generate_weekly_report_task,
            trigger=CronTrigger(day_of_week=weekly_day_of_week, hour=weekly_hour, minute=weekly_minute),
            id='weekly_report',
            name='Weekly Report Generation',
            replace_existing=True
        )
        
        # Schedule monthly report
        self.scheduler.add_job(
            self.generate_monthly_report_task,
            trigger=CronTrigger(day=monthly_day, hour=monthly_hour, minute=monthly_minute),
            id='monthly_report',
            name='Monthly Report Generation',
            replace_existing=True
        )
        
        self.scheduler.start()
        self.is_running = True
        logger.info(
            f"Scheduler started - Backup: {backup_time}, Daily: {report_time}, "
            f"Weekly: {weekly_day_of_week} {weekly_time}, Monthly: day {monthly_day} {monthly_time}"
        )
    
    def stop(self):
        """Stop the scheduler."""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Scheduler stopped")
    
    def get_jobs(self):
        """Get list of scheduled jobs."""
        return self.scheduler.get_jobs()
