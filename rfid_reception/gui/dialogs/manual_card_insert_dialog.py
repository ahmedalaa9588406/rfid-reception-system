"""Dialog for manual card insertion."""

import tkinter as tk
from tkinter import ttk, messagebox
import logging

logger = logging.getLogger(__name__)


class ManualCardInsertDialog:
    """Dialog for manually inserting a new card into the database."""
    
    def __init__(self, parent, db_service):
        """Initialize the dialog."""
        self.parent = parent
        self.db_service = db_service
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Manual Card Insert")
        self.dialog.geometry("500x360")
        self.dialog.minsize(450, 320)
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self._create_widgets()

        # Ensure dialog is raised and focused
        self.dialog.update_idletasks()
        try:
            self.dialog.lift()
            self.dialog.focus_force()
        except Exception:
            pass
    
    def _create_widgets(self):
        """Create and layout the dialog widgets."""
        frame = ttk.Frame(self.dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        ttk.Label(
            frame, 
            text="Manual Card Insertion", 
            font=('Arial', 14, 'bold')
        ).pack(pady=10)
        
        # Card UID
        ttk.Label(frame, text="Card UID:").pack(anchor=tk.W, pady=5)
        self.uid_var = tk.StringVar()
        uid_entry = ttk.Entry(
            frame, 
            textvariable=self.uid_var, 
            font=('Arial', 10), 
            width=30
        )
        uid_entry.pack(pady=5, fill=tk.X)
        uid_entry.focus_set()

        # Initial Balance
        ttk.Label(frame, text="Initial Balance (EGP):").pack(anchor=tk.W, pady=5)
        self.balance_var = tk.StringVar(value="0.0")
        balance_entry = ttk.Entry(
            frame, 
            textvariable=self.balance_var, 
            font=('Arial', 10), 
            width=30
        )
        balance_entry.pack(pady=5, fill=tk.X)

        # Employee Name
        ttk.Label(frame, text="Employee Name:").pack(anchor=tk.W, pady=5)
        self.employee_var = tk.StringVar()
        employee_entry = ttk.Entry(
            frame, 
            textvariable=self.employee_var, 
            font=('Arial', 10), 
            width=30
        )
        employee_entry.pack(pady=5, fill=tk.X)

        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=20, fill=tk.X)

        ttk.Button(
            button_frame, 
            text="Save to DB", 
            command=self._insert_card
        ).pack(side=tk.LEFT, padx=10, expand=True, fill=tk.X)
        
        ttk.Button(
            button_frame, 
            text="Cancel", 
            command=self.dialog.destroy
        ).pack(side=tk.LEFT, padx=10, expand=True, fill=tk.X)
        
        # Bind Enter key to save
        self.dialog.bind('<Return>', lambda e: self._insert_card())
        # Bind Escape key to cancel
        self.dialog.bind('<Escape>', lambda e: self.dialog.destroy())
    
    def _insert_card(self):
        """Insert the card into the database."""
        uid = self.uid_var.get().strip()
        balance_str = self.balance_var.get().strip()
        employee = self.employee_var.get().strip()
        
        # Validation
        if not uid:
            messagebox.showerror("Error", "Card UID is required.")
            return
        
        if not uid.replace('-', '').replace('_', '').replace(' ', '').isalnum():
            messagebox.showerror(
                "Error", 
                "Invalid UID format. Use alphanumeric characters only."
            )
            return
        
        try:
            balance = float(balance_str) if balance_str else 0.0
            if balance < 0:
                messagebox.showerror("Error", "Initial balance cannot be negative.")
                return
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid initial balance.")
            return
        
        if not employee:
            messagebox.showerror("Error", "Employee name is required.")
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
                    notes='Manual card insertion'
                )
                logger.info(
                    f"Card {uid} inserted with balance {balance} EGP "
                    f"by {employee} (Transaction ID: {transaction_id})"
                )
            else:
                new_balance = card['balance']
                logger.info(f"Card {uid} inserted with zero balance by {employee}")
            
            # Show simple confirmation
            messagebox.showinfo("Success", "Successfully saved the information")
            self.dialog.destroy()
            
        except Exception as e:
            logger.exception(f"Error inserting card {uid}")
            messagebox.showerror("Error", f"Failed to insert card: {e}")