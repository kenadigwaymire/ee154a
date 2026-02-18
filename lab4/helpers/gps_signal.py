import serial

# Setup Serial
ser = serial.Serial('/dev/serial0', 9600, timeout=1)

print(f"{'PRN':<6} | {'Elevation':<10} | {'Azimuth':<10} | {'SNR (Signal)':<10}")
print("-" * 45)

try:
    while True:
        line = ser.readline().decode('ascii', errors='replace').strip()
        
        if line.startswith('$GPGSV'):
            parts = line.split(',')
            # GSV sentences can have up to 4 satellites per line
            # Data starts at index 4: [PRN, Elev, Azim, SNR]
            for i in range(4, len(parts) - 3, 4):
                prn = parts[i]
                snr = parts[i+3].split('*')[0] # Clean up checksum
                if prn:
                    # Print a little bar graph for the SNR
                    bar = "█" * (int(snr) // 2) if snr else ""
                    print(f"{prn:<6} | {parts[i+1]:<10} | {parts[i+2]:<10} | {snr:<3} {bar}")
            print("-" * 45)
except KeyboardInterrupt:
    print("\nStopping meter.")