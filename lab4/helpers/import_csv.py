"""
-------------------------------------------------------------------------------
Project: Example CSV Import Script for High-Altitude Balloon Mission

File:    import_csv.py

Purpose: Handles importing flight data from a CSV file.
         Provides a clean interface for selecting and processing CSV files.

Logic:   1. Opens a file dialog for the user to select a CSV file.
         2. Validates the selected file and processes it.

If run as main:
         1. Launches the file dialog for CSV import.
         2. Prints the selected file path or an error message if no file is selected.
-------------------------------------------------------------------------------
Author:  James Scott and Kenadi Waymire
Date:    February 2026
-------------------------------------------------------------------------------
"""
import tkinter as tk
from tkinter import filedialog
import os

def browse_and_import():
    # Create a hidden root window to prevent a blank tk window from staying open
    root = tk.Tk()
    root.withdraw()

    # Open the file explorer
    # filetypes limits the view to CSVs to make it easier for the user
    file_path = filedialog.askopenfilename(
        title="Select Flight Data CSV",
        initialdir=os.getcwd(),
        filetypes=(("CSV files", "*.csv"), ("All files", "*.*"))
    )

    # Check if a file was actually selected (prevents error if user clicks cancel)
    if file_path:
        print(f"Selected file: {file_path}")
        # Logic for processing the CSV goes here
    else:
        print("No file selected.")

    root.destroy()

if __name__ == "__main__":
    browse_and_import()