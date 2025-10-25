"""
Demo script to showcase the enhanced RFID Reception System interface.
This demonstrates all the new features without requiring Arduino hardware.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
from tkinter import messagebox

def show_demo():
    """Show a demo of what the interface does."""
    
    root = tk.Tk()
    root.title("RFID Reception System - Interface Demo")
    root.geometry("600x700")
    root.configure(bg="#F5F5F5")
    
    # Header
    header = tk.Frame(root, bg="#2E86AB", height=80)
    header.pack(fill='x')
    header.pack_propagate(False)
    
    title = tk.Label(header, 
                     text="🎫 RFID Reception System - NEW INTERFACE",
                     font=('Segoe UI', 16, 'bold'),
                     fg='white',
                     bg="#2E86AB")
    title.pack(expand=True)
    
    # Content
    content = tk.Frame(root, bg="#F5F5F5")
    content.pack(fill='both', expand=True, padx=20, pady=20)
    
    # Instructions
    instructions = tk.Label(content,
                           text="📋 How to Use the New Interface:",
                           font=('Segoe UI', 14, 'bold'),
                           bg="#F5F5F5",
                           fg="#2C3E50")
    instructions.pack(anchor='w', pady=(0, 15))
    
    steps = [
        "1️⃣  Run the application:",
        "   python -m rfid_reception.app",
        "",
        "2️⃣  Employee scans card:",
        "   Click '🔍 Read Card' button",
        "   Place RFID card near reader",
        "",
        "3️⃣  Choose operation:",
        "   • '✓ Add to Balance' - Add money",
        "   • '✍ Set Balance' - Set exact amount (NEW!)",
        "",
        "4️⃣  Receipt prints automatically!",
        "",
        "💡 TIP: Use Manual Mode to test without Arduino",
    ]
    
    for step in steps:
        lbl = tk.Label(content,
                      text=step,
                      font=('Consolas', 10),
                      bg="#F5F5F5",
                      fg="#555555",
                      anchor='w',
                      justify='left')
        lbl.pack(anchor='w', pady=2)
    
    # Separator
    sep_frame = tk.Frame(content, bg="#E0E0E0", height=2)
    sep_frame.pack(fill='x', pady=20)
    
    # Feature highlights
    features_title = tk.Label(content,
                             text="✨ New Features:",
                             font=('Segoe UI', 12, 'bold'),
                             bg="#F5F5F5",
                             fg="#2C3E50")
    features_title.pack(anchor='w', pady=(0, 10))
    
    features = [
        "✅ Automatic new card detection",
        "✅ Set Balance button (set exact amount)",
        "✅ Automatic receipt printing",
        "✅ Card read event logging",
        "✅ Smart user feedback",
        "✅ Manual mode for testing",
    ]
    
    for feature in features:
        lbl = tk.Label(content,
                      text=feature,
                      font=('Segoe UI', 10),
                      bg="#F5F5F5",
                      fg="#06A77D")
        lbl.pack(anchor='w', pady=3)
    
    # Button frame
    btn_frame = tk.Frame(content, bg="#F5F5F5")
    btn_frame.pack(side='bottom', fill='x', pady=20)
    
    def launch_app():
        root.destroy()
        print("\n🚀 Launching RFID Reception System...")
        print("="*60)
        from rfid_reception.app import main
        main()
    
    def show_manual_mode_help():
        msg = """Manual Mode Testing (No Arduino Required):

1. In the main window, check ✓ "Enable Manual Card Entry"

2. Enter a test card UID:
   Example: TEST_CARD_001

3. Click "Load Card UID"

4. Now you can:
   • Add balance
   • Set balance
   • Print receipts
   • Test all features!

This is perfect for training and testing!"""
        messagebox.showinfo("Manual Mode Help", msg)
    
    # Buttons
    launch_btn = tk.Button(btn_frame,
                          text="🚀 Launch Application",
                          font=('Segoe UI', 12, 'bold'),
                          bg="#06A77D",
                          fg='white',
                          relief='flat',
                          cursor='hand2',
                          padx=20,
                          pady=12,
                          command=launch_app)
    launch_btn.pack(fill='x', pady=5)
    
    help_btn = tk.Button(btn_frame,
                        text="💡 Manual Mode Help (Test Without Arduino)",
                        font=('Segoe UI', 10),
                        bg="#F18F01",
                        fg='white',
                        relief='flat',
                        cursor='hand2',
                        padx=15,
                        pady=10,
                        command=show_manual_mode_help)
    help_btn.pack(fill='x', pady=5)
    
    # Footer
    footer = tk.Label(content,
                     text="Documentation: See QUICK_START.md and EMPLOYEE_GUIDE.md",
                     font=('Segoe UI', 8),
                     bg="#F5F5F5",
                     fg="#999999")
    footer.pack(side='bottom', pady=10)
    
    root.mainloop()

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  🎫 RFID Reception System - Interface Demo")
    print("="*60 + "\n")
    show_demo()
