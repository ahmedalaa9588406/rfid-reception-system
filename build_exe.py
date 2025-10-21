"""
Build script for creating a standalone EXE of the RFID Reception System.
Run this script to build the application: python build_exe.py
"""
import os
import shutil
import PyInstaller.__main__
import sys

def clean_build_dirs():
    """Remove previous build and dist directories."""
    for dir_name in ['build', 'dist']:
        if os.path.exists(dir_name):
            print(f"Removing existing {dir_name} directory...")
            shutil.rmtree(dir_name)

def build_executable():
    """Build the executable using PyInstaller."""
    print("Building RFID Reception System executable...")
    
    # Define the main script and output name
    main_script = 'rfid_reception/app.py'
    app_name = 'RFID_Reception_System'
    
    # Conditionally build add-data arguments based on existing directories
    add_data_args = []
    if os.path.exists('rfid_reception/data'):
        add_data_args.append('--add-data=rfid_reception/data;rfid_reception/data')
    if os.path.exists('rfid_reception/reports/templates'):
        add_data_args.append('--add-data=rfid_reception/reports/templates;rfid_reception/reports/templates')
    
    # PyInstaller configuration
    pyinstaller_args = [
        '--name=%s' % app_name,
        '--onefile',  # Create a single executable file
        '--windowed',  # For GUI applications (no console)
        # Add conditional data includes
    ] + add_data_args + [
        '--hidden-import=sqlalchemy.sql.default_comparator',
        '--hidden-import=sqlalchemy.dialects.sqlite',
        '--hidden-import=apscheduler.triggers.interval',
        '--hidden-import=apscheduler.triggers.date',
        '--hidden-import=reportlab.lib.styles',
        '--hidden-import=reportlab.platypus',
        '--hidden-import=reportlab.graphics.charts.barcharts',
        '--hidden-import=reportlab.graphics.charts.piecharts',
        '--hidden-import=arabic_reshaper',
        '--hidden-import=python_bidi',
        '--clean',  # Clean PyInstaller cache and remove temporary files
        '--noconfirm',  # Replace output directory without confirmation
        main_script
    ]
    
    # Run PyInstaller
    PyInstaller.__main__.run(pyinstaller_args)
    
    print(f"\nBuild complete! Executable is in the 'dist' directory.")
    print("You can now run the application by double-clicking on 'RFID_Reception_System.exe'")

if __name__ == '__main__':
    print("=== RFID Reception System EXE Builder ===")
    print("This script will create a standalone executable of the application.\n")
    
    # Clean previous builds
    clean_build_dirs()
    
    # Build the executable
    build_executable()
