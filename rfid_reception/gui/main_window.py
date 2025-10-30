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
        company_name = config.get('company_name', 'نظام استقبال RFID')
        company_info = {
            'address': config.get('company_address', ''),
            'phone': config.get('company_phone', '')
        }
        self.receipt_printer = ReceiptPrinter(company_name, company_info)
        self.auto_print_receipts = config.get('auto_print_receipts', True)

        self.root.title("نظام استقبال RFID")
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
                              text="🎫 نظام استقبال RFID",
                              font=('Segoe UI', 22, 'bold'),
                              fg='white',
                              bg=PRIMARY_COLOR)
        title_label.pack(side='right', anchor='e')

        # Status indicator
        self.status_indicator = tk.Label(header_content,
                                        text="● غير متصل",
                                        font=('Segoe UI', 11, 'bold'),
                                        fg=DANGER_COLOR,
                                        bg=PRIMARY_COLOR)
        self.status_indicator.pack(side='left', anchor='w')

    def _create_card_panel(self, parent):
        """Create card reading and top-up panel."""
        # Title
        title = tk.Label(parent,
                        text="💳 عمليات البطاقة",
                        font=('Segoe UI', 14, 'bold'),
                        fg=PRIMARY_COLOR,
                        bg=CARD_BG)
        title.pack(padx=15, pady=(15, 10), anchor='e')

        # Separator
        separator = ttk.Separator(parent, orient='horizontal')
        separator.pack(fill='x', padx=15, pady=(0, 15))

        # Card UID section
        self._create_info_section(parent, "📋 رقم البطاقة", "self.card_uid_var", "لم يتم اكتشاف بطاقة")

        # Balance section
        self._create_balance_section(parent)

        # Button frame for Read Card and Auto-Scan toggle
        btn_frame = tk.Frame(parent, bg=CARD_BG)
        btn_frame.pack(padx=15, pady=15, fill='x')
        
        # Read Card button
        read_btn = tk.Button(btn_frame,
                            text="🔍 قراءة البطاقة",
                            font=('Segoe UI', 12, 'bold'),
                            bg=PRIMARY_COLOR,
                            fg='white',
                            relief='flat',
                            cursor='hand2',
                            padx=20,
                            pady=12,
                            command=self._read_card)
        read_btn.pack(side='right', fill='x', expand=True, padx=(5, 0))
        
        # Auto-Scan Toggle button
        self.auto_scan_btn = tk.Button(btn_frame,
                                      text="⚡ تفعيل المسح التلقائي",
                                      font=('Segoe UI', 10, 'bold'),
                                      bg=SUCCESS_COLOR,
                                      fg='white',
                                      relief='flat',
                                      cursor='hand2',
                                      padx=15,
                                      pady=12,
                                      command=self._toggle_auto_scan)
        self.auto_scan_btn.pack(side='right', fill='x', expand=True, padx=(0, 5))

        # Spacer
        spacer = ttk.Frame(parent, height=20)
        spacer.pack()

        # Top-Up section separator
        sep2 = ttk.Separator(parent, orient='horizontal')
        sep2.pack(fill='x', padx=15, pady=10)

        # Top-Up amount section
        topup_label = tk.Label(parent,
                              text="💰 مبلغ الشحن / كتابة البيانات",
                              font=('Segoe UI', 12, 'bold'),
                              fg=PRIMARY_COLOR,
                              bg=CARD_BG)
        topup_label.pack(padx=15, pady=(10, 5), anchor='e')
        
        # Instruction label
        instruction_label = tk.Label(parent,
                                    text="أدخل: 50 (رقم) | K50 (مبلغ K) | أحمد (نص) - بحد أقصى 11 حرف",
                                    font=('Segoe UI', 8),
                                    fg=TEXT_SECONDARY,
                                    bg=CARD_BG)
        instruction_label.pack(padx=15, pady=(0, 5), anchor='e')

        # Amount input with EGP label
        amount_frame = tk.Frame(parent, bg=CARD_BG)
        amount_frame.pack(padx=15, pady=5, fill='x')

        egp_label = tk.Label(amount_frame,
                            text="جنيه ",
                            font=('Segoe UI', 12, 'bold'),
                            fg=TEXT_SECONDARY,
                            bg=CARD_BG)
        egp_label.pack(side='right', padx=10)

        self.amount_var = tk.StringVar()
        amount_entry = tk.Entry(amount_frame,
                               textvariable=self.amount_var,
                               font=('Segoe UI', 14, 'bold'),
                               relief='flat',
                               bd=1,
                               width=15,
                               justify='right')
        amount_entry.configure(highlightbackground=BORDER_COLOR, highlightthickness=1)
        amount_entry.pack(side='right', fill='x', expand=True, ipady=8)

        # Offer % input (new) -------------------------------------------------
        offer_frame = tk.Frame(parent, bg=CARD_BG)
        offer_frame.pack(padx=15, pady=(6, 10), fill='x')

        self.offer_var = tk.StringVar(value="0")
        offer_entry = tk.Entry(offer_frame,
                               textvariable=self.offer_var,
                               font=('Segoe UI', 12),
                               width=6,
                               relief='flat',
                               bd=1,
                               justify='right')
        offer_entry.configure(highlightbackground=BORDER_COLOR, highlightthickness=1)
        offer_entry.pack(side='right', ipady=4)

        offer_label = tk.Label(offer_frame,
                               text="🎁 نسبة العرض % (اختياري)",
                               font=('Segoe UI', 10),
                               fg=TEXT_SECONDARY,
                               bg=CARD_BG)
        offer_label.pack(side='right', padx=(0, 10))
        # --------------------------------------------------------------------

        # Buttons frame
        buttons_frame = tk.Frame(parent, bg=CARD_BG)
        buttons_frame.pack(padx=15, pady=10, fill='x')
        
        # Write Balance button (sets exact amount)
        write_btn = tk.Button(buttons_frame,
                             text="✍ تعيين الرصيد",
                             font=('Segoe UI', 11, 'bold'),
                             bg=SECONDARY_COLOR,
                             fg='white',
                             relief='flat',
                             cursor='hand2',
                             padx=15,
                             pady=10,
                             command=self._write_balance)
        write_btn.pack(side='left', fill='x', expand=True, padx=(5, 0))

        # Top-Up button
        topup_btn = tk.Button(buttons_frame,
                             text="✓ إضافة إلى الرصيد",
                             font=('Segoe UI', 11, 'bold'),
                             bg=SUCCESS_COLOR,
                             fg='white',
                             relief='flat',
                             cursor='hand2',
                             padx=15,
                             pady=10,
                             command=self._top_up)
        topup_btn.pack(side='right', fill='x', expand=True, padx=(0, 5))

    def _create_balance_section(self, parent):
        """Create balance display section."""
        balance_frame = tk.Frame(parent, bg=SUCCESS_COLOR, relief='flat', bd=0)
        balance_frame.pack(padx=15, pady=10, fill='x', ipady=12)

        balance_label = tk.Label(balance_frame,
                                text="💵 الرصيد الحالي",
                                font=('Segoe UI', 10),
                                fg='white',
                                bg=SUCCESS_COLOR)
        balance_label.pack(anchor='e', padx=12, pady=(0, 5))

        self.balance_var = tk.StringVar(value="0.00 جنيه")
        balance_value = tk.Label(balance_frame,
                                textvariable=self.balance_var,
                                font=('Segoe UI', 20, 'bold'),
                                fg='white',
                                bg=SUCCESS_COLOR)
        balance_value.pack(anchor='e', padx=12)

    def _create_info_section(self, parent, title, var_name, default_value):
        """Create an information display section."""
        info_frame = tk.Frame(parent, bg=CARD_BG)
        info_frame.pack(padx=15, pady=5, fill='x')

        label = tk.Label(info_frame,
                        text=title,
                        font=('Segoe UI', 10),
                        fg=TEXT_SECONDARY,
                        bg=CARD_BG)
        label.pack(anchor='e')

        var = tk.StringVar(value=default_value)
        setattr(self, var_name.split('.')[-1], var)

        value = tk.Label(info_frame,
                        textvariable=var,
                        font=('Segoe UI', 11, 'bold'),
                        fg=TEXT_PRIMARY,
                        bg=CARD_BG,
                        wraplength=300,
                        justify='right')
        value.pack(anchor='e', pady=(3, 0))

        return var

    def _create_actions_panel(self, parent):
        """Create quick actions panel."""
        # Title
        title = tk.Label(parent,
                        text="🎯 الإجراءات السريعة",
                        font=('Segoe UI', 14, 'bold'),
                        fg=PRIMARY_COLOR,
                        bg=CARD_BG)
        title.pack(padx=15, pady=(15, 10), anchor='e')

        # Separator
        separator = ttk.Separator(parent, orient='horizontal')
        separator.pack(fill='x', padx=15, pady=(0, 15))

        # Actions list
        actions = [
            ("🎫 عرض جميع البطاقات", self._show_all_cards, SUCCESS_COLOR),
            ("📜 سجل البطاقات", self._show_card_history, SECONDARY_COLOR),
            ("🖨️ طباعة آخر إيصال", self._print_last_receipt, WARNING_COLOR),
            ("📄 طباعة ملخص البطاقة", self._print_card_summary, WARNING_COLOR),
            ("📅 تقرير يومي", self._generate_daily_report_manual, PRIMARY_COLOR),
            ("🗓 تقرير أسبوعي", self._generate_weekly_report_manual, PRIMARY_COLOR),
            ("📆 تقرير شهري", self._generate_monthly_report_manual, PRIMARY_COLOR),
            ("📈 تقرير سنوي", self._generate_yearly_report_manual, SECONDARY_COLOR),
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

        self.status_var = tk.StringVar(value="جاهز")
        status_label = tk.Label(footer_frame,
                               textvariable=self.status_var,
                               font=('Segoe UI', 10),
                               fg='white',
                               bg=TEXT_PRIMARY,
                               anchor='e')
        status_label.pack(fill='both', expand=True, padx=20, pady=12)

    def _check_serial_connection(self):
        """Check if serial connection is established."""
        if self.serial_service.is_connected:
            self.status_indicator.config(text=f"● متصل ({self.serial_service.port})", fg=SUCCESS_COLOR)
            self.status_var.set(f"متصل بـ {self.serial_service.port}")
        else:
            self.status_indicator.config(text="● غير متصل", fg=DANGER_COLOR)
            self.status_var.set("غير متصل بالأردوينو - تحقق من الإعدادات")

    def _read_card(self):
        """Read RFID card from Arduino with automatic database sync from card value."""
        # Immediate feedback - button clicked
        self.status_var.set("⏳ جاري قراءة البطاقة... يرجى الانتظار...")
        self.root.update()
        self.root.update_idletasks()
        
        # Check Arduino connection
        if not self.serial_service.is_connected:
            self.status_var.set("⚠️ الأردوينو غير متصل! يرجى استخدام الوضع اليدوي للاختبار.")
            self.root.update_idletasks()
            logger.warning("Read card attempted but Arduino not connected")
            return

        try:
            # Show loading indicator
            self.status_var.set("⏳ جاري تحميل البطاقة من الأردوينو... يرجى الانتظار...")
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
                    self.balance_var.set(f"{balance:.2f} جنيه")
                    
                    # Force UI update
                    self.root.update_idletasks()
                    
                    # Log the card read event (for audit)
                    self._log_card_read(card_uid, is_new=is_new_card)
                    
                    # Update status bar with result
                    if card_amount is not None and card_amount != db_balance:
                        self.status_var.set(f"🔄 تمت مزامنة البطاقة: {card_uid} | الرصيد: {balance:.2f} جنيه (كان {db_balance:.2f} في قاعدة البيانات)")
                    elif is_new_card:
                        self.status_var.set(f"✨ تم تحميل بطاقة جديدة: {card_uid} | الرصيد: {balance:.2f} جنيه")
                    else:
                        self.status_var.set(f"✓ تم تحميل البطاقة: {card_uid} | الرصيد: {balance:.2f} جنيه")
                    
                    logger.info(f"Card read and synced: {card_uid}, Balance: {balance:.2f} EGP, New: {is_new_card}")
                    
                    # Automatically read and display card history
                    self._read_and_show_history(card_uid)
                    
                except Exception as e:
                    logger.error(f"Database error while processing card: {e}")
                    self.status_var.set(f"❌ Database error: {str(e)}")
                    self.root.update_idletasks()
            else:
                # Only show error in status bar, not popup
                self.status_var.set(f"❌ فشلت قراءة البطاقة: {str(result)}")
                self.root.update_idletasks()
                logger.warning(f"Card read failed: {result}")
                
        except Exception as e:
            logger.error(f"Error in read card function: {e}")
            self.status_var.set(f"❌ خطأ: {str(e)}")
            self.root.update_idletasks()

    def _toggle_manual_mode(self):
        """Toggle manual card entry mode."""
        self.manual_mode = self.manual_mode_var.get()
        state = 'normal' if self.manual_mode else 'disabled'
        self.manual_uid_entry.config(state=state)
        self.manual_load_btn.config(state=state)

        if self.manual_mode:
            self.status_var.set("الوضع اليدوي: أدخل الرقم يدوياً")
        else:
            self._check_serial_connection()

    def _load_manual_card(self):
        """Load card manually with automatic database save."""
        raw_uid = self.manual_uid_var.get().strip()
        if not raw_uid:
            self.status_var.set("⚠️ يرجى إدخال رقم البطاقة")
            return

        # Show loading
        self.status_var.set("⏳ جاري تحميل البطاقة يدوياً... يرجى الانتظار...")
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
            self.balance_var.set(f"{balance:.2f} جنيه")
            
            # Log the event
            self._log_card_read(uid, is_new=is_new_card)
            
            # Update status bar (no popup)
            if is_new_card:
                self.status_var.set(f"✨ تم إنشاء بطاقة جديدة (يدوي): {uid} | الرصيد: {balance:.2f} جنيه")
            else:
                self.status_var.set(f"✓ تم تحميل البطاقة (يدوي): {uid} | الرصيد: {balance:.2f} جنيه")
            
            logger.info(f"Manual card loaded: {uid}, Balance: {balance:.2f} EGP, New: {is_new_card}")
            
        except Exception as e:
            logger.error(f"Manual load error: {e}")
            self.status_var.set(f"❌ فشل تحميل البطاقة: {str(e)}")

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
            messagebox.showwarning("لا توجد بطاقة", "اقرأ أو حمّل بطاقة أولاً.")
            return

        input_value = self.amount_var.get().strip()
        if not input_value:
            messagebox.showerror("إدخال فارغ", "يرجى إدخال قيمة.")
            return
        
        # Check if input is too long for card storage
        if len(input_value) > 11:
            messagebox.showerror("إدخال طويل جداً", "الحد الأقصى 11 حرف لتخزين البطاقة.")
            return

        # Parse input
        input_type, amount, display_value = self._parse_input(input_value)
        
        if input_type == 'numeric':
            # Regular numeric input - no confirmation
            self.status_var.set("جاري معالجة الشحن...")
            self.root.update_idletasks()
            if self.manual_mode:
                self._manual_top_up(amount, display_value)
            else:
                self._arduino_top_up(amount, display_value)
                    
        elif input_type == 'k_amount':
            # K-prefixed amount (e.g., K50) - no confirmation
            self.status_var.set("جاري معالجة شحن K-amount...")
            self.root.update_idletasks()
            if self.manual_mode:
                self._manual_top_up(amount, display_value)
            else:
                self._arduino_top_up(amount, display_value)
                    
        else:
            # String input - only write to card (keep confirmation for strings)
            if messagebox.askyesno("تأكيد", f"كتابة '{display_value}' على البطاقة {self.current_card_uid}؟\n\nملاحظة: لن يتم تحديث الرصيد في قاعدة البيانات."):
                self.status_var.set("جاري كتابة النص على البطاقة...")
                self.root.update_idletasks()
                if self.manual_mode:
                    messagebox.showinfo("الوضع اليدوي", "يمكن كتابة البيانات النصية فقط في وضع الأردوينو.\nالوضع اليدوي يدعم فقط تحديثات الرصيد الرقمي.")
                else:
                    self._arduino_write_string(display_value)

    def _print_receipt(self, card_uid, amount, balance_after, transaction_id):
        """Print receipt for transaction silently in background."""
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
                # Silent - just log it
                logger.info(f"Receipt saved to: {result}")
            else:
                logger.error(f"Receipt printing failed: {result}")
        except Exception as e:
            logger.error(f"Receipt printing error: {e}")
    
    def _manual_top_up(self, amount, display_value):
        """Handle manual top-up."""
        try:
            # calculate and apply offer percent if provided
            try:
                offer_percent = float(self.offer_var.get() or 0)
            except Exception:
                offer_percent = 0.0
            offer_percent = max(0.0, min(100.0, offer_percent))
            offer_amount = round(amount * (offer_percent / 100.0), 2) if offer_percent > 0 else 0.0
            total_amount = round(amount + offer_amount, 2)
            
            logger.info(f"Manual top-up: amount={amount}, offer_percent={offer_percent}, offer_amount={offer_amount}, total={total_amount}")
            
            new_bal, tx_id = self.db_service.top_up(
                self.current_card_uid,
                total_amount,
                employee=self.config.get("employee_name", "Receptionist"),
                notes=f"Manual entry: {display_value} | Offer: {offer_percent:.2f}% (+{offer_amount:.2f})"
            )
            
            # CRITICAL FIX: ALWAYS store offer_percent (even if 0) to ensure it's tracked
            try:
                if hasattr(self.db_service, 'conn'):
                    cursor = self.db_service.conn.cursor()
                    # First ensure the column exists (safe operation - will skip if exists)
                    try:
                        cursor.execute(
                            "ALTER TABLE cards ADD COLUMN offer_percent REAL DEFAULT 0"
                        )
                        self.db_service.conn.commit()
                        logger.info("Created offer_percent column in cards table")
                    except Exception as col_err:
                        logger.debug(f"Column already exists: {col_err}")
                    
                    # Now ALWAYS update the value (even if 0)
                    cursor.execute(
                        "UPDATE cards SET offer_percent = ? WHERE card_uid = ?",
                        (offer_percent, self.current_card_uid)
                    )
                    affected = cursor.rowcount
                    self.db_service.conn.commit()
                    cursor.close()
                    logger.info(f"✓ Stored offer_percent={offer_percent}% for card {self.current_card_uid} (rows affected: {affected})")
                    
                    # VERIFY the update was successful
                    cursor = self.db_service.conn.cursor()
                    cursor.execute("SELECT offer_percent FROM cards WHERE card_uid = ?", (self.current_card_uid,))
                    verify = cursor.fetchone()
                    cursor.close()
                    logger.info(f"VERIFICATION: offer_percent in DB is now {verify[0] if verify else 'NOT FOUND'}")
                    
                elif hasattr(self.db_service, 'update_card_offer'):
                    self.db_service.update_card_offer(self.current_card_uid, offer_percent)
                    logger.info(f"✓ Stored offer_percent={offer_percent}% for card {self.current_card_uid}")
            except Exception as e:
                logger.error(f"Failed to store offer_percent: {e}", exc_info=True)
            
            self._update_balance(new_bal)
    
            # Print receipt if enabled (silent)
            if self.auto_print_receipts:
                # send total amount (base + offer) to receipt
                self._print_receipt(self.current_card_uid, total_amount, new_bal, tx_id)
    
            self.status_var.set(f"✓ Added {amount:.2f} EGP (offer: {offer_percent}%) | New Balance: {new_bal:.2f} EGP (Manual)")
        except Exception as e:
            logger.error(f"Manual top-up error: {e}", exc_info=True)
            messagebox.showerror("DB Error", str(e))

    def _arduino_top_up(self, amount, display_value):
        """Handle Arduino top-up with numeric value."""
        # compute offer and total
        try:
            offer_percent = float(self.offer_var.get() or 0)
        except Exception:
            offer_percent = 0.0
        offer_percent = max(0.0, min(100.0, offer_percent))
        offer_amount = round(amount * (offer_percent / 100.0), 2) if offer_percent > 0 else 0.0
        total_amount = round(amount + offer_amount, 2)
        
        logger.info(f"Arduino top-up: amount={amount}, offer_percent={offer_percent}, offer_amount={offer_amount}, total={total_amount}")

        # Calculate new balance BEFORE writing to card
        new_balance_expected = self.current_balance + total_amount
        
        # Determine what to write to card (new total balance)
        if display_value.startswith('K'):
            card_write_value = f"K{new_balance_expected:.0f}"
        else:
            card_write_value = str(new_balance_expected)
        
        self.status_var.set(f"⏳ Writing '{card_write_value}' to card... KEEP CARD ON READER!")
        self.root.update()
        self.root.update_idletasks()
        
        success, uid, msg = self.serial_service.write_card(card_write_value)
        if success:
            try:
                new_bal, tx_id = self.db_service.top_up(
                    self.current_card_uid,
                    total_amount,
                    employee=self.config.get("employee_name", "Receptionist"),
                    notes=f"Arduino write: {card_write_value} (added {amount:.2f} + offer {offer_amount:.2f} [{offer_percent:.2f}%])"
                )
                
                # CRITICAL FIX: ALWAYS store offer_percent (even if 0) to ensure it's tracked
                try:
                    if hasattr(self.db_service, 'conn'):
                        cursor = self.db_service.conn.cursor()
                        # First ensure the column exists (safe operation - will skip if exists)
                        try:
                            cursor.execute(
                                "ALTER TABLE cards ADD COLUMN offer_percent REAL DEFAULT 0"
                            )
                            self.db_service.conn.commit()
                            logger.info("Created offer_percent column in cards table")
                        except Exception as col_err:
                            logger.debug(f"Column already exists: {col_err}")
                    
                        # Now ALWAYS update the value (even if 0)
                        cursor.execute(
                            "UPDATE cards SET offer_percent = ? WHERE card_uid = ?",
                            (offer_percent, self.current_card_uid)
                        )
                        affected = cursor.rowcount
                        self.db_service.conn.commit()
                        cursor.close()
                        logger.info(f"✓ Stored offer_percent={offer_percent}% for card {self.current_card_uid} (rows affected: {affected})")
                        
                        # VERIFY the update was successful
                        cursor = self.db_service.conn.cursor()
                        cursor.execute("SELECT offer_percent FROM cards WHERE card_uid = ?", (self.current_card_uid,))
                        verify = cursor.fetchone()
                        cursor.close()
                        logger.info(f"VERIFICATION: offer_percent in DB is now {verify[0] if verify else 'NOT FOUND'}")
                        
                    elif hasattr(self.db_service, 'update_card_offer'):
                        self.db_service.update_card_offer(self.current_card_uid, offer_percent)
                        logger.info(f"✓ Stored offer_percent={offer_percent}% for card {self.current_card_uid}")
                except Exception as e:
                    logger.error(f"Failed to store offer_percent: {e}", exc_info=True)
                
                self._update_balance(new_bal)
                
                # Print receipt if enabled (silent)
                if self.auto_print_receipts:
                    # print total (base + offer)
                    self._print_receipt(self.current_card_uid, total_amount, new_bal, tx_id)
                
                self.status_var.set(f"✓ Added {total_amount:.2f} EGP ({amount:.2f}+offer {offer_amount:.2f} [{offer_percent}%]) | Balance: {new_bal:.2f} EGP")
            except Exception as e:
                logger.error(f"DB error after write: {e}", exc_info=True)
                self.status_var.set(f"❌ Database error: {str(e)}")
                messagebox.showerror("DB Error", str(e))
        else:
            self.status_var.set(f"❌ Write failed: {msg}")
            logger.warning(f"Write failed: {msg}")

    def _arduino_write_string(self, text_data):
        """Handle Arduino string write (no database update)."""
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
        self.balance_var.set(f"{new_balance:.2f} جنيه")
        self.amount_var.set("")
        self.status_var.set("تمت عملية الشحن بنجاح")
    
    def _print_last_receipt(self):
        """Print receipt for last transaction."""
        if not self.current_card_uid:
            messagebox.showwarning("لا توجد بطاقة", "لا توجد بطاقة محملة. يرجى قراءة بطاقة أولاً.")
            return
        
        try:
            # Get last transaction for this card
            transactions = self.db_service.get_transactions(card_uid=self.current_card_uid)
            if not transactions:
                messagebox.showinfo("لا توجد معاملات", "لا توجد معاملات لهذا البطاقة.")
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
                    self.status_var.set(f"تم فتح الإيصال: {os.path.basename(result)}")
                except Exception as e:
                    self.status_var.set(f"تم حفظ الإيصال: {os.path.basename(result)}")
            else:
                messagebox.showerror("فشل الطباعة", result)
        except Exception as e:
            logger.error(f"Print last receipt error: {e}")
            messagebox.showerror("خطأ", str(e))
    
    def _print_card_summary(self):
        """Print complete card summary with transaction history."""
        if not self.current_card_uid:
            messagebox.showwarning("لا توجد بطاقة", "لا توجد بطاقة محملة. يرجى قراءة بطاقة أولاً.")
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
                    self.status_var.set(f"تم فتح الملخص: {os.path.basename(result)}")
                except Exception as e:
                    self.status_var.set(f"تم حفظ الملخص: {os.path.basename(result)}")
            else:
                messagebox.showerror("فشل الطباعة", result)
        except Exception as e:
            logger.error(f"Print card summary error: {e}")
            messagebox.showerror("خطأ", str(e))

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
        messagebox.showinfo("الإعدادات", "تم حفظ الإعدادات!")

    def _show_all_cards(self):
        """Show all cards dialog."""
        from rfid_reception.gui.dialogs.view_all_cards_dialog import ViewAllCardsDialog
        ViewAllCardsDialog(self.root, self.db_service)

   
    
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
            self.status_var.set(f"⏳ قراءة سجل اللعبة من البطاقة...")
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
                self.status_var.set(f"✓ تم تحميل البطاقة: {card_uid} | الرصيد: {self.current_balance:.2f} جنيه | تم عرض السجل")
            else:
                # History read failed, but don't interrupt the main flow
                logger.warning(f"Could not read history: {uid_or_error}")
                self.status_var.set(f"✓ تم تحميل البطاقة: {card_uid} | الرصيد: {self.current_balance:.2f} جنيه (السجل غير متوفر)")
                
        except Exception as e:
            logger.error(f"Error reading card history: {e}")
            # Don't show error popup, just log it
            self.status_var.set(f"✓ تم تحميل البطاقة: {card_uid} | الرصيد: {self.current_balance:.2f} جنيه")

    def _generate_daily_report_manual(self):
        try:
            date_str = simpledialog.askstring(
                "التقرير اليومي", "أدخل التاريخ (YYYY-MM-DD) أو اتركه فارغًا لليوم:", parent=self.root
            )
            
            # Compute date
            if date_str:
                try:
                    d = datetime.strptime(date_str, '%Y-%m-%d').date()
                except Exception:
                    messagebox.showerror("التقرير اليومي", "تنسيق التاريخ غير صالح. استخدم YYYY-MM-DD.")
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
                messagebox.showinfo("التقرير اليومي", f"تم فتح التقرير بنجاح!\n\nتم حفظه في:\n{path}")
            except Exception as e:
                messagebox.showinfo("التقرير اليومي", f"تم إنشاء التقرير:\n{path}\n\nيرجى فتحه يدويًا.")
        except Exception as e:
            logger.error(f"Daily report error: {e}")
            messagebox.showerror("التقرير اليومي", str(e))

        
    def _generate_weekly_report_manual(self):
        try:
            week_start = simpledialog.askstring(
                "التقرير الأسبوعي",
                "أدخل بداية الأسبوع (YYYY-MM-DD, الإثنين). اتركه فارغًا للأسبوع الحالي:",
                parent=self.root
            )
            
            # Determine start/end
            if week_start:
                try:
                    start = datetime.strptime(week_start, '%Y-%m-%d').date()
                except Exception:
                    messagebox.showerror("التقرير الأسبوعي", "تنسيق التاريخ غير صالح. استخدم YYYY-MM-DD.")
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
                messagebox.showinfo("التقرير الأسبوعي", f"تم فتح التقرير بنجاح!\n\nتم حفظه في:\n{path}")
            except Exception as e:
                messagebox.showinfo("التقرير الأسبوعي", f"تم إنشاء التقرير:\n{path}\n\nيرجى فتحه يدويًا.")
        except Exception as e:
            logger.error(f"Weekly report error: {e}")
            messagebox.showerror("التقرير الأسبوعي", str(e))

    def _generate_monthly_report_manual(self):
        try:
            m = simpledialog.askinteger(
                "التقرير الشهري", "أدخل الشهر (1-12):", initialvalue=datetime.now().month,
                minvalue=1, maxvalue=12, parent=self.root
            )
            y = simpledialog.askinteger(
                "التقرير الشهري", "أدخل السنة:", initialvalue=datetime.now().year,
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
                messagebox.showinfo("التقرير الشهري", f"تم فتح التقرير بنجاح!\n\nتم حفظه في:\n{path}")
            except Exception as e:
                messagebox.showinfo("التقرير الشهري", f"تم إنشاء التقرير:\n{path}\n\nيرجى فتحه يدويًا.")
        except Exception as e:
            logger.error(f"Monthly report error: {e}")
            messagebox.showerror("التقرير الشهري", str(e))

    def _generate_yearly_report_manual(self):
        try:
            y = simpledialog.askinteger(
                "التقرير السنوي", "أدخل السنة (فارغ للسنة الحالية):", initialvalue=datetime.now().year,
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
                messagebox.showinfo("التقرير السنوي", f"تم فتح التقرير بنجاح!\n\nتم حفظه في:\n{path}")
            except Exception as e:
                messagebox.showinfo("التقرير السنوي", f"تم إنشاء التقرير:\n{path}\n\nيرجى فتحه يدويًا.")
        except Exception as e:
            logger.error(f"Yearly report error: {e}")
            messagebox.showerror("التقرير السنوي", str(e))

    def _export_cards_to_pdf(self):
        """Export cards to PDF."""
        try:
            cards = self.db_service.get_all_cards()
            if not cards:
                messagebox.showwarning("لا توجد بطاقات", "لا توجد بطاقات متاحة للتصدير.")
                return

            file_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")],
                initialfile=f"cards_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            )
            if not file_path:
                return

            self.reports_generator.generate_beautiful_arabic_report(cards, output_path=file_path)
            messagebox.showinfo("نجاح التصدير", f"تم تصدير PDF إلى:\n{file_path}")
        except Exception as e:
            logger.error(f"Export error: {e}")
            messagebox.showerror("فشل التصدير", str(e))
    
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
            messagebox.showwarning("لا توجد بطاقة", "اقرأ أو حمّل بطاقة أولاً.")
            return

        input_value = self.amount_var.get().strip()
        if not input_value:
            messagebox.showerror("إدخال فارغ", "يرجى إدخال قيمة.")
            return
        
        # Check if input is too long
        if len(input_value) > 11:
            messagebox.showerror("إدخال طويل جداً", "الحد الأقصى 11 حرف.")
            return

        # Parse input
        input_type, amount, display_value = self._parse_input(input_value)
        
        if input_type == 'string':
            messagebox.showerror("إدخال غير صالح", "تعيين الرصيد يقبل فقط القيم الرقمية أو K-amounts (مثل، 50 أو K50).\nللنص، استخدم زر 'إضافة إلى الرصيد'.")
            return
        
        if amount < 0:
            messagebox.showerror("مبلغ غير صالح", "لا يمكن أن يكون المبلغ سالبًا.")
            return

        current_balance = self.current_balance
        difference = amount - current_balance
        
        # No confirmation - proceed directly
        self.status_var.set("جاري كتابة الرصيد...")
        self.root.update_idletasks()

        if self.manual_mode:
            self._manual_write_balance(amount, difference, display_value)
        else:
            self._arduino_write_balance(amount, difference, display_value)
    
    def _manual_write_balance(self, new_balance, difference, display_value):
        """Handle manual balance write."""
        try:
            if difference != 0:
                final_balance, tx_id = self.db_service.top_up(
                    self.current_card_uid,
                    difference,
                    employee=self.config.get("employee_name", "Receptionist"),
                    notes=f"Balance set to {new_balance:.2f} ({display_value}) - Manual entry"
                )
                self._update_balance(final_balance)
                
                # Print receipt if enabled (silent)
                if self.auto_print_receipts:
                    self._print_receipt(self.current_card_uid, difference, final_balance, tx_id)
                
                self.status_var.set(f"✓ تم تعيين الرصيد إلى {new_balance:.2f} جنيه (يدوي)")
            else:
                self.status_var.set("✓ الرصيد لم يتغير (موجود بالفعل بالمبلغ المحدد)")
        except Exception as e:
            logger.error(f"Manual balance write error: {e}")
            messagebox.showerror("DB Error", str(e))
    
    def _arduino_write_balance(self, new_balance, difference, display_value):
        """Handle Arduino balance write."""
        self.status_var.set(f"⏳ Writing '{display_value}' to card... KEEP CARD ON READER!")
        self.root.update()
        self.root.update_idletasks()
        
        success, uid, msg = self.serial_service.write_card(display_value)
        if success:
            try:
                if difference != 0:
                    final_balance, tx_id = self.db_service.top_up(
                        self.current_card_uid,
                        difference,
                        employee=self.config.get("employee_name", "Receptionist"),
                        notes=f"Balance set to {new_balance:.2f} ({display_value}) - Arduino write"
                    )
                    self._update_balance(final_balance)
                    
                    # Print receipt if enabled (silent)
                    if self.auto_print_receipts:
                        self._print_receipt(self.current_card_uid, difference, final_balance, tx_id)
                    
                    self.status_var.set(f"✓ تم تعيين الرصيد إلى {new_balance:.2f} جنيه | بطاقة: '{display_value}'")
                else:
                    self.status_var.set(f"✓ تم تحديث البطاقة بـ '{display_value}' (لا تغيير في الرصيد)")
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
                "الأردوينو غير متصل",
                "يرجى الاتصال بالأردوينو قبل تفعيل المسح التلقائي.\n\nانتقل إلى الإعدادات ← تكوين المنفذ التسلسلي للاتصال."
            )
            return
        
        if self.manual_mode:
            messagebox.showwarning(
                "الوضع اليدوي نشط",
                "المسح التلقائي غير متاح في الوضع اليدوي.\n\nقم بتعطيل الوضع اليدوي أولاً لاستخدام المسح التلقائي."
            )
            return
        
        self.auto_scan_enabled = True
        self.last_scanned_uid = None
        self.auto_scan_btn.config(
            text="⏸️ تعطيل المسح التلقائي",
            bg=WARNING_COLOR
        )
        self.status_var.set("🔄 تم تفعيل المسح التلقائي - ضع البطاقة على القارئ...")
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
            text="⚡ تفعيل المسح التلقائي",
            bg=SUCCESS_COLOR
        )
        self.status_var.set("تم تعطيل المسح التلقائي")
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
                                logger.info(f"✓ Auto-scan: Card and database already in sync: {balance}")
                        else:
                            # No card data, use database
                            balance = db_balance
                            logger.info(f"Auto-scan: Card has no numeric data, using database balance: {balance}")
                        
                        # Update UI
                        self.current_card_uid = card_uid
                        self.card_uid_var.set(card_uid)
                        self.current_balance = balance
                        self.balance_var.set(f"{balance:.2f} جنيه")
                        
                        # Log the event
                        self._log_card_read(card_uid, is_new=is_new_card)
                        
                        # Update status
                        if card_amount is not None and card_amount != db_balance:
                            self.status_var.set(f"🔄 تمت مزامنة البطاقة: {card_uid} | الرصيد: {balance:.2f} جنيه (كان {db_balance:.2f})")
                        elif is_new_card:
                            self.status_var.set(f"✨ تم اكتشاف بطاقة جديدة: {card_uid} | الرصيد: {balance:.2f} جنيه")
                        else:
                            self.status_var.set(f"✓ تم اكتشاف البطاقة: {card_uid} | الرصيد: {balance:.2f} جنيه")
                        
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
 