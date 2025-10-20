"""Modern, user-friendly dialog for generating reports."""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import logging
from datetime import datetime, timedelta
from threading import Thread
from pathlib import Path

logger = logging.getLogger(__name__)


class ModernReportsDialog:
    """Modern dialog for report generation."""
    
    # Colors
    PRIMARY_COLOR = "#2E86AB"
    SECONDARY_COLOR = "#A23B72"
    SUCCESS_COLOR = "#06A77D"
    WARNING_COLOR = "#F18F01"
    LIGHT_BG = "#F5F5F5"
    DARK_TEXT = "#2C3E50"
    
    def __init__(self, parent: tk.Widget, reports_generator):
        """Initialize reports dialog."""
        self.parent = parent
        self.reports_generator = reports_generator
        self.is_generating = False
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("📊 Report Generator")
        self.dialog.geometry("700x650")
        self.dialog.minsize(600, 550)
        self.dialog.transient(parent)
        
        self._setup_theme()
        self._create_widgets()
        
        self.dialog.lift()
        self.dialog.focus_force()
    
    def _setup_theme(self) -> None:
        """Setup modern theme."""
        self.style = ttk.Style()
        try:
            self.style.theme_use('clam')
        except:
            self.style.theme_use('default')
    
    def _create_widgets(self) -> None:
        """Create dialog widgets."""
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        title_label = ttk.Label(
            main_frame,
            text="📊 Report Generator",
            font=('Segoe UI', 16, 'bold')
        )
        title_label.pack(anchor=tk.W, pady=(0, 20))
        
        # Report type section
        type_frame = ttk.LabelFrame(main_frame, text="Report Type", padding="15")
        type_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.report_type_var = tk.StringVar(value="daily")
        
        report_types = [
            ("📅 Daily Report", "daily"),
            ("📆 Weekly Report", "weekly"),
            ("📋 Monthly Report", "monthly"),
            ("📌 Custom Date Range", "custom")
        ]
        
        for label, value in report_types:
            ttk.Radiobutton(
                type_frame,
                text=label,
                variable=self.report_type_var,
                value=value,
                command=self._on_report_type_changed
            ).pack(anchor=tk.W, pady=5)
        
        # Date selection section
        self.date_frame = ttk.LabelFrame(main_frame, text="Date Selection", padding="15")
        self.date_frame.pack(fill=tk.X, pady=(0, 15))
        
        self._create_date_widgets()
        
        # Format selection
        format_frame = ttk.LabelFrame(main_frame, text="Output Format", padding="15")
        format_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.format_var = tk.StringVar(value="both")
        
        for label, value in [("📄 PDF", "pdf"), ("📊 CSV", "csv"), ("📦 Both", "both")]:
            ttk.Radiobutton(
                format_frame,
                text=label,
                variable=self.format_var,
                value=value
            ).pack(anchor=tk.W, pady=5)
        
        # Status
        self.status_var = tk.StringVar(value="Ready to generate report")
        status_label = ttk.Label(
            main_frame,
            textvariable=self.status_var,
            font=('Segoe UI', 9),
            foreground='#666666'
        )
        status_label.pack(anchor=tk.W, pady=(0, 15))
        
        # Progress bar
        self.progress = ttk.Progressbar(
            main_frame,
            mode='indeterminate'
        )
        self.progress.pack(fill=tk.X, pady=(0, 15))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        ttk.Button(
            button_frame,
            text="✕ Close",
            command=self.dialog.destroy
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            button_frame,
            text="📂 Open Reports Folder",
            command=self._open_reports_folder
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            button_frame,
            text="✓ Generate Report",
            command=self._generate_report
        ).pack(side=tk.RIGHT, padx=5)
    
    def _create_date_widgets(self) -> None:
        """Create date selection widgets."""
        # Clear existing
        for widget in self.date_frame.winfo_children():
            widget.destroy()
        
        report_type = self.report_type_var.get()
        
        if report_type == "daily":
            ttk.Label(self.date_frame, text="Select Date:").pack(anchor=tk.W)
            
            date_frame = ttk.Frame(self.date_frame)
            date_frame.pack(fill=tk.X, pady=10)
            
            self.date_var = tk.StringVar(value=datetime.now().strftime('%Y-%m-%d'))
            date_entry = ttk.Entry(date_frame, textvariable=self.date_var, width=20)
            date_entry.pack(side=tk.LEFT, padx=5)
            
            ttk.Button(
                date_frame,
                text="Select Date",
                command=lambda: self._select_date('date_var')
            ).pack(side=tk.LEFT, padx=5)
        
        elif report_type == "weekly":
            ttk.Label(self.date_frame, text="Week Starting (Monday):").pack(anchor=tk.W)
            
            date_frame = ttk.Frame(self.date_frame)
            date_frame.pack(fill=tk.X, pady=10)
            
            today = datetime.now().date()
            week_start = today - timedelta(days=today.weekday())
            
            self.week_start_var = tk.StringVar(value=week_start.strftime('%Y-%m-%d'))
            date_entry = ttk.Entry(date_frame, textvariable=self.week_start_var, width=20)
            date_entry.pack(side=tk.LEFT, padx=5)
            
            ttk.Button(
                date_frame,
                text="Select Date",
                command=lambda: self._select_date('week_start_var')
            ).pack(side=tk.LEFT, padx=5)
        
        elif report_type == "monthly":
            frame1 = ttk.Frame(self.date_frame)
            frame1.pack(fill=tk.X, pady=5)
            
            ttk.Label(frame1, text="Month:").pack(side=tk.LEFT, padx=5)
            self.month_var = tk.IntVar(value=datetime.now().month)
            month_spin = ttk.Spinbox(
                frame1,
                from_=1,
                to=12,
                textvariable=self.month_var,
                width=5
            )
            month_spin.pack(side=tk.LEFT, padx=5)
            
            ttk.Label(frame1, text="Year:").pack(side=tk.LEFT, padx=5)
            self.year_var = tk.IntVar(value=datetime.now().year)
            year_spin = ttk.Spinbox(
                frame1,
                from_=2020,
                to=2100,
                textvariable=self.year_var,
                width=6
            )
            year_spin.pack(side=tk.LEFT, padx=5)
        
        elif report_type == "custom":
            frame1 = ttk.Frame(self.date_frame)
            frame1.pack(fill=tk.X, pady=5)
            
            ttk.Label(frame1, text="Start Date:").pack(side=tk.LEFT, padx=5)
            self.start_date_var = tk.StringVar(
                value=(datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            )
            start_entry = ttk.Entry(frame1, textvariable=self.start_date_var, width=20)
            start_entry.pack(side=tk.LEFT, padx=5)
            
            ttk.Button(
                frame1,
                text="Select",
                command=lambda: self._select_date('start_date_var')
            ).pack(side=tk.LEFT, padx=2)
            
            frame2 = ttk.Frame(self.date_frame)
            frame2.pack(fill=tk.X, pady=5)
            
            ttk.Label(frame2, text="End Date:").pack(side=tk.LEFT, padx=5)
            self.end_date_var = tk.StringVar(value=datetime.now().strftime('%Y-%m-%d'))
            end_entry = ttk.Entry(frame2, textvariable=self.end_date_var, width=20)
            end_entry.pack(side=tk.LEFT, padx=5)
            
            ttk.Button(
                frame2,
                text="Select",
                command=lambda: self._select_date('end_date_var')
            ).pack(side=tk.LEFT, padx=2)
    
    def _on_report_type_changed(self) -> None:
        """Handle report type change."""
        self._create_date_widgets()
    
    def _select_date(self, var_name: str) -> None:
        """Open date picker."""
        from tkinter.simpledialog import askstring
        
        current = getattr(self, var_name).get()
        date = filedialog.askopenfilename(title=f"Select date (format: YYYY-MM-DD)")
        
        if date:
            try:
                datetime.strptime(date, '%Y-%m-%d')
                getattr(self, var_name).set(date)
            except:
                messagebox.showerror("Invalid Date", "Please use format: YYYY-MM-DD")
    
    def _generate_report(self) -> None:
        """Generate report in background thread."""
        if self.is_generating:
            messagebox.showwarning("In Progress", "Report generation already in progress")
            return
        
        self.is_generating = True
        self.progress.start()
        self.status_var.set("⏳ Generating report...")
        
        def generate_task():
            try:
                report_type = self.report_type_var.get()
                output_format = self.format_var.get()
                result = None
                
                if report_type == "daily":
                    date = self.date_var.get()
                    result = self.reports_generator.generate_daily_report(date, output_format)
                
                elif report_type == "weekly":
                    week_start = self.week_start_var.get()
                    result = self.reports_generator.generate_weekly_report(week_start, output_format)
                
                elif report_type == "monthly":
                    month = self.month_var.get()
                    year = self.year_var.get()
                    result = self.reports_generator.generate_monthly_report(month, year, output_format)
                
                elif report_type == "custom":
                    start_date = self.start_date_var.get()
                    end_date = self.end_date_var.get()
                    result = self.reports_generator.generate_custom_report(
                        start_date, end_date, output_format=output_format
                    )
                
                self.dialog.after(0, lambda: self._on_report_generated(result))
            
            except Exception as e:
                logger.error(f"Error generating report: {e}")
                self.dialog.after(0, lambda: self._on_report_error(str(e)))
        
        thread = Thread(target=generate_task, daemon=True)
        thread.start()
    
    def _on_report_generated(self, result: dict) -> None:
        """Handle report generation completion."""
        self.is_generating = False
        self.progress.stop()
        
        files_generated = []
        if 'pdf' in result:
            files_generated.append(f"PDF: {Path(result['pdf']).name}")
        if 'csv' in result:
            files_generated.append(f"CSV: {Path(result['csv']).name}")
        
        message = "✓ Report generated successfully!\n\n" + "\n".join(files_generated)
        self.status_var.set("✓ Report generated successfully")
        
        messagebox.showinfo("Success", message)
    
    def _on_report_error(self, error: str) -> None:
        """Handle report generation error."""
        self.is_generating = False
        self.progress.stop()
        self.status_var.set("✗ Error generating report")
        
        messagebox.showerror("Error", f"Failed to generate report:\n{error}")
    
    def _open_reports_folder(self) -> None:
        """Open reports folder in file explorer."""
        import subprocess
        import sys
        
        reports_path = self.reports_generator.output_dir
        
        try:
            if sys.platform == 'win32':
                subprocess.Popen(f'explorer "{reports_path}"')
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', str(reports_path)])
            else:
                subprocess.Popen(['xdg-open', str(reports_path)])
        except Exception as e:
            logger.error(f"Error opening folder: {e}")
            messagebox.showerror("Error", f"Failed to open reports folder:\n{e}")

ReportDialog = ModernReportsDialog