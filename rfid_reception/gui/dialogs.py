"""Dialog windows for settings, reports, and transactions."""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class SettingsDialog:
    """Settings dialog for configuring the application."""
    
    def __init__(self, parent, config, serial_service, on_save_callback):
        """Initialize settings dialog."""
        self.config = config
        self.serial_service = serial_service
        self.on_save_callback = on_save_callback
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Settings")
        self.dialog.geometry("400x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create settings widgets."""
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Serial settings
        serial_frame = ttk.LabelFrame(main_frame, text="Serial Connection", padding="10")
        serial_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(serial_frame, text="COM Port:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.port_var = tk.StringVar(value=self.config.get('serial_port', 'COM3'))
        port_entry = ttk.Entry(serial_frame, textvariable=self.port_var, width=20)
        port_entry.grid(row=0, column=1, pady=5)
        
        ttk.Label(serial_frame, text="Baud Rate:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.baudrate_var = tk.StringVar(value=str(self.config.get('baud_rate', 115200)))
        baudrate_combo = ttk.Combobox(serial_frame, textvariable=self.baudrate_var, 
                                     values=['9600', '57600', '115200'], width=18)
        baudrate_combo.grid(row=1, column=1, pady=5)
        
        ttk.Button(serial_frame, text="Test Connection", 
                  command=self._test_connection).grid(row=2, column=0, columnspan=2, pady=10)
        
        # Employee settings
        employee_frame = ttk.LabelFrame(main_frame, text="Employee Info", padding="10")
        employee_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(employee_frame, text="Employee Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.employee_var = tk.StringVar(value=self.config.get('employee_name', 'Receptionist'))
        employee_entry = ttk.Entry(employee_frame, textvariable=self.employee_var, width=20)
        employee_entry.grid(row=0, column=1, pady=5)
        
        # Backup settings
        backup_frame = ttk.LabelFrame(main_frame, text="Backup Settings", padding="10")
        backup_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(backup_frame, text="Backup Folder:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.backup_dir_var = tk.StringVar(value=self.config.get('backup_dir', 'backups'))
        backup_entry = ttk.Entry(backup_frame, textvariable=self.backup_dir_var, width=20)
        backup_entry.grid(row=0, column=1, pady=5)
        
        ttk.Button(backup_frame, text="Browse", 
                  command=self._browse_backup_dir).grid(row=0, column=2, padx=5)
        
        ttk.Label(backup_frame, text="Backup Time:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.backup_time_var = tk.StringVar(value=self.config.get('backup_time', '23:59'))
        backup_time_entry = ttk.Entry(backup_frame, textvariable=self.backup_time_var, width=20)
        backup_time_entry.grid(row=1, column=1, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=20)
        
        ttk.Button(button_frame, text="Save", command=self._save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def _test_connection(self):
        """Test serial connection."""
        port = self.port_var.get()
        try:
            baudrate = int(self.baudrate_var.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid baud rate")
            return
        
        try:
            if self.serial_service.is_connected:
                self.serial_service.disconnect()
            
            self.serial_service.connect(port=port, baudrate=baudrate)
            messagebox.showinfo("Success", f"Connected to {port} successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Connection failed: {e}")
    
    def _browse_backup_dir(self):
        """Browse for backup directory."""
        directory = filedialog.askdirectory()
        if directory:
            self.backup_dir_var.set(directory)
    
    def _save(self):
        """Save settings."""
        try:
            self.config['serial_port'] = self.port_var.get()
            self.config['baud_rate'] = int(self.baudrate_var.get())
            self.config['employee_name'] = self.employee_var.get()
            self.config['backup_dir'] = self.backup_dir_var.get()
            self.config['backup_time'] = self.backup_time_var.get()
            
            # Save to file
            import json
            from pathlib import Path
            config_file = Path('config/config.json')
            config_file.parent.mkdir(exist_ok=True)
            with open(config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            
            if self.on_save_callback:
                self.on_save_callback()
            
            self.dialog.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")


class TransactionsDialog:
    """Dialog to view transaction history."""
    
    def __init__(self, parent, db_service):
        """Initialize transactions dialog."""
        self.db_service = db_service
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Transaction History")
        self.dialog.geometry("800x500")
        self.dialog.transient(parent)
        
        self._create_widgets()
        self._load_transactions()
    
    def _create_widgets(self):
        """Create transaction view widgets."""
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Filter frame
        filter_frame = ttk.LabelFrame(main_frame, text="Filters", padding="5")
        filter_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(filter_frame, text="Start Date:").grid(row=0, column=0, padx=5)
        self.start_date_var = tk.StringVar(value=(datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'))
        ttk.Entry(filter_frame, textvariable=self.start_date_var, width=15).grid(row=0, column=1, padx=5)
        
        ttk.Label(filter_frame, text="End Date:").grid(row=0, column=2, padx=5)
        self.end_date_var = tk.StringVar(value=datetime.now().strftime('%Y-%m-%d'))
        ttk.Entry(filter_frame, textvariable=self.end_date_var, width=15).grid(row=0, column=3, padx=5)
        
        ttk.Button(filter_frame, text="Refresh", command=self._load_transactions).grid(row=0, column=4, padx=5)
        
        # Treeview
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree = ttk.Treeview(tree_frame, yscrollcommand=scrollbar.set,
                                columns=('ID', 'Card UID', 'Type', 'Amount', 'Balance', 'Employee', 'Time'),
                                show='headings')
        scrollbar.config(command=self.tree.yview)
        
        # Configure columns
        self.tree.heading('ID', text='ID')
        self.tree.heading('Card UID', text='Card UID')
        self.tree.heading('Type', text='Type')
        self.tree.heading('Amount', text='Amount')
        self.tree.heading('Balance', text='Balance After')
        self.tree.heading('Employee', text='Employee')
        self.tree.heading('Time', text='Timestamp')
        
        self.tree.column('ID', width=50)
        self.tree.column('Card UID', width=150)
        self.tree.column('Type', width=80)
        self.tree.column('Amount', width=80)
        self.tree.column('Balance', width=100)
        self.tree.column('Employee', width=120)
        self.tree.column('Time', width=150)
        
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # Summary label
        self.summary_var = tk.StringVar(value="Total: 0 transactions, 0.00 EGP")
        ttk.Label(main_frame, textvariable=self.summary_var, font=('Arial', 10, 'bold')).pack(pady=5)
        
        # Close button
        ttk.Button(main_frame, text="Close", command=self.dialog.destroy).pack(pady=5)
    
    def _load_transactions(self):
        """Load and display transactions."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        try:
            start_date = datetime.strptime(self.start_date_var.get(), '%Y-%m-%d')
            end_date = datetime.strptime(self.end_date_var.get(), '%Y-%m-%d')
            end_date = end_date.replace(hour=23, minute=59, second=59)
            
            transactions = self.db_service.get_transactions(
                start_date=start_date,
                end_date=end_date
            )
            
            total_amount = 0.0
            for t in transactions:
                self.tree.insert('', tk.END, values=(
                    t['id'],
                    t['card_uid'],
                    t['type'],
                    f"{t['amount']:.2f}",
                    f"{t['balance_after']:.2f}",
                    t['employee'] or '',
                    t['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                ))
                if t['type'] == 'topup':
                    total_amount += t['amount']
            
            self.summary_var.set(f"Total: {len(transactions)} transactions, {total_amount:.2f} EGP")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load transactions: {e}")


class ReportDialog:
    """Dialog for generating reports."""
    
    def __init__(self, parent, reports_generator):
        """Initialize report dialog."""
        self.reports_generator = reports_generator
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Generate Report")
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create report generation widgets."""
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="Select Report Type:", font=('Arial', 11, 'bold')).pack(pady=10)
        
        # Report type selection
        self.report_type = tk.StringVar(value='daily')
        
        ttk.Radiobutton(main_frame, text="Daily Report", 
                       variable=self.report_type, value='daily').pack(anchor=tk.W, padx=20, pady=5)
        ttk.Radiobutton(main_frame, text="Weekly Report", 
                       variable=self.report_type, value='weekly').pack(anchor=tk.W, padx=20, pady=5)
        ttk.Radiobutton(main_frame, text="Monthly Report", 
                       variable=self.report_type, value='monthly').pack(anchor=tk.W, padx=20, pady=5)
        
        # Date selection
        date_frame = ttk.Frame(main_frame)
        date_frame.pack(pady=20)
        
        ttk.Label(date_frame, text="Date:").grid(row=0, column=0, padx=5)
        self.date_var = tk.StringVar(value=datetime.now().strftime('%Y-%m-%d'))
        ttk.Entry(date_frame, textvariable=self.date_var, width=15).grid(row=0, column=1, padx=5)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="Generate", command=self._generate).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def _generate(self):
        """Generate the selected report."""
        try:
            report_type = self.report_type.get()
            date_str = self.date_var.get()
            
            if report_type == 'daily':
                report_path = self.reports_generator.generate_daily_report(date_str)
            elif report_type == 'weekly':
                report_path = self.reports_generator.generate_weekly_report(date_str)
            elif report_type == 'monthly':
                date = datetime.strptime(date_str, '%Y-%m-%d')
                report_path = self.reports_generator.generate_monthly_report(date.month, date.year)
            
            messagebox.showinfo("Success", f"Report generated:\n{report_path}")
            self.dialog.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate report: {e}")
