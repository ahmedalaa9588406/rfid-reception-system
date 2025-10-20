"""
Dialog for generating various reports (PDF only).
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from datetime import datetime
from ...reports import ModernReportsGenerator

logger = logging.getLogger(__name__)


class ReportDialog:
    """Dialog to generate PDF reports."""

    def __init__(self, parent: tk.Widget, reports_generator: ModernReportsGenerator):
        self.parent = parent
        self.reports_generator = reports_generator

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("📊 Generate Reports")
        self.dialog.geometry("500x400")
        self.dialog.transient(parent)

        self._create_widgets()

        self.dialog.lift()
        self.dialog.focus_force()

    def _create_widgets(self):
        """Create report generation dialog widgets."""
        frame = ttk.Frame(self.dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)

        # Title
        ttk.Label(frame, text="📊 Report Generator", 
                 font=('Segoe UI', 14, 'bold')).pack(pady=(0, 20))

        # Report Type
        ttk.Label(frame, text="Select Report Type:").pack(anchor=tk.W, pady=(10, 5))
        self.report_type = tk.StringVar(value="daily")
        report_combo = ttk.Combobox(
            frame, 
            textvariable=self.report_type, 
            values=["daily", "weekly", "monthly"],
            state='readonly'
        )
        report_combo.pack(fill=tk.X, pady=(0, 15))

        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=20)

        ttk.Button(
            button_frame, 
            text="✓ Generate PDF", 
            command=self._generate
        ).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(
            button_frame, 
            text="✕ Close", 
            command=self.dialog.destroy
        ).pack(side=tk.LEFT)

    def _generate(self):
        """Generate PDF report."""
        try:
            report_type = self.report_type.get()
            method_name = f"generate_{report_type}_report"
            
            if not hasattr(self.reports_generator, method_name):
                raise ValueError(f"Report type '{report_type}' not supported")
            
            result = getattr(self.reports_generator, method_name)()
            messagebox.showinfo(
                "Success", 
                f"PDF Report generated successfully!\n\nSaved to:\n{result}"
            )
            self.dialog.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate report:\n{str(e)}")
            logger.error(f"Report generation error: {e}", exc_info=True)
