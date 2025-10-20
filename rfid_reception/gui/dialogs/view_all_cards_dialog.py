"""
Modern, feature-rich dialog for viewing and managing all cards in the database.
Includes advanced filtering, sorting, batch operations, and a polished UI.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import logging
from datetime import datetime
from typing import List, Dict, Optional, Callable
from threading import Thread
from enum import Enum
import csv
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class TransactionType(Enum):
    """Transaction type enumeration."""
    TOPUP = "topup"
    READ = "read"


@dataclass
class CardData:
    """Card data model."""
    card_uid: str
    balance: float
    created_at: Optional[datetime]
    last_topped_at: Optional[datetime]
    transaction_count: int = 0


class ModernViewAllCardsDialog:
    """Modern, feature-rich dialog to display and manage all cards in the database."""
    
    # Color scheme - Modern gradient
    PRIMARY_COLOR = "#2E86AB"
    SECONDARY_COLOR = "#A23B72"
    SUCCESS_COLOR = "#06A77D"
    WARNING_COLOR = "#F18F01"
    DANGER_COLOR = "#C1121F"
    NEUTRAL_BG = "#F5F5F5"
    DARK_BG = "#1E1E1E"
    LIGHT_TEXT = "#FFFFFF"
    DARK_TEXT = "#2C3E50"
    BORDER_COLOR = "#E0E0E0"
    
    # Icon Unicode characters
    ICON_SEARCH = "🔍"
    ICON_REFRESH = "🔄"
    ICON_EXPORT = "📊"
    ICON_DELETE = "🗑️"
    ICON_DETAILS = "👁️"
    ICON_SORT = "⬍"
    
    def __init__(self, parent: tk.Widget, db_service, enable_dark_mode: bool = False):
        """
        Initialize the modern cards dialog.
        
        Args:
            parent: Parent window
            db_service: Database service instance
            enable_dark_mode: Enable dark mode theme
        """
        self.parent = parent
        self.db_service = db_service
        self.enable_dark_mode = enable_dark_mode
        
        # Data management
        self.all_cards: List[Dict] = []
        self.filtered_cards: List[Dict] = []
        self.selected_cards: set = set()
        self.is_loading = False
        self.sort_column = "Card UID"
        self.sort_reverse = False
        
        # UI setup
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("📇 Card Manager - Modern Database View")
        self.dialog.geometry("1100x700")
        self.dialog.minsize(900, 600)
        self.dialog.transient(parent)
        
        # Apply modern theme
        self._setup_theme()
        self._create_widgets()
        self._load_cards_async()
        
        self.dialog.lift()
        self.dialog.focus_force()
    
    def _setup_theme(self) -> None:
        """Setup modern theme with colors and fonts."""
        self.style = ttk.Style()
        
        # Try modern theme
        try:
            self.style.theme_use('clam')
        except:
            self.style.theme_use('default')
        
        # Define custom colors
        bg = self.DARK_BG if self.enable_dark_mode else self.NEUTRAL_BG
        fg = self.LIGHT_TEXT if self.enable_dark_mode else self.DARK_TEXT
        
        # Configure styles
        self.style.configure('TLabel', background=bg, foreground=fg)
        self.style.configure('TFrame', background=bg)
        self.style.configure('Header.TLabel', font=('Segoe UI', 16, 'bold'), 
                            background=bg, foreground=fg)
        self.style.configure('Subheader.TLabel', font=('Segoe UI', 11, 'bold'),
                            background=bg, foreground=self.PRIMARY_COLOR)
        self.style.configure('Info.TLabel', font=('Segoe UI', 9),
                            background=bg, foreground='#666666')
        
        # Button styles
        self.style.configure('Primary.TButton', font=('Segoe UI', 10))
        self.style.configure('Accent.TButton', font=('Segoe UI', 10, 'bold'))
        
        self.dialog.configure(bg=bg)
    
    def _create_widgets(self) -> None:
        """Create and layout all dialog widgets."""
        main_frame = ttk.Frame(self.dialog, padding="0")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header section
        self._create_header(main_frame)
        
        # Filter & search section
        self._create_filter_section(main_frame)
        
        # Main content area
        self._create_content_area(main_frame)
        
        # Footer section
        self._create_footer(main_frame)
    
    def _create_header(self, parent: ttk.Frame) -> None:
        """Create header with title and summary."""
        header_frame = ttk.Frame(parent, padding="20")
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        left_frame = ttk.Frame(header_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        title_label = ttk.Label(
            left_frame,
            text="📇 Card Management System",
            style='Header.TLabel'
        )
        title_label.pack(anchor=tk.W)
        
        # Summary stats
        self.summary_var = tk.StringVar(value="Loading data...")
        summary_label = ttk.Label(
            left_frame,
            textvariable=self.summary_var,
            style='Info.TLabel'
        )
        summary_label.pack(anchor=tk.W, pady=(5, 0))
        
        # Right side - loading indicator
        self.loading_var = tk.StringVar(value="")
        loading_label = ttk.Label(
            header_frame,
            textvariable=self.loading_var,
            style='Info.TLabel'
        )
        loading_label.pack(side=tk.RIGHT)
    
    def _create_filter_section(self, parent: ttk.Frame) -> None:
        """Create advanced filter and search section."""
        filter_frame = ttk.LabelFrame(
            parent,
            text=" 🔍 Search & Advanced Filters",
            padding="15"
        )
        filter_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        # Search row
        search_row = ttk.Frame(filter_frame)
        search_row.pack(fill=tk.X, pady=(0, 12))
        
        ttk.Label(search_row, text="Search by UID:").pack(side=tk.LEFT, padx=5)
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self._filter_cards())
        
        search_entry = ttk.Entry(
            search_row,
            textvariable=self.search_var,
            font=('Segoe UI', 10),
            width=30
        )
        search_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Filter options row
        filter_options_row = ttk.Frame(filter_frame)
        filter_options_row.pack(fill=tk.X)
        
        # Min balance filter
        ttk.Label(filter_options_row, text="Min Balance (EGP):").pack(side=tk.LEFT, padx=5)
        self.min_balance_var = tk.DoubleVar(value=0)
        self.min_balance_var.trace('w', lambda *args: self._filter_cards())
        
        min_balance_spin = ttk.Spinbox(
            filter_options_row,
            from_=0,
            to=1000000,
            textvariable=self.min_balance_var,
            width=12,
            font=('Segoe UI', 10)
        )
        min_balance_spin.pack(side=tk.LEFT, padx=5)
        
        # Max balance filter
        ttk.Label(filter_options_row, text="Max Balance (EGP):").pack(side=tk.LEFT, padx=5)
        self.max_balance_var = tk.DoubleVar(value=1000000)
        self.max_balance_var.trace('w', lambda *args: self._filter_cards())
        
        max_balance_spin = ttk.Spinbox(
            filter_options_row,
            from_=0,
            to=1000000,
            textvariable=self.max_balance_var,
            width=12,
            font=('Segoe UI', 10)
        )
        max_balance_spin.pack(side=tk.LEFT, padx=5)
        
        # Action buttons
        button_frame = ttk.Frame(filter_frame)
        button_frame.pack(fill=tk.X, pady=(12, 0))
        
        ttk.Button(
            button_frame,
            text=f"{self.ICON_SEARCH} Search",
            command=self._filter_cards,
            width=15
        ).pack(side=tk.LEFT, padx=3)
        
        ttk.Button(
            button_frame,
            text="Clear Filters",
            command=self._clear_filters,
            width=15
        ).pack(side=tk.LEFT, padx=3)
        
        ttk.Button(
            button_frame,
            text=f"{self.ICON_REFRESH} Refresh",
            command=self._load_cards_async,
            width=15
        ).pack(side=tk.LEFT, padx=3)
    
    def _create_content_area(self, parent: ttk.Frame) -> None:
        """Create main content area with table."""
        content_frame = ttk.Frame(parent, padding="15")
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Table frame with scrollbars
        table_frame = ttk.Frame(content_frame)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbars
        vsb = ttk.Scrollbar(table_frame, orient=tk.VERTICAL)
        hsb = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL)
        
        # Treeview with modern styling
        self.tree = ttk.Treeview(
            table_frame,
            columns=('UID', 'Balance', 'Created', 'Last Top-up', 'Employee', 'Transactions'),
            show='headings',
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set,
            height=15,
            selectmode='extended'
        )
        
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        
        # Configure columns with icons
        self.tree.heading('UID', text=f'💳 Card UID', command=lambda: self._sort_column('UID'))
        self.tree.heading('Balance', text=f'💰 Balance (EGP)', command=lambda: self._sort_column('Balance'))
        self.tree.heading('Created', text=f'📅 Created At', command=lambda: self._sort_column('Created'))
        self.tree.heading('Last Top-up', text=f'⬆️ Last Top-up', command=lambda: self._sort_column('Last Top-up'))
        self.tree.heading('Employee', text=f'👤 Last Employee', command=lambda: self._sort_column('Employee'))
        self.tree.heading('Transactions', text=f'📝 Transactions', command=lambda: self._sort_column('Transactions'))
        
        self.tree.column('UID', width=250, anchor=tk.W)
        self.tree.column('Balance', width=140, anchor=tk.E)
        self.tree.column('Created', width=160, anchor=tk.CENTER)
        self.tree.column('Last Top-up', width=160, anchor=tk.CENTER)
        self.tree.column('Employee', width=120, anchor=tk.W)
        self.tree.column('Transactions', width=120, anchor=tk.CENTER)
        
        # Alternating row colors
        style = ttk.Style()
        style.configure("Treeview", rowheight=28, font=('Segoe UI', 10))
        style.map('Treeview', background=[('selected', self.PRIMARY_COLOR)])
        
        # Bind events
        self.tree.bind('<Double-1>', lambda e: self._show_card_details())
        self.tree.bind('<Delete>', lambda e: self._delete_selected_cards())
        
        # Grid layout
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
    
    def _create_footer(self, parent: ttk.Frame) -> None:
        """Create footer with action buttons."""
        footer_frame = ttk.Frame(parent, padding="15")
        footer_frame.pack(fill=tk.X)
        
        # Left side buttons
        left_buttons = ttk.Frame(footer_frame)
        left_buttons.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(
            left_buttons,
            text=f"{self.ICON_DETAILS} View Details",
            command=self._show_card_details,
            width=18
        ).pack(side=tk.LEFT, padx=3)
        
        ttk.Button(
            left_buttons,
            text=f"{self.ICON_EXPORT} Export to CSV",
            command=self._export_to_csv,
            width=18
        ).pack(side=tk.LEFT, padx=3)
        
        ttk.Button(
            left_buttons,
            text=f"{self.ICON_DELETE} Delete Selected",
            command=self._delete_selected_cards,
            width=18
        ).pack(side=tk.LEFT, padx=3)
        
        # Right side buttons
        right_buttons = ttk.Frame(footer_frame)
        right_buttons.pack(side=tk.RIGHT)
        
        ttk.Button(
            right_buttons,
            text="✕ Close",
            command=self.dialog.destroy,
            width=15
        ).pack(side=tk.LEFT, padx=3)
    
    def _load_cards_async(self) -> None:
        """Load cards asynchronously to prevent UI freezing."""
        self.is_loading = True
        self.loading_var.set("⏳ Loading...")
        
        def load_task():
            try:
                self.all_cards = self.db_service.get_all_cards()
                self.dialog.after(0, self._on_cards_loaded)
            except Exception as e:
                logger.error(f"Error loading cards: {e}")
                self.dialog.after(0, lambda: self._show_error("Failed to load cards", str(e)))
        
        thread = Thread(target=load_task, daemon=True)
        thread.start()
    
    def _on_cards_loaded(self) -> None:
        """Handle cards loaded event."""
        self.is_loading = False
        self.loading_var.set("")
        self.filtered_cards = self.all_cards.copy()
        self._update_display()
        logger.info(f"Loaded {len(self.all_cards)} cards from database")
    
    def _filter_cards(self) -> None:
        """Filter cards based on search and range inputs."""
        search_text = self.search_var.get().lower().strip()
        min_balance = self.min_balance_var.get()
        max_balance = self.max_balance_var.get()
        
        self.filtered_cards = [
            card for card in self.all_cards
            if (not search_text or search_text in card['card_uid'].lower()) and
               (min_balance <= card['balance'] <= max_balance)
        ]
        
        self._update_display()
    
    def _sort_column(self, column: str) -> None:
        """Sort table by column."""
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = False
        
        # Sort logic
        if column == 'UID':
            key = lambda x: x['card_uid']
        elif column == 'Balance':
            key = lambda x: x['balance']
        elif column == 'Created':
            key = lambda x: x['created_at'] or datetime.min
        elif column == 'Last Top-up':
            key = lambda x: x['last_topped_at'] or datetime.min
        elif column == 'Employee':
            # For sorting, get the last employee for each card
            def get_employee(card):
                try:
                    transactions = self.db_service.get_transactions(card_uid=card['card_uid'])
                    return transactions[0]['employee'] if transactions else ''
                except:
                    return ''
            key = get_employee
        elif column == 'Transactions':
            def get_tx_count(card):
                try:
                    return len(self.db_service.get_transactions(card_uid=card['card_uid']))
                except:
                    return 0
            key = get_tx_count
        else:
            return
        
        self.filtered_cards.sort(key=key, reverse=self.sort_reverse)
        self._update_display()
    
    def _update_display(self) -> None:
        """Update the treeview with filtered and sorted cards."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Add filtered cards
        for idx, card in enumerate(self.filtered_cards):
            created_date = card['created_at'].strftime('%Y-%m-%d %H:%M:%S') if card['created_at'] else 'N/A'
            last_topup = card['last_topped_at'].strftime('%Y-%m-%d %H:%M:%S') if card['last_topped_at'] else 'Never'
            
            # Get transaction count and last employee
            try:
                transactions = self.db_service.get_transactions(card_uid=card['card_uid'])
                tx_count = len(transactions)
                last_employee = transactions[0]['employee'] if transactions else 'N/A'
            except:
                tx_count = 0
                last_employee = 'N/A'
            
            # Alternate row colors
            tag = 'oddrow' if idx % 2 == 0 else 'evenrow'
            
            self.tree.insert('', tk.END, values=(
                card['card_uid'],
                f"{card['balance']:.2f}",
                created_date,
                last_topup,
                last_employee,
                tx_count
            ), tags=(tag,))
        
        # Configure row colors
        style = ttk.Style()
        style.configure('oddrow', background=self.NEUTRAL_BG)
        style.configure('evenrow', background='#FFFFFF')
        
        self._update_summary()
    
    def _update_summary(self) -> None:
        """Update summary statistics."""
        total_balance = sum(card['balance'] for card in self.filtered_cards)
        total_cards = len(self.filtered_cards)
        all_cards_count = len(self.all_cards)
        
        if self.search_var.get().strip() or self.min_balance_var.get() > 0 or self.max_balance_var.get() < 1000000:
            summary = f"📊 Showing {total_cards} of {all_cards_count} cards | 💰 Total Balance: {total_balance:,.2f} EGP"
        else:
            summary = f"📊 Total: {total_cards} cards | 💰 Total Balance: {total_balance:,.2f} EGP"
        
        self.summary_var.set(summary)
    
    def _clear_filters(self) -> None:
        """Clear all filters."""
        self.search_var.set("")
        self.min_balance_var.set(0)
        self.max_balance_var.set(1000000)
        self._filter_cards()
    
    def _export_to_csv(self) -> None:
        """Export filtered cards to CSV file with progress."""
        if not self.filtered_cards:
            self._show_warning("No data to export")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"cards_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        
        if not file_path:
            return
        
        self.is_loading = True
        self.loading_var.set("⏳ Exporting...")
        
        def export_task():
            try:
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(["Card UID", "Balance (EGP)", "Created At", "Last Top-up", "Last Employee", "Transaction Count"])
                    
                    for card in self.filtered_cards:
                        created_date = card['created_at'].strftime('%Y-%m-%d %H:%M:%S') if card['created_at'] else 'N/A'
                        last_topup = card['last_topped_at'].strftime('%Y-%m-%d %H:%M:%S') if card['last_topped_at'] else 'Never'
                        
                        try:
                            transactions = self.db_service.get_transactions(card_uid=card['card_uid'])
                            tx_count = len(transactions)
                            last_employee = transactions[0]['employee'] if transactions else 'N/A'
                        except:
                            tx_count = 0
                            last_employee = 'N/A'
                        
                        writer.writerow([card['card_uid'], f"{card['balance']:.2f}", created_date, last_topup, last_employee, tx_count])
                
                self.dialog.after(0, lambda: self._show_success(f"Data exported successfully to:\n{file_path}"))
                logger.info(f"Cards exported to {file_path}")
            except Exception as e:
                logger.error(f"Error exporting to CSV: {e}")
                self.dialog.after(0, lambda: self._show_error("Export Failed", str(e)))
            finally:
                self.is_loading = False
                self.dialog.after(0, lambda: self.loading_var.set(""))
        
        thread = Thread(target=export_task, daemon=True)
        thread.start()
    
    def _delete_selected_cards(self) -> None:
        """Delete selected cards after confirmation."""
        selection = self.tree.selection()
        if not selection:
            self._show_warning("Please select cards to delete")
            return
        
        if messagebox.askyesno("Confirm Deletion", f"Delete {len(selection)} card(s)? This cannot be undone!"):
            self.is_loading = True
            self.loading_var.set("⏳ Deleting...")
            
            def delete_task():
                deleted_count = 0
                for item in selection:
                    try:
                        values = self.tree.item(item)['values']
                        card_uid = values[0]
                        self.db_service.delete_card(card_uid)
                        deleted_count += 1
                    except Exception as e:
                        logger.error(f"Error deleting card: {e}")
                
                self.dialog.after(0, self._load_cards_async)
                self.dialog.after(0, lambda: self._show_success(f"Deleted {deleted_count} card(s) successfully"))
            
            thread = Thread(target=delete_task, daemon=True)
            thread.start()
    
    def _show_error(self, title: str, message: str) -> None:
        """Show modern error dialog."""
        messagebox.showerror(title, message)
    
    def _show_warning(self, message: str) -> None:
        """Show modern warning dialog."""
        messagebox.showwarning("⚠️ Warning", message)
    
    def _show_success(self, message: str) -> None:
        """Show modern success dialog."""
        messagebox.showinfo("✓ Success", message)
    
    def _show_card_details(self) -> None:
        """Show detailed information for selected card in a modern window."""
        selection = self.tree.selection()
        if not selection:
            self._show_warning("Please select a card to view details")
            return
        
        item = selection[0]
        values = self.tree.item(item)['values']
        
        # Ensure card_uid is treated as a string
        card_uid = str(values[0]) if values else ""
        
        logger.debug(f"Looking for card with UID: '{card_uid}'")
        
        # More robust card lookup with normalization
        card = None
        
        # First try exact match
        card = next((c for c in self.filtered_cards if str(c['card_uid']) == card_uid), None)
        
        # If not found, try case-insensitive match with whitespace stripped
        if not card:
            normalized_uid = str(card_uid).strip().lower()
            card = next((c for c in self.filtered_cards 
                        if str(c['card_uid']).strip().lower() == normalized_uid), None)
        
        # If still not found, try searching in all cards as fallback
        if not card:
            logger.debug("Card not found in filtered cards, trying all cards")
            card = next((c for c in self.all_cards if str(c['card_uid']) == card_uid), None)
            if not card:
                normalized_uid = str(card_uid).strip().lower()
                card = next((c for c in self.all_cards 
                            if str(c['card_uid']).strip().lower() == normalized_uid), None)
        
        if not card:
            logger.error(f"Card not found: '{card_uid}'")
            available_uids = [str(c['card_uid']) for c in self.filtered_cards[:5]]
            self._show_error(
                "Card Not Found", 
                f"Could not find card with UID: '{card_uid}'\n\n"
                f"First few available cards: {available_uids}\n\n"
                "This could be due to filtering or database synchronization issues."
            )
            return
        
        logger.info(f"Found card: {card['card_uid']} with balance: {card['balance']}")
        
        # Fetch transactions
        try:
            transactions = self.db_service.get_transactions(card_uid=card['card_uid'])
        except Exception as e:
            logger.error(f"Error fetching transactions: {e}")
            transactions = []
        
        # Show the details window instead of exporting to a file
        self._create_details_window(card, transactions)
    
    def _create_details_window(self, card: Dict, transactions: List[Dict]) -> None:
        """Create a modern details window to display card information."""
        details_window = tk.Toplevel(self.dialog)
        details_window.title(f"Card Details - {card['card_uid']}")
        details_window.geometry("800x600")
        details_window.minsize(700, 500)
        details_window.transient(self.dialog)
        details_window.focus_force()
        
        # Apply theme to match main window
        bg = self.DARK_BG if self.enable_dark_mode else self.NEUTRAL_BG
        fg = self.LIGHT_TEXT if self.enable_dark_mode else self.DARK_TEXT
        details_window.configure(bg=bg)
        
        # Main content frame with padding
        main_frame = ttk.Frame(details_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header section
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Card icon and title
        title_label = ttk.Label(
            header_frame,
            text=f"💳 Card Details",
            font=('Segoe UI', 18, 'bold'),
            foreground=self.PRIMARY_COLOR
        )
        title_label.pack(anchor=tk.W)
        
        subtitle_label = ttk.Label(
            header_frame,
            text=f"UID: {card['card_uid']}",
            font=('Segoe UI', 10),
            foreground=self.SECONDARY_COLOR
        )
        subtitle_label.pack(anchor=tk.W)
        
        # Card info section with gradient background
        info_frame = ttk.LabelFrame(
            main_frame, 
            text=" Card Information ", 
            padding="15"
        )
        info_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Balance - displayed prominently
        balance_frame = ttk.Frame(info_frame)
        balance_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(
            balance_frame,
            text="Current Balance:",
            font=('Segoe UI', 12, 'bold')
        ).pack(side=tk.LEFT)
        
        ttk.Label(
            balance_frame,
            text=f"{card['balance']:.2f} EGP",
            font=('Segoe UI', 14, 'bold'),
            foreground=self.SUCCESS_COLOR
        ).pack(side=tk.LEFT, padx=10)
        
        # Other card details
        details_frame = ttk.Frame(info_frame)
        details_frame.pack(fill=tk.X)
        
        # Left column
        left_col = ttk.Frame(details_frame)
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Create date field
        date_frame = ttk.Frame(left_col)
        date_frame.pack(fill=tk.X, pady=5)
        ttk.Label(date_frame, text="Created:", width=12).pack(side=tk.LEFT)
        ttk.Label(
            date_frame,
            text=card['created_at'].strftime('%Y-%m-%d %H:%M:%S') if card['created_at'] else 'N/A',
        ).pack(side=tk.LEFT)
        
        # Last top-up field
        topup_frame = ttk.Frame(left_col)
        topup_frame.pack(fill=tk.X, pady=5)
        ttk.Label(topup_frame, text="Last Top-up:", width=12).pack(side=tk.LEFT)
        ttk.Label(
            topup_frame,
            text=card['last_topped_at'].strftime('%Y-%m-%d %H:%M:%S') if card['last_topped_at'] else 'Never',
        ).pack(side=tk.LEFT)
        
        # Right column
        right_col = ttk.Frame(details_frame)
        right_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Last employee field
        if transactions:
            employee_frame = ttk.Frame(right_col)
            employee_frame.pack(fill=tk.X, pady=5)
            ttk.Label(employee_frame, text="Last Employee:", width=12).pack(side=tk.LEFT)
            ttk.Label(
                employee_frame,
                text=transactions[0]['employee'] or 'N/A',
            ).pack(side=tk.LEFT)
        
        # Transaction count field
        tx_count_frame = ttk.Frame(right_col)
        tx_count_frame.pack(fill=tk.X, pady=5)
        ttk.Label(tx_count_frame, text="Transactions:", width=12).pack(side=tk.LEFT)
        ttk.Label(
            tx_count_frame,
            text=str(len(transactions)),
        ).pack(side=tk.LEFT)
        
        # Transactions section
        tx_frame = ttk.LabelFrame(main_frame, text=f" Transaction History ({len(transactions)}) ", padding="15")
        tx_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create transactions table
        tx_table_frame = ttk.Frame(tx_frame)
        tx_table_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbars
        vsb = ttk.Scrollbar(tx_table_frame, orient=tk.VERTICAL)
        hsb = ttk.Scrollbar(tx_table_frame, orient=tk.HORIZONTAL)
        
        # Transaction treeview
        tx_tree = ttk.Treeview(
            tx_table_frame,
            columns=('Type', 'Amount', 'Balance', 'Employee', 'Timestamp'),
            show='headings',
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set,
            height=10
        )
        
        vsb.config(command=tx_tree.yview)
        hsb.config(command=tx_tree.xview)
        
        # Configure columns
        tx_tree.heading('Type', text='Transaction Type')
        tx_tree.heading('Amount', text='Amount (EGP)')
        tx_tree.heading('Balance', text='Balance After (EGP)')
        tx_tree.heading('Employee', text='Employee')
        tx_tree.heading('Timestamp', text='Timestamp')
        
        tx_tree.column('Type', width=120, anchor=tk.CENTER)
        tx_tree.column('Amount', width=100, anchor=tk.E)
        tx_tree.column('Balance', width=120, anchor=tk.E)
        tx_tree.column('Employee', width=150, anchor=tk.W)
        tx_tree.column('Timestamp', width=160, anchor=tk.CENTER)
        
        # Add transaction data
        for idx, tx in enumerate(transactions):
            tx_type = "TOP-UP" if tx['type'] == 'topup' else "READ"
            icon = "⬆️" if tx['type'] == 'topup' else "📖"
            tag = 'topup' if tx['type'] == 'topup' else 'read'
            
            tx_tree.insert('', tk.END, values=(
                f"{icon} {tx_type}",
                f"{tx['amount']:.2f}",
                f"{tx['balance_after']:.2f}",
                tx['employee'] or 'N/A',
                tx['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
            ), tags=(tag,))
        
        # Configure transaction row colors
        tx_tree.tag_configure('topup', background='#E8F5E9')  # Light green for topups
        tx_tree.tag_configure('read', background='#E3F2FD')   # Light blue for reads
        
        # Layout with scrollbars
        tx_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        tx_table_frame.grid_rowconfigure(0, weight=1)
        tx_table_frame.grid_columnconfigure(0, weight=1)
        
        # Footer with action buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(15, 0))
        
        # Export button
        ttk.Button(
            button_frame,
            text=f"{self.ICON_EXPORT} Export Details",
            command=lambda: self._export_card_details_to_file(card, transactions)
        ).pack(side=tk.LEFT)
        
        # Delete button
        ttk.Button(
            button_frame,
            text=f"{self.ICON_DELETE} Delete Card",
            command=lambda: self._delete_card_from_details(card['card_uid'], details_window),
            style='Accent.TButton'
        ).pack(side=tk.LEFT, padx=10)
        
        # Close button
        ttk.Button(
            button_frame,
            text="Close",
            command=details_window.destroy
        ).pack(side=tk.RIGHT)
    
    def _delete_card_from_details(self, card_uid: str, details_window: tk.Toplevel) -> None:
        """Delete the card from the details window."""
        if messagebox.askyesno("Confirm Deletion", f"Delete card '{card_uid}' and all its transactions?\nThis cannot be undone!"):
            try:
                self.db_service.delete_card(card_uid)
                messagebox.showinfo("Success", f"Card '{card_uid}' deleted successfully")
                details_window.destroy()
                # Refresh the main dialog
                self._load_cards_async()
                logger.info(f"Card {card_uid} deleted from details window")
            except Exception as e:
                logger.error(f"Error deleting card {card_uid}: {e}")
                messagebox.showerror("Error", f"Failed to delete card: {e}")