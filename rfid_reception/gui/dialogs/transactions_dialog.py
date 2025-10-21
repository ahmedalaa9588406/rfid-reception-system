"""
Dialog for viewing and managing all transactions in the database.
Includes filtering, sorting, and export functionality.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import logging
from datetime import datetime
from typing import List, Dict, Optional
from threading import Thread
from ...reports import ModernReportsGenerator

logger = logging.getLogger(__name__)


class TransactionsDialog:
    """Dialog to display and manage all transactions in the database."""

    PRIMARY_COLOR = "#2E86AB"
    SECONDARY_COLOR = "#A23B72"
    SUCCESS_COLOR = "#06A77D"
    WARNING_COLOR = "#F18F01"
    DANGER_COLOR = "#C1121F"
    NEUTRAL_BG = "#F5F5F5"
    DARK_BG = "#1E1E1E"
    LIGHT_TEXT = "#FFFFFF"
    DARK_TEXT = "#2C3E50"

    ICON_SEARCH = "🔍"
    ICON_REFRESH = "🔄"
    ICON_EXPORT = "📊"
    ICON_DELETE = "🗑️"

    def __init__(self, parent: tk.Widget, db_service, enable_dark_mode: bool = False):
        self.parent = parent
        self.db_service = db_service
        self.enable_dark_mode = enable_dark_mode
        self.reports_generator = ModernReportsGenerator(self.db_service)

        self.all_transactions: List[Dict] = []
        self.filtered_transactions: List[Dict] = []
        self.is_loading = False
        self.sort_column = "Timestamp"
        self.sort_reverse = False

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("📊 Transactions Manager")
        self.dialog.geometry("1200x700")
        self.dialog.minsize(1000, 600)
        self.dialog.transient(parent)

        self._setup_theme()
        self._create_widgets()
        self._load_transactions_async()

        self.dialog.lift()
        self.dialog.focus_force()

    def _setup_theme(self):
        self.style = ttk.Style()
        try:
            self.style.theme_use('clam')
        except:
            self.style.theme_use('default')

        bg = self.DARK_BG if self.enable_dark_mode else self.NEUTRAL_BG
        fg = self.LIGHT_TEXT if self.enable_dark_mode else self.DARK_TEXT

        self.style.configure('TLabel', background=bg, foreground=fg)
        self.style.configure('TFrame', background=bg)
        self.style.configure('Header.TLabel', font=('Segoe UI', 16, 'bold'), background=bg, foreground=fg)
        self.style.configure('Subheader.TLabel', font=('Segoe UI', 11, 'bold'), background=bg, foreground=self.PRIMARY_COLOR)
        self.style.configure('Info.TLabel', font=('Segoe UI', 9), background=bg, foreground='#666666')

        self.dialog.configure(bg=bg)

    def _create_widgets(self):
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        title_label = ttk.Label(header_frame, text="📊 Transactions Manager", style='Header.TLabel')
        title_label.pack(anchor=tk.W)

        self.summary_var = tk.StringVar(value="Loading data...")
        summary_label = ttk.Label(header_frame, textvariable=self.summary_var, style='Info.TLabel')
        summary_label.pack(anchor=tk.W, pady=(5, 0))

        self.loading_var = tk.StringVar(value="")
        loading_label = ttk.Label(header_frame, textvariable=self.loading_var, style='Info.TLabel')
        loading_label.pack(side=tk.RIGHT)

        # Filter section
        filter_frame = ttk.LabelFrame(main_frame, text=" 🔍 Filters", padding="10")
        filter_frame.pack(fill=tk.X, pady=(0, 10))

        # Filters: Card UID, Type, Date Range, Employee
        ttk.Label(filter_frame, text="Card UID:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.card_uid_var = tk.StringVar()
        ttk.Entry(filter_frame, textvariable=self.card_uid_var).grid(row=0, column=1, padx=5)

        ttk.Label(filter_frame, text="Type:").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.type_var = tk.StringVar(value="All")
        ttk.Combobox(filter_frame, textvariable=self.type_var, values=["All", "topup", "read"]).grid(row=0, column=3, padx=5)

        ttk.Label(filter_frame, text="Employee:").grid(row=1, column=0, sticky=tk.W, padx=5)
        self.employee_var = tk.StringVar()
        ttk.Entry(filter_frame, textvariable=self.employee_var).grid(row=1, column=1, padx=5)

        ttk.Button(filter_frame, text=f"{self.ICON_SEARCH} Apply Filters", command=self._apply_filters).grid(row=1, column=2, padx=5)
        ttk.Button(filter_frame, text="Clear Filters", command=self._clear_filters).grid(row=1, column=3, padx=5)

        # Content area
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)

        self.tree = ttk.Treeview(content_frame, columns=('ID', 'Card UID', 'Type', 'Amount', 'Balance After', 'Employee', 'Timestamp'), show='headings', height=20)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(content_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        for col in [('ID', 50), ('Card UID', 200), ('Type', 80), ('Amount', 100), ('Balance After', 120), ('Employee', 150), ('Timestamp', 160)]:
            self.tree.heading(col[0], text=col[0], command=lambda c=col[0]: self._sort_column(c))
            self.tree.column(col[0], width=col[1])

        # Footer
        footer_frame = ttk.Frame(main_frame)
        footer_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(footer_frame, text=f"{self.ICON_EXPORT} Export to CSV", command=self._export_to_csv).pack(side=tk.LEFT, padx=5)
        ttk.Button(footer_frame, text=f"{self.ICON_EXPORT} Export to PDF", command=self._export_to_pdf).pack(side=tk.LEFT, padx=5)
        ttk.Button(footer_frame, text="Close", command=self.dialog.destroy).pack(side=tk.RIGHT, padx=5)

    def _load_transactions_async(self):
        self.is_loading = True
        self.loading_var.set("⏳ Loading...")

        def load_task():
            try:
                self.all_transactions = self.db_service.get_all_transactions()
                self.dialog.after(0, self._on_transactions_loaded)
            except Exception as e:
                logger.error(f"Error loading transactions: {e}")
                self.dialog.after(0, lambda: self._show_error("Failed to load transactions", str(e)))

        Thread(target=load_task, daemon=True).start()

    def _on_transactions_loaded(self):
        self.is_loading = False
        self.loading_var.set("")
        self.filtered_transactions = self.all_transactions.copy()
        self._update_display()

    def _apply_filters(self):
        card_uid = self.card_uid_var.get().strip().lower()
        tx_type = self.type_var.get()
        employee = self.employee_var.get().strip().lower()

        self.filtered_transactions = [
            tx for tx in self.all_transactions
            if (not card_uid or card_uid in tx['card_uid'].lower()) and
               (tx_type == "All" or tx['type'] == tx_type) and
               (not employee or employee in (tx.get('employee') or '').lower())
        ]
        self._update_display()

    def _clear_filters(self):
        self.card_uid_var.set("")
        self.type_var.set("All")
        self.employee_var.set("")
        self._apply_filters()

    def _sort_column(self, column):
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = False

        key_func = {
            'ID': lambda x: x.get('id', 0),
            'Card UID': lambda x: x['card_uid'],
            'Type': lambda x: x['type'],
            'Amount': lambda x: x['amount'],
            'Balance After': lambda x: x['balance_after'],
            'Employee': lambda x: x.get('employee', ''),
            'Timestamp': lambda x: x['timestamp']
        }.get(column, lambda x: x['timestamp'])

        self.filtered_transactions.sort(key=key_func, reverse=self.sort_reverse)
        self._update_display()

    def _update_display(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for tx in self.filtered_transactions:
            self.tree.insert('', tk.END, values=(
                tx.get('id', ''),
                tx['card_uid'],
                tx['type'],
                f"{tx['amount']:.2f}",
                f"{tx['balance_after']:.2f}",
                tx.get('employee', 'N/A'),
                tx['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
            ))

        self.summary_var.set(f"Showing {len(self.filtered_transactions)} of {len(self.all_transactions)} transactions")

    def _export_to_csv(self):
        if not self.filtered_transactions:
            self._show_warning("No data to export")
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if not file_path:
            return

        try:
            with open(file_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['ID', 'Card UID', 'Type', 'Amount', 'Balance After', 'Employee', 'Timestamp'])
                for tx in self.filtered_transactions:
                    writer.writerow([
                        tx.get('id', ''),
                        tx['card_uid'],
                        tx['type'],
                        tx['amount'],
                        tx['balance_after'],
                        tx.get('employee', ''),
                        tx['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                    ])
            self._show_success(f"Exported to {file_path}")
        except Exception as e:
            self._show_error("Export Failed", str(e))

    def _export_to_pdf(self):
        if not self.filtered_transactions:
            self._show_warning("No data to export")
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
        if not file_path:
            return

        try:
            self.reports_generator.generate_custom_report(
                start_date=min(tx['timestamp'] for tx in self.filtered_transactions),
                end_date=max(tx['timestamp'] for tx in self.filtered_transactions),
                output_format='pdf'
            )
            self._show_success(f"PDF generated")
        except Exception as e:
            self._show_error("Export Failed", str(e))

    def _show_error(self, title, message):
        messagebox.showerror(title, message)

    def _show_warning(self, message):
        messagebox.showwarning("Warning", message)

    def _show_success(self, message):
        messagebox.showinfo("Success", message)
