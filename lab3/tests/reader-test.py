from ccsds import CCSDSReader
import struct

reader = CCSDSReader(folder="data")

print(f"{'Source File':<25} | {'Seq':<5} | {'Temp':<6}")
print("-" * 45)

packet_count = 0
for packet in reader.stream_all_files():
    packet_count += 1
    
    # We only print every 5000th packet so your terminal doesn't freeze
    if packet_count % 5000 == 0:
        # Unpack the payload using our map
        # [0]=Time, [1]=Temp, [2]=Volt, [3]=Status
        data = struct.unpack(">IffB", packet['payload'])
        temp = data[1]
        
        print(f"{packet['source']:<25} | {packet['seq']:<5} | {temp:.2f}C")

print(f"\nTotal packets found across all files: {packet_count}")