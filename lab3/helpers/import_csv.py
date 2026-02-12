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