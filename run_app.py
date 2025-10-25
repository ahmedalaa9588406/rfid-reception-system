"""
Quick launcher for RFID Reception System.
Double-click this file to start the application.
"""

import sys
import os

# Add the project to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Run the application
from rfid_reception.app import main

if __name__ == "__main__":
    print("="*60)
    print("  🎫 RFID Reception System")
    print("="*60)
    print("\n✓ Starting application...")
    print("✓ Loading interface...")
    print("\n📱 The GUI window will open shortly...")
    print("\nTip: Use Manual Mode to test without Arduino hardware!")
    print("="*60 + "\n")
    
    main()
