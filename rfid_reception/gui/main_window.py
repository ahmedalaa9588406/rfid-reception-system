"""Main GUI window for RFID Reception System."""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import logging
from datetime import datetime
from rfid_reception.reports import ModernReportsGenerator

logger = logging.getLogger(__name__)


class MainWindow:
    """Main application window."""

    def __init__(self, root, db_service, serial_service, reports_generator, scheduler, config):
        """Initialize the main window."""
        self.root = root
        self.db_service = db_service
        self.serial_service = serial_service
        self.reports_generator = ModernReportsGenerator(db_service)
        self.scheduler = scheduler
        self.config = config

        self.root.title("RFID Reception System")
        self.root.geometry("600x550")

        self.current_card_uid = None
        self.current_balance = 0.0

        self._create_widgets()
        self._check_serial_connection()

    def _create_widgets(self):
        """Create and layout all widgets."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Title
        title_label = ttk.Label(main_frame, text="RFID Reception System", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=10)

        # Card UID section
        ttk.Label(main_frame, text="Card UID:", font=("Arial", 10)).grid(row=1, column=0, sticky=tk.W, pady=5)
        self.card_uid_var = tk.StringVar(value="No card detected")
        ttk.Label(main_frame, textvariable=self.card_uid_var, font=("Arial", 10, "bold")).grid(
            row=1, column=1, columnspan=2, sticky=tk.W, pady=5
        )

        # Balance section
        ttk.Label(main_frame, text="Current Balance:", font=("Arial", 10)).grid(row=2, column=0, sticky=tk.W, pady=5)
        self.balance_var = tk.StringVar(value="0.00 EGP")
        ttk.Label(main_frame, textvariable=self.balance_var, font=("Arial", 12, "bold"), foreground="green").grid(
            row=2, column=1, columnspan=2, sticky=tk.W, pady=5
        )

        # Read Card button
        self.read_card_btn = ttk.Button(main_frame, text="Read Card", command=self._read_card)
        self.read_card_btn.grid(row=3, column=0, columnspan=3, pady=10, sticky=(tk.W, tk.E))

        # Amount input section
        ttk.Label(main_frame, text="Top-Up Amount:", font=("Arial", 10)).grid(row=4, column=0, sticky=tk.W, pady=5)
        self.amount_var = tk.StringVar()
        amount_entry = ttk.Entry(main_frame, textvariable=self.amount_var, font=("Arial", 12), width=15)
        amount_entry.grid(row=4, column=1, sticky=tk.W, pady=5)
        ttk.Label(main_frame, text="EGP").grid(row=4, column=2, sticky=tk.W, pady=5)

        # Quick amount buttons
        quick_frame = ttk.LabelFrame(main_frame, text="Quick Amounts", padding="5")
        quick_frame.grid(row=5, column=0, columnspan=3, pady=10, sticky=(tk.W, tk.E))

        amounts = [10, 20, 50, 100]
        for i, amount in enumerate(amounts):
            ttk.Button(quick_frame, text=f"{amount} EGP", command=lambda a=amount: self.amount_var.set(str(a))).grid(
                row=0, column=i, padx=5, pady=5
            )

        # Top-Up button
        ttk.Button(main_frame, text="Top-Up", command=self._top_up, style="Accent.TButton").grid(
            row=6, column=0, columnspan=3, pady=15, sticky=(tk.W, tk.E)
        )

        # Action buttons frame
        actions_frame = ttk.Frame(main_frame)
        actions_frame.grid(row=7, column=0, columnspan=3, pady=10, sticky=(tk.W, tk.E))

        ttk.Button(actions_frame, text="View Transactions", command=self._show_transactions).pack(
            side=tk.LEFT, padx=5, fill=tk.X, expand=True
        )
        ttk.Button(actions_frame, text="Generate Report", command=self._generate_report).pack(
            side=tk.LEFT, padx=5, fill=tk.X, expand=True
        )
        ttk.Button(actions_frame, text="Settings", command=self._show_settings).pack(
            side=tk.LEFT, padx=5, fill=tk.X, expand=True
        )
        ttk.Button(actions_frame, text="View All Cards", command=self._show_all_cards).pack(
            side=tk.LEFT, padx=5, fill=tk.X, expand=True
        )
        ttk.Button(actions_frame, text="Insert Card Manual", command=self._show_manual_card_insert).pack(
            side=tk.LEFT, padx=5, fill=tk.X, expand=True
        )
        ttk.Button(actions_frame, text="Export to PDF", command=self._export_cards_to_pdf).pack(
            side=tk.LEFT, padx=5, fill=tk.X, expand=True
        )

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=8, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

    def _check_serial_connection(self):
        """Check if serial connection is established."""
        if self.serial_service.is_connected:
            self.status_var.set(f"Connected to {self.serial_service.port}")
        else:
            self.status_var.set("Not connected to Arduino - Check settings")

    def _read_card(self):
        """Read RFID card from Arduino."""
        if not self.serial_service.is_connected:
            messagebox.showerror("Error", "Not connected to Arduino. Please check settings.")
            return

        self.status_var.set("Reading card...")
        self.root.update()

        success, result = self.serial_service.read_card()

        if success:
            self.current_card_uid = result
            self.card_uid_var.set(result)

            # Get current balance from database
            balance = self.db_service.get_card_balance(result)
            self.current_balance = balance
            self.balance_var.set(f"{balance:.2f} EGP")

            self.status_var.set("Card read successfully")
            messagebox.showinfo("Success", f"Card detected: {result}\nBalance: {balance:.2f} EGP")
        else:
            self.status_var.set("Failed to read card")
            messagebox.showerror("Error", f"Failed to read card: {result}")

    def _top_up(self):
        """Perform top-up operation."""
        if not self.current_card_uid:
            messagebox.showwarning("Warning", "Please read a card first.")
            return

        try:
            amount = float(self.amount_var.get())
            if amount <= 0:
                messagebox.showerror("Error", "Amount must be greater than 0.")
                return
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid amount.")
            return

        if not self.serial_service.is_connected:
            messagebox.showerror("Error", "Not connected to Arduino. Please check settings.")
            return

        # Confirm top-up
        confirm = messagebox.askyesno(
            "Confirm Top-Up",
            f"Top-up {amount:.2f} EGP to card {self.current_card_uid}?",
        )

        if not confirm:
            return

        self.status_var.set("Processing top-up...")
        self.root.update()

        # Write to card and update database
        success, uid, message = self.serial_service.write_card(amount)

        if success:
            try:
                # Save to database
                new_balance, transaction_id = self.db_service.top_up(
                    self.current_card_uid, amount, employee=self.config.get("employee_name", "Receptionist")
                )

                self.current_balance = new_balance
                self.balance_var.set(f"{new_balance:.2f} EGP")
                self.amount_var.set("")

                self.status_var.set("Top-up successful")
                messagebox.showinfo(
                    "Success",
                    f"Top-up successful!\n\nCard: {self.current_card_uid}\n"
                    f"Amount: {amount:.2f} EGP\nNew Balance: {new_balance:.2f} EGP",
                )
            except Exception as e:
                logger.error(f"Database error during top-up: {e}")
                messagebox.showerror("Error", f"Failed to save to database: {e}")
                self.status_var.set("Database error")
        else:
            self.status_var.set("Top-up failed")
            messagebox.showerror("Error", f"Failed to write to card: {message}")

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
        messagebox.showinfo("Settings", "Settings saved successfully!")

    def _show_all_cards(self):
        """Show all cards dialog."""
        from rfid_reception.gui.dialogs.view_all_cards_dialog import ViewAllCardsDialog

        ViewAllCardsDialog(self.root, self.db_service)

    def _toggle_manual_mode(self):
        self.manual_mode = self.manual_mode_var.get()
        state = NORMAL if self.manual_mode else DISABLED
        self.manual_uid_entry.config(state=state)
        self.manual_load_btn.config(state=state)
        self.read_card_btn.config(state=DISABLED if self.manual_mode else NORMAL)

        if self.manual_mode:
            self.status_var.set("Manual Mode: Enter UID manually")
        else:
            self._check_serial_connection()

    def _load_manual_card(self):
        uid = self.manual_uid_var.get().strip()
        if not uid:
            messagebox.showwarning("Input Required", "Enter a card UID.")
            return
        if not uid.replace("-", "").replace("_", "").isalnum():
            messagebox.showerror("Invalid UID", "Use alphanumeric characters only.")
            return

        self.current_card_uid = uid
        self.card_uid_var.set(uid)
        balance = self.db_service.get_card_balance(uid)
        self.current_balance = balance
        self.balance_var.set(f"{balance:.2f} EGP")
        self.status_var.set(f"Manual Card Loaded: {uid}")
        messagebox.showinfo("Loaded", f"UID: {uid}\nBalance: {balance:.2f} EGP")

    # ------------------------------------------------------------------ #
    # Core Actions
    # ------------------------------------------------------------------ #
    def _read_card(self):
        if not self.serial_service.is_connected:
            messagebox.showerror("Connection Error", "Arduino not connected.")
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

            # Auto-register new card
            try:
                card = self.db_service.create_or_get_card(result)
                messagebox.showinfo("Success", f"Card saved!\nUID: {result}\nBalance: {balance:.2f} EGP")
            except Exception as e:
                logger.error(f"DB save error: {e}")
                messagebox.showwarning("Partial Success", f"Read OK, but DB error: {e}")
        else:
            self.status_var.set("Read failed")
            messagebox.showerror("Read Error", str(result))

    def _top_up(self):
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
        self.current_balance = new_balance
        self.balance_var.set(f"{new_balance:.2f} EGP")
        self.amount_var.set("")
        self.status_var.set("Top-up successful")

    # ------------------------------------------------------------------ #
    # Dialog Openers
    # ------------------------------------------------------------------ #
    def _show_transactions(self):
        from rfid_reception.gui.dialogs import TransactionsDialog
        TransactionsDialog(self.root, self.db_service)

    def _generate_report(self):
        from rfid_reception.gui.dialogs import ReportDialog
        ReportDialog(self.root, self.reports_generator)

    def _show_settings(self):
        from rfid_reception.gui.dialogs import SettingsDialog
        SettingsDialog(self.root, self.config, self.serial_service, self._on_settings_saved)

    def _on_settings_saved(self):
        self._check_serial_connection()
        messagebox.showinfo("Settings", "Settings saved!")

    def _show_all_cards(self):
        from rfid_reception.gui.dialogs.view_all_cards_dialog import ViewAllCardsDialog
        ViewAllCardsDialog(self.root, self.db_service)

    def _show_manual_card_insert(self):
        from rfid_reception.gui.dialogs.manual_card_insert_dialog import ManualCardInsertDialog
        ManualCardInsertDialog(self.root, self.db_service)

    def _export_cards_to_pdf(self):
        """Export selected cards to a PDF file."""
        selected_cards = self._get_selected_cards()
        if not selected_cards:
            messagebox.showwarning("No Selection", "Please select cards to export.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=f"cards_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        )
        if not file_path:
            return

        try:
            transactions_map = {}
            for card in selected_cards:
                try:
                    transactions_map[card['card_uid']] = self.db_service.get_transactions(card_uid=card['card_uid'])
                except Exception as e:
                    logging.error(f"Failed to fetch transactions for card {card['card_uid']}: {e}")
                    transactions_map[card['card_uid']] = []

            self.reports_generator.generate_cards_pdf(
                cards=selected_cards,
                transactions_map=transactions_map,
                output_path=file_path
            )
            messagebox.showinfo("Export Successful", f"PDF exported successfully to:\n{file_path}")
        except Exception as e:
            logging.error(f"Error exporting cards to PDF: {e}")
            messagebox.showerror("Export Failed", f"An error occurred while exporting to PDF:\n{e}")

    def _get_selected_cards(self):
        """Retrieve selected cards from the UI."""
        # Implement logic to fetch selected cards based on your UI structure.
        # This is a placeholder and should be replaced with actual implementation.
        return []
