import os
import platform
import subprocess

def launch():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(base_dir)
    flight_name = "flight_state_machine.py"
    ground_name = "terminal_debugger.py"
    
    # Determine venv python path based on OS
    if platform.system() == "Windows":
        python_exe = os.path.join(parent_dir, ".venv", "Scripts", "python.exe")
        # Command for Windows (start opens a new cmd window)
        cmd_state = f'start "FLIGHT STATE MACHINE" "{python_exe}" {flight_name}'
        cmd_ground = f'start "DEBUG TERMINAL" "{python_exe}" {ground_name}'
    else:
        python_exe = os.path.join(parent_dir, ".venv", "bin", "python")
        # Command for Mac/Linux (uses AppleScript or xterm)
        if platform.system() == "Darwin": # Mac
            pass  # macOS Terminal doesn't support --title, so we use AppleScript to set the title after launching
        else: # Linux
            cmd_state = f'gnome-terminal -- bash -c "{python_exe} {flight_name}; exec bash"'
            cmd_ground = f'gnome-terminal -- bash -c "{python_exe} {ground_name}; exec bash"'

    # 2. Launch both processes
    print("Launching Flight State Machine...")
    os.system(cmd_state)
    
    print("Launching Debug Terminal...")
    os.system(cmd_ground)

if __name__ == "__main__":
    launch()