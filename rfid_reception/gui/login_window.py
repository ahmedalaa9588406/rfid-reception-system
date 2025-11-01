"""Login window for RFID Reception System authentication."""

import tkinter as tk
from tkinter import messagebox
import hashlib
import logging

logger = logging.getLogger(__name__)

# Modern color palette
PRIMARY_COLOR = "#2E86AB"
SECONDARY_COLOR = "#A23B72"
SUCCESS_COLOR = "#06A77D"
DANGER_COLOR = "#C1121F"
LIGHT_BG = "#F5F5F5"
CARD_BG = "#FFFFFF"
TEXT_PRIMARY = "#2C3E50"
TEXT_SECONDARY = "#555555"
BORDER_COLOR = "#E0E0E0"


class LoginWindow:
    """Authentication window for the RFID Reception System."""
    
    def __init__(self, root, config, on_success):
        """
        Initialize the login window.
        
        Args:
            root: Tkinter root window
            config: Configuration dictionary
            on_success: Callback function to call on successful authentication
        """
        self.root = root
        self.config = config
        self.on_success = on_success
        self.authenticated = False
        
        # Get password from config (default: "admin123")
        self.stored_password_hash = config.get('password_hash', self._hash_password('admin123'))
        
        # Setup window
        self.root.title("🔐 تسجيل الدخول - نظام استقبال RFID")
        self.root.geometry("450x500")
        self.root.resizable(False, False)
        self.root.configure(bg=LIGHT_BG)
        
        # Center window on screen
        self._center_window()
        
        # Set application icon
        try:
            import os
            icon_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'images', 'images.ico')
            self.icon = tk.PhotoImage(file=icon_path)
            self.root.iconphoto(True, self.icon)
        except (tk.TclError, FileNotFoundError):
            # Icon file not found, continue without icon
            pass
        
        self._create_widgets()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        
    def _center_window(self):
        """Center the window on the screen."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
    def _hash_password(self, password):
        """Hash password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _create_widgets(self):
        """Create and layout login widgets."""
        # Main container
        main_frame = tk.Frame(self.root, bg=CARD_BG, relief='flat', bd=0)
        main_frame.place(relx=0.5, rely=0.5, anchor='center', width=380, height=420)
        main_frame.configure(highlightbackground=BORDER_COLOR, highlightthickness=2)
        
        # Header section with gradient effect
        header_frame = tk.Frame(main_frame, bg=PRIMARY_COLOR, height=120)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        
        # Lock icon and title
        lock_label = tk.Label(
            header_frame,
            text="🔐",
            font=('Segoe UI', 48),
            bg=PRIMARY_COLOR,
            fg='white'
        )
        lock_label.pack(pady=(15, 5))
        
        title_label = tk.Label(
            header_frame,
            font=('Segoe UI', 18, 'bold'),
            bg=PRIMARY_COLOR,
            fg='white'
        )
        title_label.pack()
        
        # Content section
        content_frame = tk.Frame(main_frame, bg=CARD_BG)
        content_frame.pack(fill='both', expand=True, padx=30, pady=30)
        
        # Welcome message
        welcome_label = tk.Label(
            content_frame,
            text="مرحباً بك في نظام استقبال RFID",
            font=('Segoe UI', 11),
            bg=CARD_BG,
            fg=TEXT_SECONDARY
        )
        welcome_label.pack(pady=(0, 20))
        
        # Password label
        password_label = tk.Label(
            content_frame,
            text="🔑 كلمة المرور",
            font=('Segoe UI', 11, 'bold'),
            bg=CARD_BG,
            fg=TEXT_PRIMARY,
            anchor='e'
        )
        password_label.pack(fill='x', pady=(0, 8))
        
        # Password entry frame
        password_frame = tk.Frame(content_frame, bg=CARD_BG)
        password_frame.pack(fill='x', pady=(0, 25))
        
        self.password_var = tk.StringVar()
        self.password_entry = tk.Entry(
            password_frame,
            textvariable=self.password_var,
            font=('Segoe UI', 14),
            relief='flat',
            bd=1,
            show='●',
            justify='center'
        )
        self.password_entry.configure(
            highlightbackground=BORDER_COLOR,
            highlightthickness=2,
            highlightcolor=PRIMARY_COLOR
        )
        self.password_entry.pack(fill='x', ipady=12)
        self.password_entry.focus()
        
        # Bind Enter key to login
        self.password_entry.bind('<Return>', lambda e: self._login())
        
        # Show/Hide password button
        show_hide_frame = tk.Frame(content_frame, bg=CARD_BG)
        show_hide_frame.pack(fill='x', pady=(0, 20))
        
        self.show_password_var = tk.BooleanVar(value=False)
        show_password_check = tk.Checkbutton(
            show_hide_frame,
            text="👁️ إظهار كلمة المرور",
            variable=self.show_password_var,
            command=self._toggle_password_visibility,
            font=('Segoe UI', 9),
            bg=CARD_BG,
            fg=TEXT_SECONDARY,
            activebackground=CARD_BG,
            selectcolor=CARD_BG,
            cursor='hand2'
        )
        show_password_check.pack(anchor='e')
        
        # Login button
        login_btn = tk.Button(
            content_frame,
            text="✓ تسجيل الدخول",
            font=('Segoe UI', 13, 'bold'),
            bg=SUCCESS_COLOR,
            fg='white',
            relief='flat',
            cursor='hand2',
            padx=20,
            pady=14,
            command=self._login
        )
        login_btn.pack(fill='x')
        
        # Add hover effect
        login_btn.bind('<Enter>', lambda e: login_btn.config(bg=self._darken_color(SUCCESS_COLOR)))
        login_btn.bind('<Leave>', lambda e: login_btn.config(bg=SUCCESS_COLOR))
        
        # Footer info
        footer_label = tk.Label(
            content_frame,
            text="💡 كلمة المرور الافتراضية: admin123",
            font=('Segoe UI', 8),
            bg=CARD_BG,
            fg=TEXT_SECONDARY
        )
        footer_label.pack(pady=(15, 0))
        
    def _toggle_password_visibility(self):
        """Toggle password visibility."""
        if self.show_password_var.get():
            self.password_entry.config(show='')
        else:
            self.password_entry.config(show='●')
    
    def _darken_color(self, color):
        """Darken a hex color for hover effect."""
        # Simple darkening by reducing RGB values
        color = color.lstrip('#')
        r, g, b = int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)
        r, g, b = max(0, r - 30), max(0, g - 30), max(0, b - 30)
        return f'#{r:02x}{g:02x}{b:02x}'
    
    def _login(self):
        """Handle login attempt."""
        password = self.password_var.get().strip()
        
        if not password:
            messagebox.showwarning(
                "حقل فارغ",
                "يرجى إدخال كلمة المرور",
                parent=self.root
            )
            self.password_entry.focus()
            return
        
        # Hash entered password and compare
        password_hash = self._hash_password(password)
        
        if password_hash == self.stored_password_hash:
            # Successful authentication
            logger.info("User authenticated successfully")
            self.authenticated = True
            self.root.destroy()  # Close login window
            self.on_success()  # Call success callback
        else:
            # Failed authentication
            logger.warning("Failed login attempt")
            messagebox.showerror(
                "خطأ في تسجيل الدخول",
                "كلمة المرور غير صحيحة!\nيرجى المحاولة مرة أخرى.",
                parent=self.root
            )
            self.password_var.set('')
            self.password_entry.focus()
    
    def _on_close(self):
        """Handle window close event."""
        if not self.authenticated:
            if messagebox.askyesno(
                "تأكيد الخروج",
                "هل تريد الخروج من التطبيق؟",
                parent=self.root
            ):
                logger.info("Application closed from login window")
                self.root.quit()
        else:
            self.root.destroy()
