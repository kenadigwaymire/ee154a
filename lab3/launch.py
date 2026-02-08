import os
import platform
import subprocess

SIM_MODE = False  # Set to True to run in simulation mode

def launch():
    # 1. Identify the paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(base_dir)
    flight_name = "flight_state_machine.py"
    ground_name = "log_to_terminal.py"
    active_plot = "active_plot.py"
    sim_flag = "--simulate" if SIM_MODE else ""
    
    # Determine venv python path based on OS
    if platform.system() == "Windows":
        python_exe = os.path.join(parent_dir, ".venv", "Scripts", "python.exe")
        # Command for Windows (start opens a new cmd window)
        cmd_state = f'start "FLIGHT STATE MACHINE" "{python_exe}" {flight_name} {sim_flag}'
        cmd_ground = f'start "GROUND STATION" "{python_exe}" {ground_name} {sim_flag}'
        cmd_plot = f'start "ACTIVE PLOT" "{python_exe}" {active_plot} {sim_flag}'
    else:
        python_exe = os.path.join(parent_dir, ".venv", "bin", "python")
        # Command for Mac/Linux (uses AppleScript or xterm)
        if platform.system() == "Darwin": # Mac
            cmd_state = f"osascript -e 'tell application \"Terminal\" to do script \"cd {parent_dir} && {python_exe} {flight_name} {sim_flag}\"'"
            cmd_ground = f"osascript -e 'tell application \"Terminal\" to do script \"cd {parent_dir} && {python_exe} {ground_name} {sim_flag}\"'"
            cmd_plot = f"osascript -e 'tell application \"Terminal\" to do script \"cd {parent_dir} && {python_exe} {active_plot} {sim_flag}\"'"
        else: # Linux
            cmd_state = f'gnome-terminal -- bash -c "{python_exe} {flight_name} {sim_flag}; exec bash"'
            cmd_ground = f'gnome-terminal -- bash -c "{python_exe} {ground_name} {sim_flag}; exec bash"'

    # 2. Launch both processes
    print("Launching Flight State Machine...")
    os.system(cmd_state)
    
    print("Launching Ground Station Dashboard...")
    os.system(cmd_ground)

    print("Launching Active Plotter...")
    os.system(cmd_plot)

if __name__ == "__main__":
    launch()