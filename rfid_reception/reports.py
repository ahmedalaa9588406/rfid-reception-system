"""Reports generation module for creating CSV and PDF reports."""

import csv
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict

logger = logging.getLogger(__name__)


class ReportsGenerator:
    """Generate various reports for transactions."""
    
    def __init__(self, db_service, output_dir='reports'):
        """Initialize reports generator."""
        self.db_service = db_service
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def _write_csv(self, filename, transactions, summary=None):
        """Write transactions to CSV file."""
        filepath = self.output_dir / filename
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Write summary if provided
                if summary:
                    writer.writerow(['Report Summary'])
                    writer.writerow(['Total Transactions:', summary.get('count', 0)])
                    writer.writerow(['Total Amount:', f"{summary.get('total', 0):.2f} EGP"])
                    writer.writerow(['Period:', summary.get('period', '')])
                    writer.writerow([])
                
                # Write header
                writer.writerow([
                    'ID', 'Card UID', 'Type', 'Amount', 
                    'Balance After', 'Employee', 'Timestamp', 'Notes'
                ])
                
                # Write transactions
                for t in transactions:
                    writer.writerow([
                        t['id'],
                        t['card_uid'],
                        t['type'],
                        f"{t['amount']:.2f}",
                        f"{t['balance_after']:.2f}",
                        t['employee'] or '',
                        t['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                        t['notes'] or ''
                    ])
            
            logger.info(f"Report generated: {filepath}")
            return str(filepath)
        except Exception as e:
            logger.error(f"Error generating CSV report: {e}")
            raise
    
    def generate_daily_report(self, date=None):
        """Generate daily report for all transactions on a specific date."""
        if date is None:
            date = datetime.now().date()
        elif isinstance(date, str):
            date = datetime.strptime(date, '%Y-%m-%d').date()
        
        start_date = datetime.combine(date, datetime.min.time())
        end_date = datetime.combine(date, datetime.max.time())
        
        transactions = self.db_service.get_transactions(
            start_date=start_date,
            end_date=end_date
        )
        
        total_amount = sum(t['amount'] for t in transactions if t['type'] == 'topup')
        
        summary = {
            'count': len(transactions),
            'total': total_amount,
            'period': f"{date.strftime('%Y-%m-%d')}"
        }
        
        filename = f"daily_report_{date.strftime('%Y-%m-%d')}.csv"
        return self._write_csv(filename, transactions, summary)
    
    def generate_weekly_report(self, week_start=None):
        """Generate weekly report starting from a specific date."""
        if week_start is None:
            # Start from Monday of current week
            today = datetime.now().date()
            week_start = today - timedelta(days=today.weekday())
        elif isinstance(week_start, str):
            week_start = datetime.strptime(week_start, '%Y-%m-%d').date()
        
        week_end = week_start + timedelta(days=6)
        
        start_date = datetime.combine(week_start, datetime.min.time())
        end_date = datetime.combine(week_end, datetime.max.time())
        
        transactions = self.db_service.get_transactions(
            start_date=start_date,
            end_date=end_date
        )
        
        total_amount = sum(t['amount'] for t in transactions if t['type'] == 'topup')
        
        summary = {
            'count': len(transactions),
            'total': total_amount,
            'period': f"{week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')}"
        }
        
        filename = f"weekly_report_{week_start.strftime('%Y-%m-%d')}.csv"
        return self._write_csv(filename, transactions, summary)
    
    def generate_monthly_report(self, month=None, year=None):
        """Generate monthly report for a specific month and year."""
        if month is None or year is None:
            now = datetime.now()
            month = month or now.month
            year = year or now.year
        
        # First day of the month
        start_date = datetime(year, month, 1)
        
        # Last day of the month
        if month == 12:
            end_date = datetime(year + 1, 1, 1) - timedelta(seconds=1)
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(seconds=1)
        
        transactions = self.db_service.get_transactions(
            start_date=start_date,
            end_date=end_date
        )
        
        total_amount = sum(t['amount'] for t in transactions if t['type'] == 'topup')
        
        summary = {
            'count': len(transactions),
            'total': total_amount,
            'period': f"{start_date.strftime('%B %Y')}"
        }
        
        filename = f"monthly_report_{year}_{month:02d}.csv"
        return self._write_csv(filename, transactions, summary)
    
    def generate_custom_report(self, start_date, end_date, card_uid=None):
        """Generate custom report for a specific date range and optional card."""
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        
        transactions = self.db_service.get_transactions(
            start_date=start_date,
            end_date=end_date,
            card_uid=card_uid
        )
        
        total_amount = sum(t['amount'] for t in transactions if t['type'] == 'topup')
        
        period_str = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
        if card_uid:
            period_str += f" (Card: {card_uid})"
        
        summary = {
            'count': len(transactions),
            'total': total_amount,
            'period': period_str
        }
        
        filename = f"custom_report_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv"
        return self._write_csv(filename, transactions, summary)
