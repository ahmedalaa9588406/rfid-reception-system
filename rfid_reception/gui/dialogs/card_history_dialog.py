"""Dialog for displaying RFID card game history from blocks 9-15."""

import tkinter as tk
from tkinter import ttk, messagebox
import logging

logger = logging.getLogger(__name__)

# Modern color palette
PRIMARY_COLOR = "#2E86AB"
SUCCESS_COLOR = "#06A77D"
DANGER_COLOR = "#C1121F"
LIGHT_BG = "#F5F5F5"
CARD_BG = "#FFFFFF"
TEXT_PRIMARY = "#2C3E50"
TEXT_SECONDARY = "#555555"
BORDER_COLOR = "#E0E0E0"


class CardHistoryDialog:
    """Dialog to display game history stored in RFID card blocks 9-15."""
    
    def __init__(self, parent, serial_service, card_uid=None, history_data=None):
        """Initialize the card history dialog.
        
        Args:
            parent: Parent window
            serial_service: Serial communication service
            card_uid: Optional pre-loaded card UID
            history_data: Optional pre-loaded history data (list of block dicts)
        """
        self.parent = parent
        self.serial_service = serial_service
        self.preloaded_uid = card_uid
        self.preloaded_history = history_data
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("📜 Card Game History")
        self.dialog.geometry("800x600")
        self.dialog.configure(bg=LIGHT_BG)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self._create_widgets()
        
        # Load history - use preloaded data if available
        if self.preloaded_uid and self.preloaded_history is not None:
            self._display_preloaded_history()
        else:
            self._load_history()
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
    
    def _create_widgets(self):
        """Create dialog widgets."""
        # Header
        header_frame = tk.Frame(self.dialog, bg=PRIMARY_COLOR, height=80)
        header_frame.pack(fill='x', side='top')
        header_frame.pack_propagate(False)
        
        header_label = tk.Label(
            header_frame,
            text="📜 Card Game History",
            font=('Segoe UI', 18, 'bold'),
            fg='white',
            bg=PRIMARY_COLOR
        )
        header_label.pack(pady=20)
        
        # Info section
        info_frame = tk.Frame(self.dialog, bg=CARD_BG, relief='flat', bd=1)
        info_frame.configure(highlightbackground=BORDER_COLOR, highlightthickness=1)
        info_frame.pack(fill='x', padx=15, pady=(15, 5))
        
        # Card UID label
        self.uid_label = tk.Label(
            info_frame,
            text="Card UID: Loading...",
            font=('Segoe UI', 11, 'bold'),
            fg=TEXT_PRIMARY,
            bg=CARD_BG,
            anchor='w'
        )
        self.uid_label.pack(padx=15, pady=10, fill='x')
        
        # Instructions
        instructions_label = tk.Label(
            info_frame,
            text="Game history shows all games played with this card (Game ID : Price)",
            font=('Segoe UI', 9),
            fg=TEXT_SECONDARY,
            bg=CARD_BG,
            anchor='w'
        )
        instructions_label.pack(padx=15, pady=(0, 10), fill='x')
        
        # Main content frame
        content_frame = tk.Frame(self.dialog, bg=CARD_BG, relief='flat', bd=1)
        content_frame.configure(highlightbackground=BORDER_COLOR, highlightthickness=1)
        content_frame.pack(fill='both', expand=True, padx=15, pady=5)
        
        # Title for history table
        table_title = tk.Label(
            content_frame,
            text="🎮 Game History by Block",
            font=('Segoe UI', 12, 'bold'),
            fg=PRIMARY_COLOR,
            bg=CARD_BG
        )
        table_title.pack(padx=15, pady=(15, 10), anchor='w')
        
        # Create treeview with scrollbar
        tree_frame = tk.Frame(content_frame, bg=CARD_BG)
        tree_frame.pack(fill='both', expand=True, padx=15, pady=(0, 15))
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        
        # Treeview
        self.tree = ttk.Treeview(
            tree_frame,
            columns=('Block', 'Game ID', 'Price', 'Full Entry'),
            show='headings',
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set,
            height=15
        )
        
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        
        # Configure columns
        self.tree.heading('Block', text='Block #')
        self.tree.heading('Game ID', text='Game ID')
        self.tree.heading('Price', text='Price (EGP)')
        self.tree.heading('Full Entry', text='Raw Entry')
        
        self.tree.column('Block', width=80, anchor='center')
        self.tree.column('Game ID', width=100, anchor='center')
        self.tree.column('Price', width=120, anchor='center')
        self.tree.column('Full Entry', width=400, anchor='w')
        
        # Pack treeview and scrollbars
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Style the treeview
        style = ttk.Style()
        style.configure("Treeview", 
                       background=CARD_BG,
                       foreground=TEXT_PRIMARY,
                       fieldbackground=CARD_BG,
                       font=('Segoe UI', 10))
        style.configure("Treeview.Heading",
                       background=PRIMARY_COLOR,
                       foreground='white',
                       font=('Segoe UI', 10, 'bold'))
        style.map('Treeview', background=[('selected', SUCCESS_COLOR)])
        
        # Status label
        self.status_label = tk.Label(
            content_frame,
            text="Reading history from card...",
            font=('Segoe UI', 9),
            fg=TEXT_SECONDARY,
            bg=CARD_BG,
            anchor='w'
        )
        self.status_label.pack(padx=15, pady=(0, 10), fill='x')
        
        # Button frame
        button_frame = tk.Frame(self.dialog, bg=LIGHT_BG)
        button_frame.pack(fill='x', padx=15, pady=(5, 15))
        
        # Refresh button
        refresh_btn = tk.Button(
            button_frame,
            text="🔄 Refresh History",
            font=('Segoe UI', 10, 'bold'),
            bg=PRIMARY_COLOR,
            fg='white',
            relief='flat',
            cursor='hand2',
            padx=15,
            pady=8,
            command=self._load_history
        )
        refresh_btn.pack(side='left', padx=(0, 5))
        
        # Close button
        close_btn = tk.Button(
            button_frame,
            text="✖ Close",
            font=('Segoe UI', 10, 'bold'),
            bg=DANGER_COLOR,
            fg='white',
            relief='flat',
            cursor='hand2',
            padx=15,
            pady=8,
            command=self.dialog.destroy
        )
        close_btn.pack(side='right')
    
    def _display_preloaded_history(self):
        """Display preloaded history data without reading from Arduino."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        self.uid_label.config(text=f"Card UID: {self.preloaded_uid}")
        self.status_label.config(
            text="📖 Displaying history from recent card read...",
            fg=TEXT_SECONDARY
        )
        self.dialog.update_idletasks()
        
        try:
            if not self.preloaded_history:
                self.status_label.config(
                    text="ℹ️ No history found on this card (all blocks empty)",
                    fg=TEXT_SECONDARY
                )
                return
            
            # Parse and display history entries
            total_entries = 0
            for block_entry in self.preloaded_history:
                block_num = block_entry['block']
                block_data = block_entry['data'].strip()
                
                if not block_data or block_data == '' or all(c in '\x00 ' for c in block_data):
                    # Empty block, skip
                    continue
                
                # Parse entries in format: "A:50#B:30#C:25#"
                entries = block_data.split('#')
                for entry in entries:
                    entry = entry.strip()
                    if not entry or ':' not in entry:
                        continue
                    
                    # Parse "GameID:Price"
                    parts = entry.split(':', 1)
                    if len(parts) == 2:
                        game_id = parts[0].strip()
                        try:
                            price = parts[1].strip()
                            # Insert into tree
                            self.tree.insert('', 'end', values=(
                                f"Block {block_num}",
                                game_id,
                                price,
                                entry
                            ))
                            total_entries += 1
                        except ValueError:
                            # Invalid price format, show raw entry
                            self.tree.insert('', 'end', values=(
                                f"Block {block_num}",
                                game_id,
                                'Invalid',
                                entry
                            ))
                            total_entries += 1
            
            if total_entries == 0:
                self.status_label.config(
                    text="ℹ️ No valid game history entries found",
                    fg=TEXT_SECONDARY
                )
            else:
                self.status_label.config(
                    text=f"✓ Loaded {total_entries} game history entries from card",
                    fg=SUCCESS_COLOR
                )
            
            logger.info(f"Displayed preloaded history: {total_entries} entries")
            
        except Exception as e:
            logger.error(f"Error displaying preloaded history: {e}")
            self.status_label.config(
                text=f"❌ Error: {str(e)}",
                fg=DANGER_COLOR
            )
    
    def _load_history(self):
        """Load history from card using Arduino."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        self.status_label.config(
            text="⏳ Reading history from card... Please keep card on reader...",
            fg=TEXT_SECONDARY
        )
        self.dialog.update_idletasks()
        
        # Check if Arduino is connected
        if not self.serial_service.is_connected:
            self.status_label.config(
                text="❌ Arduino not connected! Please connect Arduino first.",
                fg=DANGER_COLOR
            )
            self.uid_label.config(text="Card UID: Not connected")
            messagebox.showerror(
                "Connection Error",
                "Arduino is not connected.\n\nPlease connect to Arduino before reading card history.",
                parent=self.dialog
            )
            return
        
        try:
            # Read history from card
            success, uid_or_error, history_entries = self.serial_service.read_history()
            
            if success:
                self.uid_label.config(text=f"Card UID: {uid_or_error}")
                
                if not history_entries:
                    self.status_label.config(
                        text="ℹ️ No history found on this card (all blocks empty)",
                        fg=TEXT_SECONDARY
                    )
                    return
                
                # Parse and display history entries
                total_entries = 0
                for block_entry in history_entries:
                    block_num = block_entry['block']
                    block_data = block_entry['data'].strip()
                    
                    if not block_data or block_data == '' or all(c in '\x00 ' for c in block_data):
                        # Empty block, skip
                        continue
                    
                    # Parse entries in format: "A:50#B:30#C:25#"
                    entries = block_data.split('#')
                    for entry in entries:
                        entry = entry.strip()
                        if not entry or ':' not in entry:
                            continue
                        
                        # Parse "GameID:Price"
                        parts = entry.split(':', 1)
                        if len(parts) == 2:
                            game_id = parts[0].strip()
                            try:
                                price = parts[1].strip()
                                # Insert into tree
                                self.tree.insert('', 'end', values=(
                                    f"Block {block_num}",
                                    game_id,
                                    price,
                                    entry
                                ))
                                total_entries += 1
                            except ValueError:
                                # Invalid price format, show raw entry
                                self.tree.insert('', 'end', values=(
                                    f"Block {block_num}",
                                    game_id,
                                    'Invalid',
                                    entry
                                ))
                                total_entries += 1
                
                if total_entries == 0:
                    self.status_label.config(
                        text="ℹ️ No valid game history entries found",
                        fg=TEXT_SECONDARY
                    )
                else:
                    self.status_label.config(
                        text=f"✓ Successfully loaded {total_entries} game history entries",
                        fg=SUCCESS_COLOR
                    )
                
                logger.info(f"Card history loaded: {total_entries} entries from {len(history_entries)} blocks")
                
            else:
                # Error reading history
                self.uid_label.config(text="Card UID: Error reading card")
                self.status_label.config(
                    text=f"❌ Error: {uid_or_error}",
                    fg=DANGER_COLOR
                )
                messagebox.showerror(
                    "Read Error",
                    f"Failed to read card history:\n\n{uid_or_error}\n\nPlease ensure the card is on the reader.",
                    parent=self.dialog
                )
                logger.error(f"Card history read failed: {uid_or_error}")
        
        except Exception as e:
            logger.error(f"Error loading card history: {e}")
            self.status_label.config(
                text=f"❌ Error: {str(e)}",
                fg=DANGER_COLOR
            )
            messagebox.showerror(
                "Error",
                f"An error occurred while reading card history:\n\n{str(e)}",
                parent=self.dialog
            )
