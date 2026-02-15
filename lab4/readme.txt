SSH - in cmd terminal
Command: ssh ee154@10.8.18.185
Password: raspberry23

Script is set to auto start on launch and restart after 5 seconds if it fails.
In ssh terminal:
mission-start to start script if off
mission-stop to turn off temporarily
mission-log to observe the script and debug issues
mission-enable to enable this watchdog script for every startup
mission-disable to disable this script permanently and no longer start on startup
feed-start to observe mission data live
(Ctrl+C to exit this terminal debugger)

VENV (Need to run any files directly other than watchdog script)
cd ee154
source .venv/bin/activate

How to run important files
cd lab4 (takes you into main folder for balloon launch/lab4)
python flight-state-machine.py  (Main watchdog script: DONT NEED TO RUN)
python terminal_debugger (Reads latest values and measures in terminal)

Plotting (Only run in lab4 folder)
python plot.py (plots all data)
python plot.py --minDate="02/14/2026|12:00:00" --maxDate="02/14/2026|23:59:59"

Convert to CSV (only run in lab4 folder)
python ccsds_to_csv.py 
python ccsds_to_csv.py --minDate="02/14/2026|08:00:00"