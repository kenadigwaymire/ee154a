from ccsds import CCSDSWriter

import struct
import os
import time
import random

# Initialize writer with 1MB limit to see rotation quickly
# Change 1*1024*1024 to 10*1024*1024 for your 10MB requirement
logger = CCSDSWriter(apid=0x123, folder="data", max_bytes=1*1024*1024)

print("Starting Stress Test... Writing ~1.5MB of data.")

# We will write 100,000 packets
for i in range(100000):
    # Simulated payload: [Timestamp, Temp, Voltage, Status]
    now = int(time.time())
    temp = random.uniform(20.0, 30.0)
    volt = random.uniform(3.0, 3.6)
    status = random.randint(0, 1)
    
    payload = struct.pack(">IffB", now, temp, volt, status)
    logger.write(payload)
    
    if i % 10000 == 0:
        print(f"Logged {i} packets...")

print("Done! Check your 'data' folder for multiple .ccsds files.")