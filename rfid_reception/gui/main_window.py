"""Main GUI window for RFID Reception System with modern design."""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import logging
from datetime import datetime, timedelta
from rfid_reception.reports import ModernReportsGenerator

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

        self.root.title("RFID Reception System")
        self.root.geometry("1100x750")
        self.root.minsize(900, 600)
        self.root.configure(bg=LIGHT_BG)

        self.current_card_uid = None
        self.current_balance = 0.0
        self.manual_mode = False

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

        # Read Card button
        read_btn = tk.Button(parent,
                            text="🔍 Read Card",
                            font=('Segoe UI', 12, 'bold'),
                            bg=PRIMARY_COLOR,
                            fg='white',
                            relief='flat',
                            cursor='hand2',
                            padx=20,
                            pady=12,
                            command=self._read_card)
        read_btn.pack(padx=15, pady=15, fill='x')

        # Spacer
        spacer = ttk.Frame(parent, height=20)
        spacer.pack()

        # Top-Up section separator
        sep2 = ttk.Separator(parent, orient='horizontal')
        sep2.pack(fill='x', padx=15, pady=10)

        # Top-Up amount section
        topup_label = tk.Label(parent,
                              text="💰 Top-Up Amount",
                              font=('Segoe UI', 12, 'bold'),
                              fg=PRIMARY_COLOR,
                              bg=CARD_BG)
        topup_label.pack(padx=15, pady=(10, 5), anchor='w')

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

        # Top-Up button
        topup_btn = tk.Button(parent,
                             text="✓ Confirm Top-Up",
                             font=('Segoe UI', 12, 'bold'),
                             bg=SUCCESS_COLOR,
                             fg='white',
                             relief='flat',
                             cursor='hand2',
                             padx=20,
                             pady=12,
                             command=self._top_up)
        topup_btn.pack(padx=15, pady=15, fill='x')

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
        """Read RFID card from Arduino."""
        if not self.serial_service.is_connected:
            messagebox.showerror("Connection Error", "Arduino not connected. Please check settings.")
            return

        self.status_var.set("Reading card...")
        self.root.update_idletasks()

        success, result = self.serial_service.read_card()

        if success:
            self.current_card_uid = result
            self.card_uid_var.set(result)
            balance = self.db_service.get_card_balance(result)
            self.current_balance = balance
            self.balance_var.set(f"{balance:.2f} EGP")
            self.status_var.set("Card read successfully")

            try:
                card = self.db_service.create_or_get_card(result)
                messagebox.showinfo("Success", f"Card detected!\nUID: {result}\nBalance: {balance:.2f} EGP")
            except Exception as e:
                logger.error(f"DB save error: {e}")
                messagebox.showwarning("Partial Success", f"Read OK, but DB error: {e}")
        else:
            self.status_var.set("Read failed")
            messagebox.showerror("Read Error", str(result))

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
        """Load card manually."""
        uid = self.manual_uid_var.get().strip()
        if not uid:
            messagebox.showwarning("Input Required", "Enter a card UID.")
            return

        self.current_card_uid = uid
        self.card_uid_var.set(uid)
        balance = self.db_service.get_card_balance(uid)
        self.current_balance = balance
        self.balance_var.set(f"{balance:.2f} EGP")
        self.status_var.set(f"Manual Card Loaded: {uid}")
        messagebox.showinfo("Loaded", f"UID: {uid}\nBalance: {balance:.2f} EGP")

    def _top_up(self):
        """Perform top-up operation."""
        if not self.current_card_uid:
            messagebox.showwarning("No Card", "Read or load a card first.")
            return

        try:
            amount = float(self.amount_var.get() or 0)
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Amount", "Enter a positive number.")
            return

        mode = "Manual" if self.manual_mode else "Arduino"
        if messagebox.askyesno("Confirm", f"Add {amount:.2f} EGP to {self.current_card_uid}?\nMode: {mode}"):
            self.status_var.set("Processing top-up...")
            self.root.update_idletasks()

            if self.manual_mode:
                self._manual_top_up(amount)
            else:
                self._arduino_top_up(amount)

    def _manual_top_up(self, amount):
        """Handle manual top-up."""
        try:
            new_bal, tx_id = self.db_service.top_up(
                self.current_card_uid,
                amount,
                employee=self.config.get("employee_name", "Receptionist"),
                notes="Manual entry"
            )
            self._update_balance(new_bal)
            messagebox.showinfo(
                "Success (Manual)",
                f"Added {amount:.2f} EGP\nNew Balance: {new_bal:.2f} EGP\n(Note: Card not written)"
            )
        except Exception as e:
            logger.error(f"Manual top-up error: {e}")
            messagebox.showerror("DB Error", str(e))

    def _arduino_top_up(self, amount):
        """Handle Arduino top-up."""
        success, uid, msg = self.serial_service.write_card(amount)
        if success:
            try:
                new_bal, tx_id = self.db_service.top_up(
                    self.current_card_uid,
                    amount,
                    employee=self.config.get("employee_name", "Receptionist")
                )
                self._update_balance(new_bal)
                messagebox.showinfo("Success", f"Added {amount:.2f} EGP\nNew Balance: {new_bal:.2f} EGP")
            except Exception as e:
                logger.error(f"DB error after write: {e}")
                messagebox.showerror("DB Error", str(e))
        else:
            messagebox.showerror("Write Failed", msg)

    def _update_balance(self, new_balance):
        """Update balance display."""
        self.current_balance = new_balance
        self.balance_var.set(f"{new_balance:.2f} EGP")
        self.amount_var.set("")
        self.status_var.set("Top-up successful")

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

    def _generate_daily_report_manual(self):
        try:
            date_str = simpledialog.askstring(
                "Daily Report", "Enter date (YYYY-MM-DD) or leave blank for today:", parent=self.root
            )
            # Compute default filename
            if date_str:
                try:
                    d = datetime.strptime(date_str, '%Y-%m-%d').date()
                except Exception:
                    messagebox.showerror("Daily Report", "Invalid date format. Use YYYY-MM-DD.")
                    return
            else:
                d = datetime.now().date()

            default_name = f"daily_report_{d.strftime('%Y%m%d')}.pdf"
            save_path = filedialog.asksaveasfilename(
                title="Save Daily Report As",
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")],
                initialfile=default_name,
                parent=self.root
            )
            if not save_path:
                return

            if date_str:
                path = self.reports_generator.generate_daily_report(date_str, output_path=save_path)
            else:
                path = self.reports_generator.generate_daily_report(output_path=save_path)
            messagebox.showinfo("Daily Report", f"Generated:\n{path}")
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
            # Determine start/end for default filename
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

            default_name = f"weekly_report_{start.strftime('%Y%m%d')}_to_{end.strftime('%Y%m%d')}.pdf"
            save_path = filedialog.asksaveasfilename(
                title="Save Weekly Report As",
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")],
                initialfile=default_name,
                parent=self.root
            )
            if not save_path:
                return

            if week_start:
                path = self.reports_generator.generate_weekly_report(week_start, output_path=save_path)
            else:
                path = self.reports_generator.generate_weekly_report(output_path=save_path)
            messagebox.showinfo("Weekly Report", f"Generated:\n{path}")
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
            default_name = f"monthly_report_{y}{m:02d}.pdf"
            save_path = filedialog.asksaveasfilename(
                title="Save Monthly Report As",
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")],
                initialfile=default_name,
                parent=self.root
            )
            if not save_path:
                return
            path = self.reports_generator.generate_monthly_report(m, y, output_path=save_path)
            messagebox.showinfo("Monthly Report", f"Generated:\n{path}")
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
            default_name = f"yearly_report_{y}.pdf"
            save_path = filedialog.asksaveasfilename(
                title="Save Yearly Report As",
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")],
                initialfile=default_name,
                parent=self.root
            )
            if not save_path:
                return
            path = self.reports_generator.generate_yearly_report(y, output_path=save_path)
            messagebox.showinfo("Yearly Report", f"Generated:\n{path}")
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


# Backward compatibility alias
MainWindow = ModernMainWindow
