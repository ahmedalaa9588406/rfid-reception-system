"""
Dialog for generating various reports.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from datetime import datetime
from ...reports import ModernReportsGenerator

logger = logging.getLogger(__name__)


class ReportDialog:
    """Dialog to generate reports."""

    def __init__(self, parent: tk.Widget, reports_generator: ModernReportsGenerator):
        self.parent = parent
        self.reports_generator = reports_generator

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("📊 Generate Reports")
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)

        self._create_widgets()

        self.dialog.lift()
        self.dialog.focus_force()

    def _create_widgets(self):
        frame = ttk.Frame(self.dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Select Report Type:").pack(pady=5)

        self.report_type = tk.StringVar(value="daily")
        ttk.Combobox(frame, textvariable=self.report_type, values=["daily", "weekly", "monthly"]).pack(pady=5)

        ttk.Label(frame, text="Output Format:").pack(pady=5)
        self.format = tk.StringVar(value="both")
        ttk.Combobox(frame, textvariable=self.format, values=["csv", "pdf", "both"]).pack(pady=5)

        ttk.Button(frame, text="Generate", command=self._generate).pack(pady=10)
        ttk.Button(frame, text="Close", command=self.dialog.destroy).pack()

    def _generate(self):
        try:
            result = getattr(self.reports_generator, f"generate_{self.report_type.get()}_report")(output_format=self.format.get())
            messagebox.showinfo("Success", f"Report generated: {result}")
        except Exception as e:
            messagebox.showerror("Error", str(e))
