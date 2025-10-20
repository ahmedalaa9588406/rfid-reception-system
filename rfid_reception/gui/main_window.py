"""Main GUI window for RFID Reception System."""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class MainWindow:
    """Main application window."""
    
    def __init__(self, root, db_service, serial_service, reports_generator, scheduler, config):
        """Initialize the main window."""
        self.root = root
        self.db_service = db_service
        self.serial_service = serial_service
        self.reports_generator = reports_generator
        self.scheduler = scheduler
        self.config = config
        
        self.root.title("RFID Reception System")
        self.root.geometry("600x550")
        
        self.current_card_uid = None
        self.current_balance = 0.0
        self.manual_mode = False
        
        self._create_widgets()
        self._check_serial_connection()
    
    def _create_widgets(self):
        """Create and layout all widgets."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="RFID Reception System", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=10)
        
        # Card UID section
        ttk.Label(main_frame, text="Card UID:", font=('Arial', 10)).grid(
            row=1, column=0, sticky=tk.W, pady=5
        )
        self.card_uid_var = tk.StringVar(value="No card detected")
        ttk.Label(main_frame, textvariable=self.card_uid_var, 
                 font=('Arial', 10, 'bold')).grid(
            row=1, column=1, columnspan=2, sticky=tk.W, pady=5
        )
        
        # Balance section
        ttk.Label(main_frame, text="Current Balance:", font=('Arial', 10)).grid(
            row=2, column=0, sticky=tk.W, pady=5
        )
        self.balance_var = tk.StringVar(value="0.00 EGP")
        ttk.Label(main_frame, textvariable=self.balance_var, 
                 font=('Arial', 12, 'bold'), foreground='green').grid(
            row=2, column=1, columnspan=2, sticky=tk.W, pady=5
        )
        
        # Read Card button
        self.read_card_btn = ttk.Button(main_frame, text="Read Card", 
                  command=self._read_card)
        self.read_card_btn.grid(
            row=3, column=0, columnspan=3, pady=10, sticky=(tk.W, tk.E)
        )
        
        # Manual mode section
        manual_frame = ttk.LabelFrame(main_frame, text="Manual Entry Mode", padding="5")
        manual_frame.grid(row=4, column=0, columnspan=3, pady=10, sticky=(tk.W, tk.E))
        
        # Manual mode checkbox
        self.manual_mode_var = tk.BooleanVar(value=False)
        manual_check = ttk.Checkbutton(manual_frame, text="Use Manual Entry", 
                                       variable=self.manual_mode_var,
                                       command=self._toggle_manual_mode)
        manual_check.grid(row=0, column=0, sticky=tk.W, pady=5)
        
        # Manual UID entry
        ttk.Label(manual_frame, text="Card UID:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.manual_uid_var = tk.StringVar()
        self.manual_uid_entry = ttk.Entry(manual_frame, textvariable=self.manual_uid_var, 
                                          font=('Arial', 10), width=30, state='disabled')
        self.manual_uid_entry.grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)
        
        self.manual_load_btn = ttk.Button(manual_frame, text="Load Card", 
                                          command=self._load_manual_card, state='disabled')
        self.manual_load_btn.grid(row=1, column=2, pady=5)
        
        # Amount input section
        ttk.Label(main_frame, text="Top-Up Amount:", font=('Arial', 10)).grid(
            row=5, column=0, sticky=tk.W, pady=5
        )
        self.amount_var = tk.StringVar()
        amount_entry = ttk.Entry(main_frame, textvariable=self.amount_var, 
                                font=('Arial', 12), width=15)
        amount_entry.grid(row=5, column=1, sticky=tk.W, pady=5)
        ttk.Label(main_frame, text="EGP").grid(row=5, column=2, sticky=tk.W, pady=5)
        
        # Quick amount buttons
        quick_frame = ttk.LabelFrame(main_frame, text="Quick Amounts", padding="5")
        quick_frame.grid(row=6, column=0, columnspan=3, pady=10, sticky=(tk.W, tk.E))
        
        amounts = [10, 20, 50, 100]
        for i, amount in enumerate(amounts):
            ttk.Button(quick_frame, text=f"{amount} EGP", 
                      command=lambda a=amount: self.amount_var.set(str(a))).grid(
                row=0, column=i, padx=5, pady=5
            )
        
        # Top-Up button
        ttk.Button(main_frame, text="Top-Up", 
                  command=self._top_up, 
                  style='Accent.TButton').grid(
            row=7, column=0, columnspan=3, pady=15, sticky=(tk.W, tk.E)
        )
        
        # Action buttons frame
        actions_frame = ttk.Frame(main_frame)
        actions_frame.grid(row=8, column=0, columnspan=3, pady=10, sticky=(tk.W, tk.E))
        
        ttk.Button(actions_frame, text="View Transactions", 
                  command=self._show_transactions).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(actions_frame, text="Generate Report", 
                  command=self._generate_report).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(actions_frame, text="Settings", 
                  command=self._show_settings).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, 
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=9, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
    
    def _check_serial_connection(self):
        """Check if serial connection is established."""
        if self.serial_service.is_connected:
            self.status_var.set(f"Connected to {self.serial_service.port}")
        else:
            self.status_var.set("Not connected to Arduino - Check settings or use manual mode")
    
    def _toggle_manual_mode(self):
        """Toggle between manual and Arduino mode."""
        self.manual_mode = self.manual_mode_var.get()
        
        if self.manual_mode:
            # Enable manual mode
            self.manual_uid_entry.config(state='normal')
            self.manual_load_btn.config(state='normal')
            self.read_card_btn.config(state='disabled')
            self.status_var.set("Manual Entry Mode: Enter card UID manually")
        else:
            # Disable manual mode
            self.manual_uid_entry.config(state='disabled')
            self.manual_load_btn.config(state='disabled')
            self.read_card_btn.config(state='normal')
            self._check_serial_connection()
    
    def _load_manual_card(self):
        """Load a card using manually entered UID."""
        uid = self.manual_uid_var.get().strip()
        
        if not uid:
            messagebox.showwarning("Warning", "Please enter a card UID.")
            return
        
        # Validate UID format (basic validation - alphanumeric and some special chars)
        if not uid.replace('-', '').replace('_', '').isalnum():
            messagebox.showerror("Error", "Invalid UID format. Use alphanumeric characters only.")
            return
        
        self.current_card_uid = uid
        self.card_uid_var.set(uid)
        
        # Get current balance from database
        balance = self.db_service.get_card_balance(uid)
        self.current_balance = balance
        self.balance_var.set(f"{balance:.2f} EGP")
        
        self.status_var.set(f"Manual mode: Card {uid} loaded")
        messagebox.showinfo("Success", f"Card loaded: {uid}\nBalance: {balance:.2f} EGP")
    
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
            messagebox.showwarning("Warning", "Please read a card or enter a card UID first.")
            return
        
        try:
            amount = float(self.amount_var.get())
            if amount <= 0:
                messagebox.showerror("Error", "Amount must be greater than 0.")
                return
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid amount.")
            return
        
        # Check if we need Arduino connection for non-manual mode
        if not self.manual_mode and not self.serial_service.is_connected:
            messagebox.showerror("Error", "Not connected to Arduino. Please check settings or use manual mode.")
            return
        
        # Confirm top-up
        mode_text = "Manual Mode" if self.manual_mode else "Arduino Mode"
        confirm = messagebox.askyesno(
            "Confirm Top-Up",
            f"Top-up {amount:.2f} EGP to card {self.current_card_uid}?\n\nMode: {mode_text}"
        )
        
        if not confirm:
            return
        
        self.status_var.set("Processing top-up...")
        self.root.update()
        
        # Handle top-up based on mode
        if self.manual_mode:
            # Manual mode: Skip Arduino write, only update database
            try:
                new_balance, transaction_id = self.db_service.top_up(
                    self.current_card_uid, 
                    amount,
                    employee=self.config.get('employee_name', 'Receptionist'),
                    notes='Manual entry mode'
                )
                
                self.current_balance = new_balance
                self.balance_var.set(f"{new_balance:.2f} EGP")
                self.amount_var.set("")
                
                self.status_var.set("Top-up successful (Manual mode)")
                messagebox.showinfo(
                    "Success", 
                    f"Top-up successful! (Manual Mode)\n\nCard: {self.current_card_uid}\n"
                    f"Amount: {amount:.2f} EGP\nNew Balance: {new_balance:.2f} EGP\n\n"
                    f"Note: Card was not physically written to."
                )
            except Exception as e:
                logger.error(f"Database error during manual top-up: {e}")
                messagebox.showerror("Error", f"Failed to save to database: {e}")
                self.status_var.set("Database error")
        else:
            # Arduino mode: Write to card and update database
            success, uid, message = self.serial_service.write_card(amount)
            
            if success:
                try:
                    # Save to database
                    new_balance, transaction_id = self.db_service.top_up(
                        self.current_card_uid, 
                        amount,
                        employee=self.config.get('employee_name', 'Receptionist')
                    )
                    
                    self.current_balance = new_balance
                    self.balance_var.set(f"{new_balance:.2f} EGP")
                    self.amount_var.set("")
                    
                    self.status_var.set("Top-up successful")
                    messagebox.showinfo(
                        "Success", 
                        f"Top-up successful!\n\nCard: {self.current_card_uid}\n"
                        f"Amount: {amount:.2f} EGP\nNew Balance: {new_balance:.2f} EGP"
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
