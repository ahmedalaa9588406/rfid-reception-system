"""Main GUI window for RFID Reception System with modern design."""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import logging
import os
from datetime import datetime, timedelta
from rfid_reception.reports import ModernReportsGenerator
from rfid_reception.services.receipt_printer import ReceiptPrinter

logger = logging.getLogger(__name__)

# Modern color palette
PRIMARY_COLOR = "#2E86AB"
SECONDARY_COLOR = "#A23B72"
SUCCESS_COLOR = "#06A77D"
WARNING_COLOR = "#F18F01"
DANGER_COLOR = "#C1121F"
LIGHT_BG = "#F5F5F5"
CARD_BG = "#FFFFFF"
TEXT_PRIMARY = "#2C3E50"
TEXT_SECONDARY = "#555555"
BORDER_COLOR = "#E0E0E0"


class ModernMainWindow:
    """Modern main application window with enhanced UI."""

    def __init__(self, root, db_service, serial_service, reports_generator, scheduler, config):
        """Initialize the modern main window."""
        self.root = root
        self.db_service = db_service
        self.serial_service = serial_service
        self.reports_generator = reports_generator
        self.scheduler = scheduler
        self.config = config
        
        # Initialize receipt printer
        company_name = config.get('company_name', 'RFID Reception System')
        company_info = {
            'address': config.get('company_address', ''),
            'phone': config.get('company_phone', '')
        }
        self.receipt_printer = ReceiptPrinter(company_name, company_info)
        self.auto_print_receipts = config.get('auto_print_receipts', True)

        self.root.title("RFID Reception System")
        self.root.geometry("1100x750")
        self.root.minsize(900, 600)
        self.root.configure(bg=LIGHT_BG)

        # Set application icon
        try:
            icon_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'images', 'images.ico')
            self.icon = tk.PhotoImage(file=icon_path)
            self.root.iconphoto(True, self.icon)
        except tk.TclError:
            # Icon file not found, continue without icon
            pass

        self.current_card_uid = None
        self.current_balance = 0.0
        self.manual_mode = False
        self.auto_scan_enabled = False
        self.auto_scan_job = None
        self.last_scanned_uid = None

        self._setup_styles()
        self._create_widgets()
        self._check_serial_connection()

    def _setup_styles(self):
        """Configure modern ttk styles."""
        style = ttk.Style()
        style.theme_use('clam')

        # Modern button styles
        style.configure('Primary.TButton',
                       font=('Segoe UI', 10, 'bold'),
                       padding=10)
        style.map('Primary.TButton',
                 background=[('active', SECONDARY_COLOR)])

        style.configure('Success.TButton',
                       font=('Segoe UI', 10, 'bold'),
                       padding=10)

        style.configure('TLabel', font=('Segoe UI', 10), background=LIGHT_BG)
        style.configure('Header.TLabel', font=('Segoe UI', 24, 'bold'), background=PRIMARY_COLOR, foreground='white')
        style.configure('Title.TLabel', font=('Segoe UI', 14, 'bold'), background=LIGHT_BG, foreground=TEXT_PRIMARY)
        style.configure('Subtitle.TLabel', font=('Segoe UI', 11), background=LIGHT_BG, foreground=TEXT_SECONDARY)

    def _create_widgets(self):
        """Create and layout all widgets with modern design."""
        # Header banner
        self._create_header()

        # Main content area
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        # Left panel - Card operations
        left_panel = tk.Frame(main_container, bg=CARD_BG, relief='flat', bd=1)
        left_panel.configure(highlightbackground=BORDER_COLOR, highlightthickness=1)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=15, pady=15)

        self._create_card_panel(left_panel)

        # Right panel - Quick actions
        right_panel = tk.Frame(main_container, bg=CARD_BG, relief='flat', bd=1)
        right_panel.configure(highlightbackground=BORDER_COLOR, highlightthickness=1)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(0, 15), pady=15)

        self._create_actions_panel(right_panel)

        # Footer status bar
        self._create_footer()

    def _create_header(self):
        """Create attractive header section."""
        header_frame = tk.Frame(self.root, bg=PRIMARY_COLOR, height=100)
        header_frame.pack(fill='x', side='top')
        header_frame.pack_propagate(False)

        # Header content
        header_content = tk.Frame(header_frame, bg=PRIMARY_COLOR)
        header_content.pack(fill='both', expand=True, padx=20, pady=15)

        # Title with icon
        title_label = tk.Label(header_content,
                              text="🎫 RFID Reception System",
                              font=('Segoe UI', 22, 'bold'),
                              fg='white',
                              bg=PRIMARY_COLOR)
        title_label.pack(side='left', anchor='w')

        # Status indicator
        self.status_indicator = tk.Label(header_content,
                                        text="● Disconnected",
                                        font=('Segoe UI', 11, 'bold'),
                                        fg=DANGER_COLOR,
                                        bg=PRIMARY_COLOR)
        self.status_indicator.pack(side='right', anchor='e')

    def _create_card_panel(self, parent):
        """Create card reading and top-up panel."""
        # Title
        title = tk.Label(parent,
                        text="💳 Card Operations",
                        font=('Segoe UI', 14, 'bold'),
                        fg=PRIMARY_COLOR,
                        bg=CARD_BG)
        title.pack(padx=15, pady=(15, 10), anchor='w')

        # Separator
        separator = ttk.Separator(parent, orient='horizontal')
        separator.pack(fill='x', padx=15, pady=(0, 15))

        # Card UID section
        self._create_info_section(parent, "📋 Card UID", "self.card_uid_var", "No card detected")

        # Balance section
        self._create_balance_section(parent)

        # Button frame for Read Card and Auto-Scan toggle
        btn_frame = tk.Frame(parent, bg=CARD_BG)
        btn_frame.pack(padx=15, pady=15, fill='x')
        
        # Read Card button
        read_btn = tk.Button(btn_frame,
                            text="🔍 Read Card",
                            font=('Segoe UI', 12, 'bold'),
                            bg=PRIMARY_COLOR,
                            fg='white',
                            relief='flat',
                            cursor='hand2',
                            padx=20,
                            pady=12,
                            command=self._read_card)
        read_btn.pack(side='left', fill='x', expand=True, padx=(0, 5))
        
        # Auto-Scan Toggle button
        self.auto_scan_btn = tk.Button(btn_frame,
                                      text="⚡ Enable Auto-Scan",
                                      font=('Segoe UI', 10, 'bold'),
                                      bg=SUCCESS_COLOR,
                                      fg='white',
                                      relief='flat',
                                      cursor='hand2',
                                      padx=15,
                                      pady=12,
                                      command=self._toggle_auto_scan)
        self.auto_scan_btn.pack(side='left', fill='x', expand=True, padx=(5, 0))

        # Spacer
        spacer = ttk.Frame(parent, height=20)
        spacer.pack()

        # Top-Up section separator
        sep2 = ttk.Separator(parent, orient='horizontal')
        sep2.pack(fill='x', padx=15, pady=10)

        # Top-Up amount section
        topup_label = tk.Label(parent,
                              text="💰 Top-Up Amount / Write Data",
                              font=('Segoe UI', 12, 'bold'),
                              fg=PRIMARY_COLOR,
                              bg=CARD_BG)
        topup_label.pack(padx=15, pady=(10, 5), anchor='w')
        
        # Instruction label
        instruction_label = tk.Label(parent,
                                    text="Enter: 50 (number) | K50 (K-amount) | Ahmed (text) - Max 11 chars",
                                    font=('Segoe UI', 8),
                                    fg=TEXT_SECONDARY,
                                    bg=CARD_BG)
        instruction_label.pack(padx=15, pady=(0, 5), anchor='w')

        # Amount input with EGP label
        amount_frame = tk.Frame(parent, bg=CARD_BG)
        amount_frame.pack(padx=15, pady=5, fill='x')

        self.amount_var = tk.StringVar()
        amount_entry = tk.Entry(amount_frame,
                               textvariable=self.amount_var,
                               font=('Segoe UI', 14, 'bold'),
                               relief='flat',
                               bd=1,
                               width=15)
        amount_entry.configure(highlightbackground=BORDER_COLOR, highlightthickness=1)
        amount_entry.pack(side='left', fill='x', expand=True, ipady=8)

        egp_label = tk.Label(amount_frame,
                            text=" EGP",
                            font=('Segoe UI', 12, 'bold'),
                            fg=TEXT_SECONDARY,
                            bg=CARD_BG)
        egp_label.pack(side='left', padx=10)

        # Quick amount buttons
        quick_frame = tk.Frame(parent, bg=CARD_BG)
        quick_frame.pack(padx=15, pady=10, fill='x')

        quick_label = tk.Label(quick_frame,
                              text="Quick Amounts:",
                              font=('Segoe UI', 9),
                              fg=TEXT_SECONDARY,
                              bg=CARD_BG)
        quick_label.pack(anchor='w', pady=(0, 5))

        amounts_button_frame = tk.Frame(quick_frame, bg=CARD_BG)
        amounts_button_frame.pack(fill='x')

        amounts = [10, 20, 50, 100]
        for amount in amounts:
            btn = tk.Button(amounts_button_frame,
                           text=f"{amount} EGP",
                           font=('Segoe UI', 9, 'bold'),
                           bg=LIGHT_BG,
                           fg=TEXT_PRIMARY,
                           relief='flat',
                           cursor='hand2',
                           padx=10,
                           pady=6,
                           command=lambda a=amount: self.amount_var.set(str(a)))
            btn.pack(side='left', padx=3, fill='x', expand=True)

        # Buttons frame
        buttons_frame = tk.Frame(parent, bg=CARD_BG)
        buttons_frame.pack(padx=15, pady=10, fill='x')
        
        # Top-Up button
        topup_btn = tk.Button(buttons_frame,
                             text="✓ Add to Balance",
                             font=('Segoe UI', 11, 'bold'),
                             bg=SUCCESS_COLOR,
                             fg='white',
                             relief='flat',
                             cursor='hand2',
                             padx=15,
                             pady=10,
                             command=self._top_up)
        topup_btn.pack(side='left', fill='x', expand=True, padx=(0, 5))
        
        # Write Balance button (sets exact amount)
        write_btn = tk.Button(buttons_frame,
                             text="✍ Set Balance",
                             font=('Segoe UI', 11, 'bold'),
                             bg=SECONDARY_COLOR,
                             fg='white',
                             relief='flat',
                             cursor='hand2',
                             padx=15,
                             pady=10,
                             command=self._write_balance)
        write_btn.pack(side='right', fill='x', expand=True, padx=(5, 0))

        # Manual mode section
        sep3 = ttk.Separator(parent, orient='horizontal')
        sep3.pack(fill='x', padx=15, pady=10)

        manual_label = tk.Label(parent,
                               text="⚙ Manual Mode",
                               font=('Segoe UI', 11, 'bold'),
                               fg=WARNING_COLOR,
                               bg=CARD_BG)
        manual_label.pack(padx=15, pady=(10, 5), anchor='w')

        self.manual_mode_var = tk.BooleanVar()
        manual_check = tk.Checkbutton(parent,
                                     text="Enable Manual Card Entry",
                                     variable=self.manual_mode_var,
                                     font=('Segoe UI', 10),
                                     bg=CARD_BG,
                                     fg=TEXT_PRIMARY,
                                     command=self._toggle_manual_mode)
        manual_check.pack(padx=15, pady=5, anchor='w')

        # Manual UID entry
        self.manual_uid_var = tk.StringVar()
        manual_uid_entry = tk.Entry(parent,
                                   textvariable=self.manual_uid_var,
                                   font=('Segoe UI', 10),
                                   relief='flat',
                                   bd=1,
                                   state='disabled')
        manual_uid_entry.configure(highlightbackground=BORDER_COLOR, highlightthickness=1)
        manual_uid_entry.pack(padx=15, pady=5, fill='x', ipady=6)
        self.manual_uid_entry = manual_uid_entry

        self.manual_load_btn = tk.Button(parent,
                                        text="Load Card UID",
                                        font=('Segoe UI', 10, 'bold'),
                                        bg=WARNING_COLOR,
                                        fg='white',
                                        relief='flat',
                                        cursor='hand2',
                                        state='disabled',
                                        padx=10,
                                        pady=8,
                                        command=self._load_manual_card)
        self.manual_load_btn.pack(padx=15, pady=10, fill='x')

    def _create_balance_section(self, parent):
        """Create balance display section."""
        balance_frame = tk.Frame(parent, bg=SUCCESS_COLOR, relief='flat', bd=0)
        balance_frame.pack(padx=15, pady=10, fill='x', ipady=12)

        balance_label = tk.Label(balance_frame,
                                text="💵 Current Balance",
                                font=('Segoe UI', 10),
                                fg='white',
                                bg=SUCCESS_COLOR)
        balance_label.pack(anchor='w', padx=12, pady=(0, 5))

        self.balance_var = tk.StringVar(value="0.00 EGP")
        balance_value = tk.Label(balance_frame,
                                textvariable=self.balance_var,
                                font=('Segoe UI', 20, 'bold'),
                                fg='white',
                                bg=SUCCESS_COLOR)
        balance_value.pack(anchor='w', padx=12)

    def _create_info_section(self, parent, title, var_name, default_value):
        """Create an information display section."""
        info_frame = tk.Frame(parent, bg=CARD_BG)
        info_frame.pack(padx=15, pady=5, fill='x')

        label = tk.Label(info_frame,
                        text=title,
                        font=('Segoe UI', 10),
                        fg=TEXT_SECONDARY,
                        bg=CARD_BG)
        label.pack(anchor='w')

        var = tk.StringVar(value=default_value)
        setattr(self, var_name.split('.')[-1], var)

        value = tk.Label(info_frame,
                        textvariable=var,
                        font=('Segoe UI', 11, 'bold'),
                        fg=TEXT_PRIMARY,
                        bg=CARD_BG,
                        wraplength=300,
                        justify='left')
        value.pack(anchor='w', pady=(3, 0))

        return var

    def _create_actions_panel(self, parent):
        """Create quick actions panel."""
        # Title
        title = tk.Label(parent,
                        text="🎯 Quick Actions",
                        font=('Segoe UI', 14, 'bold'),
                        fg=PRIMARY_COLOR,
                        bg=CARD_BG)
        title.pack(padx=15, pady=(15, 10), anchor='w')

        # Separator
        separator = ttk.Separator(parent, orient='horizontal')
        separator.pack(fill='x', padx=15, pady=(0, 15))

        # Actions list
        actions = [
            ("🎫 View All Cards", self._show_all_cards, SUCCESS_COLOR),
            ("📜 Cards History", self._show_card_history, SECONDARY_COLOR),
            ("🖨️ Print Last Receipt", self._print_last_receipt, WARNING_COLOR),
            ("📄 Print Card Summary", self._print_card_summary, WARNING_COLOR),
            ("✏️ Insert Card Manual", self._show_manual_card_insert, WARNING_COLOR),
            ("📅 Daily Report", self._generate_daily_report_manual, PRIMARY_COLOR),
            ("🗓 Weekly Report", self._generate_weekly_report_manual, PRIMARY_COLOR),
            ("📆 Monthly Report", self._generate_monthly_report_manual, PRIMARY_COLOR),
            ("📈 Yearly Report", self._generate_yearly_report_manual, SECONDARY_COLOR),
        ]

        for i, (text, command, color) in enumerate(actions):
            btn = tk.Button(parent,
                           text=text,
                           font=('Segoe UI', 11, 'bold'),
                           bg=color,
                           fg='white',
                           relief='flat',
                           cursor='hand2',
                           padx=15,
                           pady=12,
                           command=command)
            btn.pack(padx=15, pady=8, fill='x')

    def _create_footer(self):
        """Create footer status bar."""
        footer_frame = tk.Frame(self.root, bg=TEXT_PRIMARY, height=50)
        footer_frame.pack(fill='x', side='bottom')
        footer_frame.pack_propagate(False)

        self.status_var = tk.StringVar(value="Ready")
        status_label = tk.Label(footer_frame,
                               textvariable=self.status_var,
                               font=('Segoe UI', 10),
                               fg='white',
                               bg=TEXT_PRIMARY,
                               anchor='w')
        status_label.pack(fill='both', expand=True, padx=20, pady=12)

    def _check_serial_connection(self):
        """Check if serial connection is established."""
        if self.serial_service.is_connected:
            self.status_indicator.config(text=f"● Connected ({self.serial_service.port})", fg=SUCCESS_COLOR)
            self.status_var.set(f"Connected to {self.serial_service.port}")
        else:
            self.status_indicator.config(text="● Disconnected", fg=DANGER_COLOR)
            self.status_var.set("Not connected to Arduino - Check settings")

    def _read_card(self):
        """Read RFID card from Arduino with automatic database sync from card value."""
        # Immediate feedback - button clicked
        self.status_var.set("⏳ Reading card... Please wait...")
        self.root.update()
        self.root.update_idletasks()
        
        # Check Arduino connection
        if not self.serial_service.is_connected:
            self.status_var.set("⚠️ Arduino not connected! Please use Manual Mode to test.")
            self.root.update_idletasks()
            logger.warning("Read card attempted but Arduino not connected")
            return

        try:
            # Show loading indicator
            self.status_var.set("⏳ Loading card from Arduino... Please wait...")
            self.root.update()
            
            # Read card from Arduino
            success, result = self.serial_service.read_card()

            if success:
                # Parse result - Arduino sends "UID:AMOUNT" format if card has data
                raw_data = result.strip()
                card_amount = None
                
                # Check if data contains amount (format: UID:AMOUNT)
                if ':' in raw_data:
                    parts = raw_data.split(':')
                    raw_uid = parts[0]
                    # Try to parse amount if present
                    if len(parts) > 1 and parts[1]:
                        card_data_str = parts[1].strip()
                        
                        # Handle K-prefix (e.g., K50)
                        if card_data_str.upper().startswith('K'):
                            try:
                                card_amount = float(card_data_str[1:])
                                logger.info(f"Card contains K-amount data: UID={raw_uid}, Amount={card_amount}")
                            except ValueError:
                                logger.warning(f"Could not parse K-amount from: {card_data_str}")
                                card_amount = None
                        else:
                            # Try to parse as regular number
                            try:
                                card_amount = float(card_data_str)
                                logger.info(f"Card contains numeric data: UID={raw_uid}, Amount={card_amount}")
                            except ValueError:
                                logger.info(f"Card contains non-numeric data: {card_data_str}")
                                card_amount = None
                else:
                    raw_uid = raw_data
                
                # Format card UID: remove all spaces and standardize format
                card_uid = self._format_card_uid(raw_uid)
                
                # Update status
                self.status_var.set(f"⏳ Syncing card {card_uid} with database...")
                self.root.update_idletasks()
                
                # Check if this is a new card
                is_new_card = not self._card_exists_in_db(card_uid)
                
                try:
                    # Get or create card from database
                    card = self.db_service.create_or_get_card(card_uid)
                    db_balance = card['balance']
                    
                    # CRITICAL: Sync database with card's actual value
                    if card_amount is not None and card_amount >= 0:
                        # Card has valid numeric data - this is the SOURCE OF TRUTH
                        if card_amount != db_balance:
                            # Database is out of sync - update it to match the card
                            difference = card_amount - db_balance
                            
                            logger.warning(f"⚠️ SYNC REQUIRED: Card={card_amount}, DB={db_balance}, Diff={difference}")
                            
                            # Update database to match card
                            balance, tx_id = self.db_service.top_up(
                                card_uid,
                                difference,
                                employee=self.config.get("employee_name", "System Auto-Sync"),
                                notes=f"Auto-sync from card: Card value={card_amount}, DB was={db_balance}, Adjusted by={difference:+.2f}"
                            )
                            logger.info(f"✓ Database synced: {db_balance} → {balance} (matched card value)")
                        else:
                            # Already in sync
                            balance = db_balance
                            logger.info(f"✓ Card and database already in sync: {balance}")
                    else:
                        # Card has no valid numeric data - use database balance
                        balance = db_balance
                        logger.info(f"Card has no numeric data, using database balance: {balance}")
                    
                    # Update UI with card information
                    self.current_card_uid = card_uid
                    self.card_uid_var.set(card_uid)
                    self.current_balance = balance
                    self.balance_var.set(f"{balance:.2f} EGP")
                    
                    # Force UI update
                    self.root.update_idletasks()
                    
                    # Log the card read event (for audit)
                    self._log_card_read(card_uid, is_new=is_new_card)
                    
                    # Update status bar with result
                    if card_amount is not None and card_amount != db_balance:
                        self.status_var.set(f"🔄 Card synced: {card_uid} | Balance: {balance:.2f} EGP (was {db_balance:.2f} in DB)")
                    elif is_new_card:
                        self.status_var.set(f"✨ New card loaded: {card_uid} | Balance: {balance:.2f} EGP")
                    else:
                        self.status_var.set(f"✓ Card loaded: {card_uid} | Balance: {balance:.2f} EGP")
                    
                    logger.info(f"Card read and synced: {card_uid}, Balance: {balance:.2f} EGP, New: {is_new_card}")
                    
                    # Automatically read and display card history
                    self._read_and_show_history(card_uid)
                    
                except Exception as e:
                    logger.error(f"Database error while processing card: {e}")
                    self.status_var.set(f"❌ Database error: {str(e)}")
                    self.root.update_idletasks()
            else:
                # Only show error in status bar, not popup
                self.status_var.set(f"❌ Card read failed: {str(result)}")
                self.root.update_idletasks()
                logger.warning(f"Card read failed: {result}")
                
        except Exception as e:
            logger.error(f"Error in read card function: {e}")
            self.status_var.set(f"❌ Error: {str(e)}")
            self.root.update_idletasks()

    def _toggle_manual_mode(self):
        """Toggle manual card entry mode."""
        self.manual_mode = self.manual_mode_var.get()
        state = 'normal' if self.manual_mode else 'disabled'
        self.manual_uid_entry.config(state=state)
        self.manual_load_btn.config(state=state)

        if self.manual_mode:
            self.status_var.set("Manual Mode: Enter UID manually")
        else:
            self._check_serial_connection()

    def _load_manual_card(self):
        """Load card manually with automatic database save."""
        raw_uid = self.manual_uid_var.get().strip()
        if not raw_uid:
            self.status_var.set("⚠️ Please enter a card UID")
            return

        # Show loading
        self.status_var.set("⏳ Loading card manually... Please wait...")
        self.root.update_idletasks()

        try:
            # Format card UID to standard format (no spaces)
            uid = self._format_card_uid(raw_uid)
            
            # Check if card exists
            is_new_card = not self._card_exists_in_db(uid)
            
            # Automatically create or get card from database
            card = self.db_service.create_or_get_card(uid)
            
            # Update UI
            self.current_card_uid = uid
            self.card_uid_var.set(uid)
            balance = card['balance']
            self.current_balance = balance
            self.balance_var.set(f"{balance:.2f} EGP")
            
            # Log the event
            self._log_card_read(uid, is_new=is_new_card)
            
            # Update status bar (no popup)
            if is_new_card:
                self.status_var.set(f"✨ New card created (Manual): {uid} | Balance: {balance:.2f} EGP")
            else:
                self.status_var.set(f"✓ Card loaded (Manual): {uid} | Balance: {balance:.2f} EGP")
            
            logger.info(f"Manual card loaded: {uid}, Balance: {balance:.2f} EGP, New: {is_new_card}")
            
        except Exception as e:
            logger.error(f"Manual load error: {e}")
            self.status_var.set(f"❌ Failed to load card: {str(e)}")

    def _parse_input(self, input_value):
        """Parse input to detect type: numeric, K-prefixed, or string.
        
        Returns:
            tuple: (input_type, amount, display_value)
            - input_type: 'numeric', 'k_amount', or 'string'
            - amount: float value (0.0 for non-numeric)
            - display_value: string to write to card
        """
        input_value = input_value.strip().upper()
        
        # Check for K-prefix (e.g., K50)
        if input_value.startswith('K'):
            try:
                amount = float(input_value[1:])
                if amount > 0:
                    return 'k_amount', amount, input_value
            except ValueError:
                pass
        
        # Try to parse as regular numeric
        try:
            amount = float(input_value)
            if amount > 0:
                return 'numeric', amount, str(amount)
        except ValueError:
            pass
        
        # It's a string
        return 'string', 0.0, input_value
    
    def _top_up(self):
        """Perform top-up operation or write string data."""
        if not self.current_card_uid:
            messagebox.showwarning("No Card", "Read or load a card first.")
            return

        input_value = self.amount_var.get().strip()
        if not input_value:
            messagebox.showerror("Empty Input", "Please enter a value.")
            return
        
        # Check if input is too long for card storage
        if len(input_value) > 11:
            messagebox.showerror("Input Too Long", "Maximum 11 characters allowed for card storage.")
            return

        # Parse input
        input_type, amount, display_value = self._parse_input(input_value)
        mode = "Manual" if self.manual_mode else "Arduino"
        
        if input_type == 'numeric':
            # Regular numeric input
            if messagebox.askyesno("Confirm", f"Add {amount:.2f} EGP to {self.current_card_uid}?\nMode: {mode}"):
                self.status_var.set("Processing top-up...")
                self.root.update_idletasks()
                if self.manual_mode:
                    self._manual_top_up(amount, display_value)
                else:
                    self._arduino_top_up(amount, display_value)
                    
        elif input_type == 'k_amount':
            # K-prefixed amount (e.g., K50)
            if messagebox.askyesno("Confirm K-Amount", f"Add {amount:.2f} EGP (K-Amount) to {self.current_card_uid}?\nCard will store: '{display_value}'\nMode: {mode}"):
                self.status_var.set("Processing K-amount top-up...")
                self.root.update_idletasks()
                if self.manual_mode:
                    self._manual_top_up(amount, display_value)
                else:
                    self._arduino_top_up(amount, display_value)
                    
        else:
            # String input - only write to card
            if messagebox.askyesno("Confirm", f"Write '{display_value}' to card {self.current_card_uid}?\nMode: {mode}\n\nNote: Balance will NOT be updated in database."):
                self.status_var.set("Writing string to card...")
                self.root.update_idletasks()
                if self.manual_mode:
                    messagebox.showinfo("Manual Mode", "String data can only be written in Arduino mode.\nManual mode only supports numeric balance updates.")
                else:
                    self._arduino_write_string(display_value)

    def _manual_top_up(self, amount, display_value):
        """Handle manual top-up."""
        try:
            new_bal, tx_id = self.db_service.top_up(
                self.current_card_uid,
                amount,
                employee=self.config.get("employee_name", "Receptionist"),
                notes=f"Manual entry: {display_value}"
            )
            self._update_balance(new_bal)
            
            # Print receipt if enabled
            if self.auto_print_receipts:
                self._print_receipt(self.current_card_uid, amount, new_bal, tx_id)
            
            messagebox.showinfo(
                "Success (Manual)",
                f"Added {amount:.2f} EGP\nNew Balance: {new_bal:.2f} EGP\n(Note: Physical card not updated)"
            )
        except Exception as e:
            logger.error(f"Manual top-up error: {e}")
            messagebox.showerror("DB Error", str(e))

    def _arduino_top_up(self, amount, display_value):
        """Handle Arduino top-up with numeric value."""
        # Calculate new balance BEFORE writing to card
        new_balance_expected = self.current_balance + amount
        
        # Determine what to write to card (new total balance)
        # For K-amounts, keep the K prefix; for numeric, write the new total
        if display_value.startswith('K'):
            # K-amount: write K + new total balance
            card_write_value = f"K{new_balance_expected:.0f}"
        else:
            # Regular amount: write new total balance
            card_write_value = str(new_balance_expected)
        
        # Show clear instructions with messagebox warning
        result = messagebox.askokcancel(
            "Important - Keep Card on Reader",
            f"⚠️ PLEASE KEEP THE CARD ON THE READER!\n\n"
            f"Adding {amount:.2f} EGP to card.\n"
            f"New balance will be: {new_balance_expected:.2f} EGP\n"
            f"Card will store: '{card_write_value}'\n\n"
            f"Do NOT remove the card until you see a success message.\n\n"
            f"Click OK when the card is on the reader and you're ready.",
            icon='warning'
        )
        
        if not result:
            self.status_var.set("Write operation cancelled")
            return
        
        # Show clear instructions to user
        self.status_var.set(f"⏳ Writing '{card_write_value}' to card... KEEP CARD ON READER!")
        self.root.update()
        self.root.update_idletasks()
        
        success, uid, msg = self.serial_service.write_card(card_write_value)
        if success:
            try:
                new_bal, tx_id = self.db_service.top_up(
                    self.current_card_uid,
                    amount,
                    employee=self.config.get("employee_name", "Receptionist"),
                    notes=f"Arduino write: {card_write_value} (added {amount:.2f})"
                )
                self._update_balance(new_bal)
                
                # Print receipt if enabled
                if self.auto_print_receipts:
                    self._print_receipt(self.current_card_uid, amount, new_bal, tx_id)
                
                self.status_var.set(f"✓ Successfully wrote {card_write_value} to card!")
                messagebox.showinfo("Success", f"Added {amount:.2f} EGP\nNew Balance: {new_bal:.2f} EGP\nCard now stores: '{card_write_value}'")
            except Exception as e:
                logger.error(f"DB error after write: {e}")
                self.status_var.set(f"❌ Database error: {str(e)}")
                messagebox.showerror("DB Error", str(e))
        else:
            self.status_var.set(f"❌ Write failed: {msg}")
            logger.warning(f"Write failed: {msg}")
    
    def _arduino_write_string(self, text_data):
        """Handle Arduino string write (no database update)."""
        # Show clear instructions with messagebox warning
        result = messagebox.askokcancel(
            "Important - Keep Card on Reader",
            f"⚠️ PLEASE KEEP THE CARD ON THE READER!\n\n"
            f"The system will now write '{text_data}' to the card.\n"
            f"Do NOT remove the card until you see a success message.\n\n"
            f"Click OK when the card is on the reader and you're ready.",
            icon='warning'
        )
        
        if not result:
            self.status_var.set("Write operation cancelled")
            return
        
        # Show clear instructions to user
        self.status_var.set(f"⏳ Writing '{text_data}' to card... KEEP CARD ON READER!")
        self.root.update()
        self.root.update_idletasks()
        
        success, uid, msg = self.serial_service.write_card(text_data)
        if success:
            self.status_var.set(f"✓ Successfully wrote '{text_data}' to card!")
            self.amount_var.set("")
            messagebox.showinfo("Success", f"String '{text_data}' written to card!\nCard UID: {uid}\n\nNote: Database balance NOT updated.")
        else:
            self.status_var.set(f"❌ Write failed: {msg}")
            logger.warning(f"Write failed: {msg}")

    def _update_balance(self, new_balance):
        """Update balance display."""
        self.current_balance = new_balance
        self.balance_var.set(f"{new_balance:.2f} EGP")
        self.amount_var.set("")
        self.status_var.set("Top-up successful")
    
    def _print_receipt(self, card_uid, amount, balance_after, transaction_id):
        """Print receipt for transaction."""
        try:
            employee = self.config.get("employee_name", "Receptionist")
            success, result = self.receipt_printer.print_receipt(
                card_uid=card_uid,
                amount=amount,
                balance_after=balance_after,
                transaction_id=transaction_id,
                employee=employee,
                timestamp=datetime.now(),
                auto_print=True
            )
            
            if success:
                if result.endswith('.pdf'):
                    logger.info(f"Receipt saved to: {result}")
                    self.status_var.set(f"Receipt saved: {os.path.basename(result)}")
                else:
                    logger.info(f"Receipt printed: {result}")
                    self.status_var.set("Receipt printed successfully")
            else:
                logger.error(f"Receipt printing failed: {result}")
                self.status_var.set("Receipt printing failed")
        except Exception as e:
            logger.error(f"Receipt printing error: {e}")
            self.status_var.set(f"Receipt error: {str(e)}")
    
    def _print_last_receipt(self):
        """Print receipt for last transaction."""
        if not self.current_card_uid:
            messagebox.showwarning("No Card", "No card loaded. Please read a card first.")
            return
        
        try:
            # Get last transaction for this card
            transactions = self.db_service.get_transactions(card_uid=self.current_card_uid)
            if not transactions:
                messagebox.showinfo("No Transactions", "No transactions found for this card.")
                return
            
            last_txn = transactions[0]  # Most recent
            
            employee = self.config.get("employee_name", "Receptionist")
            success, result = self.receipt_printer.print_receipt(
                card_uid=last_txn['card_uid'],
                amount=last_txn['amount'],
                balance_after=last_txn['balance_after'],
                transaction_id=last_txn['id'],
                employee=last_txn.get('employee', employee),
                timestamp=last_txn['timestamp'],
                auto_print=False  # Always save as PDF for reprints
            )
            
            if success:
                # Auto-open the PDF
                try:
                    os.startfile(result)
                    messagebox.showinfo("Receipt Generated", f"Receipt opened successfully!\n\nSaved to:\n{result}")
                except Exception as e:
                    messagebox.showinfo("Receipt Saved", f"Receipt saved to:\n{result}\n\nPlease open it manually.")
            else:
                messagebox.showerror("Print Failed", result)
        except Exception as e:
            logger.error(f"Print last receipt error: {e}")
            messagebox.showerror("Error", str(e))
    
    def _print_card_summary(self):
        """Print complete card summary with transaction history."""
        if not self.current_card_uid:
            messagebox.showwarning("No Card", "No card loaded. Please read a card first.")
            return
        
        try:
            # Get card data
            card = self.db_service.create_or_get_card(self.current_card_uid)
            transactions = self.db_service.get_transactions(card_uid=self.current_card_uid)
            
            success, result = self.receipt_printer.print_card_summary(
                card_data=card,
                transactions=transactions
            )
            
            if success:
                # Auto-open the PDF
                try:
                    os.startfile(result)
                    messagebox.showinfo("Summary Generated", f"Card summary opened successfully!\n\nSaved to:\n{result}")
                except Exception as e:
                    messagebox.showinfo("Summary Saved", f"Card summary saved to:\n{result}\n\nPlease open it manually.")
            else:
                messagebox.showerror("Print Failed", result)
        except Exception as e:
            logger.error(f"Print card summary error: {e}")
            messagebox.showerror("Error", str(e))

    # ------------------------------------------------------------------ #
    # Dialog Openers
    # ------------------------------------------------------------------ #
    def _show_transactions(self):
        """Show transactions dialog."""
        from rfid_reception.gui.dialogs import TransactionsDialog
        TransactionsDialog(self.root, self.db_service)

    def _generate_report(self):
        """Show report generation dialog."""
        from rfid_reception.gui.dialogs import ReportDialog
        ReportDialog(self.root, self.reports_generator)

    def _show_settings(self):
        """Show settings dialog."""
        from rfid_reception.gui.dialogs import SettingsDialog
        SettingsDialog(self.root, self.config, self.serial_service, self._on_settings_saved)

    def _on_settings_saved(self):
        """Callback when settings are saved."""
        self._check_serial_connection()
        messagebox.showinfo("Settings", "Settings saved!")

    def _show_all_cards(self):
        """Show all cards dialog."""
        from rfid_reception.gui.dialogs.view_all_cards_dialog import ViewAllCardsDialog
        ViewAllCardsDialog(self.root, self.db_service)

    def _show_manual_card_insert(self):
        """Show manual card insert dialog."""
        from rfid_reception.gui.dialogs.manual_card_insert_dialog import ManualCardInsertDialog
        ManualCardInsertDialog(self.root, self.db_service)
    
    def _show_card_history(self):
        """Show card history dialog."""
        from rfid_reception.gui.dialogs.card_history_dialog import CardHistoryDialog
        CardHistoryDialog(self.root, self.serial_service)
    
    def _read_and_show_history(self, card_uid):
        """Read card history from Arduino and display in dialog automatically.
        
        Args:
            card_uid: The UID of the card that was just read
        """
        if not self.serial_service.is_connected:
            logger.info("Skipping history read - Arduino not connected")
            return
        
        try:
            # Update status
            self.status_var.set(f"⏳ Reading game history from card...")
            self.root.update_idletasks()
            
            # Read history from Arduino
            success, uid_or_error, history_entries = self.serial_service.read_history()
            
            if success:
                logger.info(f"History read successfully: {len(history_entries)} blocks")
                
                # Show history dialog with preloaded data
                from rfid_reception.gui.dialogs.card_history_dialog import CardHistoryDialog
                CardHistoryDialog(
                    self.root, 
                    self.serial_service,
                    card_uid=uid_or_error,  # Use UID from history read
                    history_data=history_entries
                )
                
                # Update status
                self.status_var.set(f"✓ Card loaded: {card_uid} | Balance: {self.current_balance:.2f} EGP | History displayed")
            else:
                # History read failed, but don't interrupt the main flow
                logger.warning(f"Could not read history: {uid_or_error}")
                self.status_var.set(f"✓ Card loaded: {card_uid} | Balance: {self.current_balance:.2f} EGP (history unavailable)")
                
        except Exception as e:
            logger.error(f"Error reading card history: {e}")
            # Don't show error popup, just log it
            self.status_var.set(f"✓ Card loaded: {card_uid} | Balance: {self.current_balance:.2f} EGP")

    def _generate_daily_report_manual(self):
        try:
            date_str = simpledialog.askstring(
                "Daily Report", "Enter date (YYYY-MM-DD) or leave blank for today:", parent=self.root
            )
            
            # Compute date
            if date_str:
                try:
                    d = datetime.strptime(date_str, '%Y-%m-%d').date()
                except Exception:
                    messagebox.showerror("Daily Report", "Invalid date format. Use YYYY-MM-DD.")
                    return
            else:
                d = datetime.now().date()

            # Auto-generate filename in reports folder
            reports_dir = os.path.join(os.getcwd(), "reports")
            os.makedirs(reports_dir, exist_ok=True)
            
            filename = f"daily_report_{d.strftime('%Y%m%d')}.pdf"
            save_path = os.path.join(reports_dir, filename)

            if date_str:
                path = self.reports_generator.generate_daily_report(date_str, output_path=save_path)
            else:
                path = self.reports_generator.generate_daily_report(output_path=save_path)
            
            # Auto-open the PDF
            try:
                os.startfile(path)
                messagebox.showinfo("Daily Report", f"Report opened successfully!\n\nSaved to:\n{path}")
            except Exception as e:
                messagebox.showinfo("Daily Report", f"Report generated:\n{path}\n\nPlease open it manually.")
        except Exception as e:
            logger.error(f"Daily report error: {e}")
            messagebox.showerror("Daily Report", str(e))

        
    def _generate_weekly_report_manual(self):
        try:
            week_start = simpledialog.askstring(
                "Weekly Report",
                "Enter week start (YYYY-MM-DD, Monday). Leave blank for current week:",
                parent=self.root
            )
            
            # Determine start/end
            if week_start:
                try:
                    start = datetime.strptime(week_start, '%Y-%m-%d').date()
                except Exception:
                    messagebox.showerror("Weekly Report", "Invalid date format. Use YYYY-MM-DD.")
                    return
            else:
                today = datetime.now().date()
                start = today - timedelta(days=today.weekday())
            end = start + timedelta(days=6)

            # Auto-generate filename in reports folder
            reports_dir = os.path.join(os.getcwd(), "reports")
            os.makedirs(reports_dir, exist_ok=True)
            
            filename = f"weekly_report_{start.strftime('%Y%m%d')}_to_{end.strftime('%Y%m%d')}.pdf"
            save_path = os.path.join(reports_dir, filename)

            if week_start:
                path = self.reports_generator.generate_weekly_report(week_start, output_path=save_path)
            else:
                path = self.reports_generator.generate_weekly_report(output_path=save_path)
            
            # Auto-open the PDF
            try:
                os.startfile(path)
                messagebox.showinfo("Weekly Report", f"Report opened successfully!\n\nSaved to:\n{path}")
            except Exception as e:
                messagebox.showinfo("Weekly Report", f"Report generated:\n{path}\n\nPlease open it manually.")
        except Exception as e:
            logger.error(f"Weekly report error: {e}")
            messagebox.showerror("Weekly Report", str(e))

    def _generate_monthly_report_manual(self):
        try:
            m = simpledialog.askinteger(
                "Monthly Report", "Enter month (1-12):", initialvalue=datetime.now().month,
                minvalue=1, maxvalue=12, parent=self.root
            )
            y = simpledialog.askinteger(
                "Monthly Report", "Enter year:", initialvalue=datetime.now().year,
                minvalue=2000, maxvalue=2100, parent=self.root
            )
            if not m:
                m = datetime.now().month
            if not y:
                y = datetime.now().year
            
            # Auto-generate filename in reports folder
            reports_dir = os.path.join(os.getcwd(), "reports")
            os.makedirs(reports_dir, exist_ok=True)
            
            filename = f"monthly_report_{y}{m:02d}.pdf"
            save_path = os.path.join(reports_dir, filename)
            
            path = self.reports_generator.generate_monthly_report(m, y, output_path=save_path)
            
            # Auto-open the PDF
            try:
                os.startfile(path)
                messagebox.showinfo("Monthly Report", f"Report opened successfully!\n\nSaved to:\n{path}")
            except Exception as e:
                messagebox.showinfo("Monthly Report", f"Report generated:\n{path}\n\nPlease open it manually.")
        except Exception as e:
            logger.error(f"Monthly report error: {e}")
            messagebox.showerror("Monthly Report", str(e))

    def _generate_yearly_report_manual(self):
        try:
            y = simpledialog.askinteger(
                "Yearly Report", "Enter year (blank for current):", initialvalue=datetime.now().year,
                minvalue=2000, maxvalue=2100, parent=self.root
            )
            if not y:
                y = datetime.now().year
            
            # Auto-generate filename in reports folder
            reports_dir = os.path.join(os.getcwd(), "reports")
            os.makedirs(reports_dir, exist_ok=True)
            
            filename = f"yearly_report_{y}.pdf"
            save_path = os.path.join(reports_dir, filename)
            
            path = self.reports_generator.generate_yearly_report(y, output_path=save_path)
            
            # Auto-open the PDF
            try:
                os.startfile(path)
                messagebox.showinfo("Yearly Report", f"Report opened successfully!\n\nSaved to:\n{path}")
            except Exception as e:
                messagebox.showinfo("Yearly Report", f"Report generated:\n{path}\n\nPlease open it manually.")
        except Exception as e:
            logger.error(f"Yearly report error: {e}")
            messagebox.showerror("Yearly Report", str(e))

    def _export_cards_to_pdf(self):
        """Export cards to PDF."""
        try:
            cards = self.db_service.get_all_cards()
            if not cards:
                messagebox.showwarning("No Cards", "No cards available to export.")
                return

            file_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")],
                initialfile=f"cards_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            )
            if not file_path:
                return

            self.reports_generator.generate_beautiful_arabic_report(cards, output_path=file_path)
            messagebox.showinfo("Export Successful", f"PDF exported to:\n{file_path}")
        except Exception as e:
            logger.error(f"Export error: {e}")
            messagebox.showerror("Export Failed", str(e))
    
    def _format_card_uid(self, raw_uid):
        """Format card UID to standard format without spaces."""
        # First, check if UID contains amount data (format: UID:AMOUNT)
        if ':' in raw_uid:
            # Split and take only the UID part, ignore the amount
            uid_part = raw_uid.split(':')[0]
            logger.debug(f"Card UID contains amount data: '{raw_uid}' -> extracting UID: '{uid_part}'")
            raw_uid = uid_part
        
        # Remove all spaces, tabs, and standardize to uppercase
        formatted = raw_uid.replace(' ', '').replace('\t', '').strip().upper()
        logger.debug(f"Card UID formatted: '{raw_uid}' -> '{formatted}'")
        return formatted
    
    def _card_exists_in_db(self, card_uid):
        """Check if a card exists in the database."""
        try:
            # Format card UID before checking
            card_uid = self._format_card_uid(card_uid)
            
            # Check if card has any transactions (means it exists)
            transactions = self.db_service.get_transactions(card_uid=card_uid)
            if transactions:
                return True
            
            # Check if card balance exists
            balance = self.db_service.get_card_balance(card_uid)
            return balance is not None
        except Exception as e:
            logger.debug(f"Card existence check failed: {e}")
            return False
    
    def _log_card_read(self, card_uid, is_new=False):
        """Log a card read event."""
        try:
            employee = self.config.get("employee_name", "Receptionist")
            notes = "New card created" if is_new else "Card read from Arduino"
            
            if not is_new:
                # Only log read events for existing cards
                self.db_service.log_card_read(card_uid, employee=employee)
                logger.info(f"Card read logged: {card_uid}")
        except Exception as e:
            logger.error(f"Failed to log card read: {e}")
    
    def _write_balance(self):
        """Write a specific balance to the card (not add, but set)."""
        if not self.current_card_uid:
            messagebox.showwarning("No Card", "Read or load a card first.")
            return

        input_value = self.amount_var.get().strip()
        if not input_value:
            messagebox.showerror("Empty Input", "Please enter a value.")
            return
        
        # Check if input is too long
        if len(input_value) > 11:
            messagebox.showerror("Input Too Long", "Maximum 11 characters allowed.")
            return

        # Parse input
        input_type, amount, display_value = self._parse_input(input_value)
        
        if input_type == 'string':
            messagebox.showerror("Invalid Input", "Set Balance only accepts numeric values or K-amounts (e.g., 50 or K50).\nFor text, use 'Add to Balance' button.")
            return
        
        if amount < 0:
            messagebox.showerror("Invalid Amount", "Amount cannot be negative.")
            return

        mode = "Manual" if self.manual_mode else "Arduino"
        current_balance = self.current_balance
        difference = amount - current_balance
        
        prefix = "K-" if input_type == 'k_amount' else ""
        msg = f"Set balance to {amount:.2f} EGP ({prefix}Amount)?\n"
        if input_type == 'k_amount':
            msg += f"Card will store: '{display_value}'\n\n"
        else:
            msg += "\n"
            
        if difference > 0:
            msg += f"This will ADD {difference:.2f} EGP to the card.\n"
        elif difference < 0:
            msg += f"This will DEDUCT {abs(difference):.2f} EGP from the card.\n"
        else:
            msg += f"Balance is already {amount:.2f} EGP (no change).\n"
        msg += f"\nCard: {self.current_card_uid}\nMode: {mode}"
        
        if messagebox.askyesno("Confirm Balance Write", msg):
            self.status_var.set("Writing balance...")
            self.root.update_idletasks()

            if self.manual_mode:
                self._manual_write_balance(amount, difference, display_value)
            else:
                self._arduino_write_balance(amount, difference, display_value)
    
    def _manual_write_balance(self, new_balance, difference, display_value):
        """Handle manual balance write."""
        try:
            # Use top_up with the difference (can be negative for deductions)
            if difference != 0:
                final_balance, tx_id = self.db_service.top_up(
                    self.current_card_uid,
                    difference,
                    employee=self.config.get("employee_name", "Receptionist"),
                    notes=f"Balance set to {new_balance:.2f} ({display_value}) - Manual entry"
                )
                self._update_balance(final_balance)
                
                # Print receipt if enabled
                if self.auto_print_receipts:
                    self._print_receipt(self.current_card_uid, difference, final_balance, tx_id)
                
                messagebox.showinfo(
                    "Success (Manual)",
                    f"Balance set to {new_balance:.2f} EGP\nCard value: {display_value}\n(Note: Physical card not updated in manual mode)"
                )
            else:
                messagebox.showinfo("No Change", "Balance is already at the specified amount.")
        except Exception as e:
            logger.error(f"Manual balance write error: {e}")
            messagebox.showerror("DB Error", str(e))
    
    def _arduino_write_balance(self, new_balance, difference, display_value):
        """Handle Arduino balance write."""
        # Show clear instructions with messagebox warning
        result = messagebox.askokcancel(
            "Important - Keep Card on Reader",
            f"⚠️ PLEASE KEEP THE CARD ON THE READER!\n\n"
            f"The system will now write '{display_value}' to the card.\n"
            f"Do NOT remove the card until you see a success message.\n\n"
            f"Click OK when the card is on the reader and you're ready.",
            icon='warning'
        )
        
        if not result:
            self.status_var.set("Write operation cancelled")
            return
        
        # Show clear instructions
        self.status_var.set(f"⏳ Writing '{display_value}' to card... KEEP CARD ON READER!")
        self.root.update()
        self.root.update_idletasks()
        
        # Write the display value to the card (e.g., "50" or "K50")
        success, uid, msg = self.serial_service.write_card(display_value)
        if success:
            try:
                # Update database with the difference
                if difference != 0:
                    final_balance, tx_id = self.db_service.top_up(
                        self.current_card_uid,
                        difference,
                        employee=self.config.get("employee_name", "Receptionist"),
                        notes=f"Balance set to {new_balance:.2f} ({display_value}) - Arduino write"
                    )
                    self._update_balance(final_balance)
                    
                    # Print receipt if enabled
                    if self.auto_print_receipts:
                        self._print_receipt(self.current_card_uid, difference, final_balance, tx_id)
                    
                    self.status_var.set(f"✓ Successfully wrote '{display_value}' to card!")
                    messagebox.showinfo("Success", f"Balance set to {new_balance:.2f} EGP\nCard data: '{display_value}'\nPhysical card updated successfully.")
                else:
                    self.status_var.set(f"✓ Card updated with '{display_value}'")
                    messagebox.showinfo("No Change", f"Balance is already at the specified amount.\nCard updated with: '{display_value}'")
            except Exception as e:
                logger.error(f"DB error after write: {e}")
                self.status_var.set(f"❌ Database error: {str(e)}")
                messagebox.showerror("DB Error", str(e))
        else:
            self.status_var.set(f"❌ Write failed: {msg}")
            logger.warning(f"Write failed: {msg}")
    
    def _toggle_auto_scan(self):
        """Toggle auto-scan mode on/off."""
        if self.auto_scan_enabled:
            # Disable auto-scan
            self._stop_auto_scan()
        else:
            # Enable auto-scan
            self._start_auto_scan()
    
    def _start_auto_scan(self):
        """Start automatic card scanning."""
        if not self.serial_service.is_connected:
            messagebox.showwarning(
                "Arduino Not Connected",
                "Please connect to Arduino before enabling auto-scan.\n\n"
                "Go to Settings → Configure Serial to connect."
            )
            return
        
        if self.manual_mode:
            messagebox.showwarning(
                "Manual Mode Active",
                "Auto-scan is not available in Manual Mode.\n\n"
                "Disable Manual Mode first to use auto-scan."
            )
            return
        
        self.auto_scan_enabled = True
        self.last_scanned_uid = None
        self.auto_scan_btn.config(
            text="⏸️ Disable Auto-Scan",
            bg=WARNING_COLOR
        )
        self.status_var.set("🔄 Auto-scan enabled - Place card on reader...")
        logger.info("Auto-scan enabled")
        
        # Start the scanning loop
        self._auto_scan_loop()
    
    def _stop_auto_scan(self):
        """Stop automatic card scanning."""
        self.auto_scan_enabled = False
        if self.auto_scan_job:
            self.root.after_cancel(self.auto_scan_job)
            self.auto_scan_job = None
        
        self.auto_scan_btn.config(
            text="⚡ Enable Auto-Scan",
            bg=SUCCESS_COLOR
        )
        self.status_var.set("Auto-scan disabled")
        logger.info("Auto-scan disabled")
    
    def _auto_scan_loop(self):
        """Continuously scan for cards with automatic sync."""
        if not self.auto_scan_enabled:
            return
        
        try:
            # Only scan if Arduino is connected
            if self.serial_service.is_connected:
                # Read card without showing loading message
                success, result = self.serial_service.read_card()
                
                if success:
                    # Parse UID and amount
                    raw_data = result.strip()
                    card_amount = None
                    
                    if ':' in raw_data:
                        parts = raw_data.split(':')
                        card_uid = parts[0]
                        
                        # Try to parse amount if present
                        if len(parts) > 1 and parts[1]:
                            card_data_str = parts[1].strip()
                            
                            # Handle K-prefix (e.g., K50)
                            if card_data_str.upper().startswith('K'):
                                try:
                                    card_amount = float(card_data_str[1:])
                                except ValueError:
                                    card_amount = None
                            else:
                                # Try to parse as regular number
                                try:
                                    card_amount = float(card_data_str)
                                except ValueError:
                                    card_amount = None
                    else:
                        card_uid = raw_data
                    
                    # Format UID
                    card_uid = self._format_card_uid(card_uid)
                    
                    # Only process if it's a different card
                    if card_uid != self.last_scanned_uid:
                        self.last_scanned_uid = card_uid
                        logger.info(f"Auto-scan detected card: {card_uid}")
                        
                        # Check if new card
                        is_new_card = not self._card_exists_in_db(card_uid)
                        
                        # Create or get card from database
                        card = self.db_service.create_or_get_card(card_uid)
                        db_balance = card['balance']
                        
                        # CRITICAL: Sync database with card's actual value
                        if card_amount is not None and card_amount >= 0:
                            # Card has valid numeric data - sync database
                            if card_amount != db_balance:
                                # Database is out of sync - update it
                                difference = card_amount - db_balance
                                
                                logger.warning(f"⚠️ AUTO-SCAN SYNC: Card={card_amount}, DB={db_balance}, Diff={difference}")
                                
                                balance, tx_id = self.db_service.top_up(
                                    card_uid,
                                    difference,
                                    employee=self.config.get("employee_name", "System Auto-Sync"),
                                    notes=f"Auto-sync from card (auto-scan): Card value={card_amount}, DB was={db_balance}, Adjusted by={difference:+.2f}"
                                )
                                logger.info(f"✓ Auto-scan synced: {db_balance} → {balance}")
                            else:
                                balance = db_balance
                        else:
                            # No card data, use database
                            balance = db_balance
                        
                        # Update UI
                        self.current_card_uid = card_uid
                        self.card_uid_var.set(card_uid)
                        self.current_balance = balance
                        self.balance_var.set(f"{balance:.2f} EGP")
                        
                        # Log the event
                        self._log_card_read(card_uid, is_new=is_new_card)
                        
                        # Update status
                        if card_amount is not None and card_amount != db_balance:
                            self.status_var.set(f"🔄 Card synced: {card_uid} | Balance: {balance:.2f} EGP (was {db_balance:.2f})")
                        elif is_new_card:
                            self.status_var.set(f"✨ New card detected: {card_uid} | Balance: {balance:.2f} EGP")
                        else:
                            self.status_var.set(f"✓ Card detected: {card_uid} | Balance: {balance:.2f} EGP")
                        
                        logger.info(f"Auto-scan loaded: {card_uid}, Balance: {balance:.2f} EGP, New: {is_new_card}")
                        
                        # Automatically read and display card history
                        self._read_and_show_history(card_uid)
        
        except Exception as e:
            logger.error(f"Auto-scan error: {e}")
            # Don't stop auto-scan on error, just log it
        
        # Schedule next scan (every 1 second)
        self.auto_scan_job = self.root.after(1000, self._auto_scan_loop)


# Backward compatibility alias
MainWindow = ModernMainWindow
