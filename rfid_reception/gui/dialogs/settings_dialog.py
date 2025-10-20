"""
Dialog for application settings.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging

logger = logging.getLogger(__name__)


class SettingsDialog:
    """Dialog to manage application settings."""

    def __init__(self, parent: tk.Widget, config, serial_service, on_save_callback):
        self.parent = parent
        self.config = config
        self.serial_service = serial_service
        self.on_save_callback = on_save_callback

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("⚙️ Settings")
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)

        self._create_widgets()

        self.dialog.lift()
        self.dialog.focus_force()

    def _create_widgets(self):
        frame = ttk.Frame(self.dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Serial Port:").pack(pady=5)
        self.port_var = tk.StringVar(value=self.config.get('serial_port', 'COM3'))
        ttk.Entry(frame, textvariable=self.port_var).pack(pady=5)

        ttk.Label(frame, text="Baud Rate:").pack(pady=5)
        self.baud_var = tk.StringVar(value=str(self.config.get('baud_rate', 9600)))
        ttk.Entry(frame, textvariable=self.baud_var).pack(pady=5)

        ttk.Button(frame, text="Save", command=self._save).pack(pady=10)
        ttk.Button(frame, text="Close", command=self.dialog.destroy).pack()

    def _save(self):
        try:
            self.config['serial_port'] = self.port_var.get()
            self.config['baud_rate'] = int(self.baud_var.get())
            # Reconnect serial if needed
            self.serial_service.connect(self.config['serial_port'], self.config['baud_rate'])
            self.on_save_callback()
            messagebox.showinfo("Success", "Settings saved")
            self.dialog.destroy()
        except Exception as e:
            messagebox.showerror("Error", str(e))
