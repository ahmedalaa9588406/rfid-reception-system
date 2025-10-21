"""Dialog for manual card insertion with modern UI."""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Modern color palette
PRIMARY_COLOR = "#2E86AB"
SECONDARY_COLOR = "#A23B72"
SUCCESS_COLOR = "#06A77D"
WARNING_COLOR = "#F18F01"
LIGHT_BG = "#F5F5F5"
CARD_BG = "#FFFFFF"
TEXT_PRIMARY = "#2C3E50"
TEXT_SECONDARY = "#555555"
BORDER_COLOR = "#E0E0E0"


class ManualCardInsertDialog:
    """Dialog for manually inserting a new card into the database."""
    
    def __init__(self, parent, db_service):
        """Initialize the dialog."""
        self.parent = parent
        self.db_service = db_service
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Manual Card Insert - Add New Card")
        self.dialog.geometry("600x550")
        self.dialog.minsize(500, 450)
        self.dialog.resizable(True, True)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.configure(bg=LIGHT_BG)
        
        self._setup_styles()
        self._create_widgets()

        # Ensure dialog is raised and focused
        self.dialog.update_idletasks()
        try:
            self.dialog.lift()
            self.dialog.focus_force()
        except Exception:
            pass
    
    def _setup_styles(self):
        """Configure modern ttk styles."""
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure('Dialog.TLabel', 
                       font=('Segoe UI', 10),
                       background=LIGHT_BG,
                       foreground=TEXT_PRIMARY)
        
        style.configure('Dialog.Title.TLabel',
                       font=('Segoe UI', 16, 'bold'),
                       background=LIGHT_BG,
                       foreground=PRIMARY_COLOR)
    
    def _create_widgets(self):
        """Create and layout the dialog widgets."""
        # Header
        header_frame = tk.Frame(self.dialog, bg=PRIMARY_COLOR, height=70)
        header_frame.pack(fill='x', side='top')
        header_frame.pack_propagate(False)
        
        header_content = tk.Frame(header_frame, bg=PRIMARY_COLOR)
        header_content.pack(fill='both', expand=True, padx=20, pady=15)
        
        title_label = tk.Label(header_content,
                              text="✏️ Add New Card",
                              font=('Segoe UI', 18, 'bold'),
                              fg='white',
                              bg=PRIMARY_COLOR)
        title_label.pack(side='left', anchor='w')
        
        subtitle_label = tk.Label(header_content,
                                 text="Register a new card with initial information",
                                 font=('Segoe UI', 10),
                                 fg='#E8F4F8',
                                 bg=PRIMARY_COLOR)
        subtitle_label.pack(side='left', padx=(20, 0), anchor='w')
        
        # Main content frame
        main_frame = tk.Frame(self.dialog, bg=LIGHT_BG)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Card UID section
        uid_label = tk.Label(main_frame,
                            text="📋 Card UID *",
                            font=('Segoe UI', 11, 'bold'),
                            fg=PRIMARY_COLOR,
                            bg=LIGHT_BG)
        uid_label.pack(anchor='w', pady=(0, 5))
        
        self.uid_var = tk.StringVar()
        uid_entry = tk.Entry(main_frame,
                            textvariable=self.uid_var,
                            font=('Segoe UI', 11),
                            relief='flat',
                            bd=1)
        uid_entry.configure(highlightbackground=BORDER_COLOR,
                           highlightthickness=1)
        uid_entry.pack(fill='x', pady=(0, 15), ipady=8)
        uid_entry.focus_set()
        
        # Initial Balance section
        balance_label = tk.Label(main_frame,
                                text="💰 Initial Balance (EGP) *",
                                font=('Segoe UI', 11, 'bold'),
                                fg=PRIMARY_COLOR,
                                bg=LIGHT_BG)
        balance_label.pack(anchor='w', pady=(0, 5))
        
        self.balance_var = tk.StringVar(value="0.0")
        balance_entry = tk.Entry(main_frame,
                                textvariable=self.balance_var,
                                font=('Segoe UI', 11),
                                relief='flat',
                                bd=1)
        balance_entry.configure(highlightbackground=BORDER_COLOR,
                               highlightthickness=1)
        balance_entry.pack(fill='x', pady=(0, 15), ipady=8)
        
        # Employee Name section
        employee_label = tk.Label(main_frame,
                                 text="👤 Employee Name (Registrar) *",
                                 font=('Segoe UI', 11, 'bold'),
                                 fg=PRIMARY_COLOR,
                                 bg=LIGHT_BG)
        employee_label.pack(anchor='w', pady=(0, 5))
        
        self.employee_var = tk.StringVar()
        employee_entry = tk.Entry(main_frame,
                                 textvariable=self.employee_var,
                                 font=('Segoe UI', 11),
                                 relief='flat',
                                 bd=1)
        employee_entry.configure(highlightbackground=BORDER_COLOR,
                                highlightthickness=1)
        employee_entry.pack(fill='x', pady=(0, 15), ipady=8)
        
        # Notes section
        notes_label = tk.Label(main_frame,
                              text="📝 Notes (Optional)",
                              font=('Segoe UI', 11, 'bold'),
                              fg=PRIMARY_COLOR,
                              bg=LIGHT_BG)
        notes_label.pack(anchor='w', pady=(0, 5))
        
        self.notes_var = tk.StringVar()
        notes_entry = tk.Entry(main_frame,
                              textvariable=self.notes_var,
                              font=('Segoe UI', 11),
                              relief='flat',
                              bd=1)
        notes_entry.configure(highlightbackground=BORDER_COLOR,
                             highlightthickness=1)
        notes_entry.pack(fill='x', pady=(0, 20), ipady=8)
        
        # Info message
        info_label = tk.Label(main_frame,
                             text="* Required fields",
                             font=('Segoe UI', 9),
                             fg=TEXT_SECONDARY,
                             bg=LIGHT_BG)
        info_label.pack(anchor='w', pady=(0, 15))
        
        # Footer with buttons
        footer_frame = tk.Frame(self.dialog, bg=LIGHT_BG)
        footer_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        button_frame = tk.Frame(footer_frame, bg=LIGHT_BG)
        button_frame.pack(fill='x', pady=(10, 0))
        
        save_btn = tk.Button(button_frame,
                            text="✓ Save Card",
                            font=('Segoe UI', 11, 'bold'),
                            bg=SUCCESS_COLOR,
                            fg='white',
                            relief='flat',
                            cursor='hand2',
                            padx=20,
                            pady=10,
                            command=self._insert_card)
        save_btn.pack(side='left', padx=(0, 10), expand=True, fill='x')
        
        cancel_btn = tk.Button(button_frame,
                              text="✕ Cancel",
                              font=('Segoe UI', 11, 'bold'),
                              bg='#E8E8E8',
                              fg=TEXT_PRIMARY,
                              relief='flat',
                              cursor='hand2',
                              padx=20,
                              pady=10,
                              command=self.dialog.destroy)
        cancel_btn.pack(side='left', expand=True, fill='x')
        
        # Bind Enter key to save
        self.dialog.bind('<Return>', lambda e: self._insert_card())
        # Bind Escape key to cancel
        self.dialog.bind('<Escape>', lambda e: self.dialog.destroy())
    
    def _insert_card(self):
        """Insert the card into the database."""
        uid = self.uid_var.get().strip()
        balance_str = self.balance_var.get().strip()
        employee = self.employee_var.get().strip()
        notes = self.notes_var.get().strip()
        
        # Validation
        if not uid:
            messagebox.showerror("Validation Error", 
                               "Card UID is required.",
                               parent=self.dialog)
            return
        
        if not uid.replace('-', '').replace('_', '').replace(' ', '').isalnum():
            messagebox.showerror("Validation Error",
                               "Invalid UID format. Use alphanumeric characters only.",
                               parent=self.dialog)
            return
        
        try:
            balance = float(balance_str) if balance_str else 0.0
            if balance < 0:
                messagebox.showerror("Validation Error",
                                   "Initial balance cannot be negative.",
                                   parent=self.dialog)
                return
        except ValueError:
            messagebox.showerror("Validation Error",
                               "Please enter a valid initial balance.",
                               parent=self.dialog)
            return
        
        if not employee:
            messagebox.showerror("Validation Error",
                               "Employee name (registrar) is required.",
                               parent=self.dialog)
            return
        
        try:
            # Create or get the card
            card = self.db_service.create_or_get_card(uid)
            
            # If balance > 0, perform a top-up to set initial balance and log transaction
            if balance > 0:
                new_balance, transaction_id = self.db_service.top_up(
                    uid,
                    balance,
                    employee=employee,
                    notes=notes or 'Manual card insertion'
                )
                logger.info(
                    f"Card {uid} inserted with balance {balance} EGP "
                    f"by {employee} (Transaction ID: {transaction_id})"
                )
            else:
                new_balance = card.get('balance', 0)
                logger.info(f"Card {uid} inserted with zero balance by {employee}")
            
            # Update card with employee name if not already set
            if hasattr(self.db_service, 'update_card'):
                try:
                    self.db_service.update_card(uid, {'employee_name': employee})
                except Exception as e:
                    logger.warning(f"Could not update employee name: {e}")
            
            # Show success message
            messagebox.showinfo("Success",
                              f"✓ Card inserted successfully!\n\n"
                              f"UID: {uid}\n"
                              f"Balance: {new_balance:.2f} EGP\n"
                              f"Registrar: {employee}",
                              parent=self.dialog)
            self.dialog.destroy()
            
        except Exception as e:
            logger.exception(f"Error inserting card {uid}")
            messagebox.showerror("Error",
                               f"Failed to insert card:\n{str(e)}",
                               parent=self.dialog)