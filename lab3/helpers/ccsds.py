"""
CCSDS DATA LOGGING
--------------------------------------
PURPOSE: 
    This module implements the CCSDS Space Packet Protocol for an ISS payload. 
    It is designed to ensure data integrity, autonomous recovery from power 
    failures, and efficient transmission of data "bits" to a ground station.

REASONING:
    1. BINARY VS TEXT: We use binary (struct) because it is 3-10x more compact 
       than CSV/JSON, saving critical bandwidth during ISS downlink passes.
    2. STANDARDIZATION: Using CCSDS headers allows our data to be parsed by 
       standard NASA/ESA ground station tools.
    3. AUTONOMY: The 'rotation' and 'fsync' logic ensures that if the Pi 
       reboots unexpectedly, the data remains intact and organized.
"""

import struct
import os
import time
import glob

class CCSDSWriter:
    """
    Handles the creation and storage of CCSDS-compliant binary packets.
    
    This class manages 'File Rotation' to prevent data corruption from 
    impacting large datasets and handles low-level disk synchronization 
    to protect against sudden power loss on the ISS. Files rotate every
    10mb currently, but this can be adjusted as needed.
    """

    def __init__(self, apid, folder="data", filename="telemetry.ccsds", max_bytes=10 * 1024 * 1024):
        """
        Initializes the logger and ensures the storage directory exists.
        
        Args:
            apid (int): Application Process ID (11-bit). Identifies this 
                        specific experiment to the ground station.
            folder (str): Directory for storage. Isolates data from source code.
            filename (str): The active log file name.
            max_bytes (int): Threshold for file rotation to maintain small, 
                             manageable upload chunks.
        """
        self.apid = apid & 0x07FF   # Masking ensures APID fits in 11 bits
        self.folder = folder        
        self.filename = filename    
        self.max_bytes = max_bytes  
        self.seq_count = 0          # Tracks packet order; helps ground detect loss.
        
        if not os.path.exists(self.folder):
            os.makedirs(self.folder)
            
        self.filepath = os.path.join(self.folder, self.filename)

    def _rotate_file(self):
        """
        Archives the current log file by adding a timestamp to its name.
        
        REASONING: Small files are easier to upload during short ground-link 
        windows. If one file is corrupted by radiation, other files remain safe.
        """
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        new_name = os.path.join(self.folder, f"telemetry_{timestamp}.ccsds")
        if os.path.exists(self.filepath):
            os.rename(self.filepath, new_name)
            print(f"File rotated to: {new_name}")

    def write(self, payload):
        """
        Wraps a data payload in a 6-byte CCSDS header and commits it to disk.
        
        This function forces a 'Hardware Flush' (fsync) to ensure the data is 
        physically written to the SD card immediately, protecting against 
        Single Event Upsets (SEUs) or power resets.

        Args:
            payload (bytes): The raw binary data from sensors.
        Returns:
            int: The total length of the packet written.
        """
        # Check if the current file is too large before writing
        if os.path.exists(self.filepath) and os.path.getsize(self.filepath) > self.max_bytes:
            self._rotate_file()

        # Build CCSDS Header
        # word 1: Version, Type, Sec Header Flag, and APID
        word1 = self.apid

        # word 2: Sequence Flags (11 = unsegmented) and 14-bit Sequence Count
        word2 = 0xC000 | (self.seq_count & 0x3FFF)
        
        # word 3: Payload Length - 1 (per CCSDS standard)
        word3 = (len(payload) - 1) & 0xFFFF
        
        # Pack header as Big-Endian (>), the standard for space-link protocols
        header = struct.pack(">HHH", word1, word2, word3)
        packet = header + payload
        
        # Open in 'Append Binary' (ab) mode to never overwrite historical data
        with open(self.filepath, "ab") as f:
            f.write(packet)
            f.flush()        # Pushes data from Python to the OS buffer
            os.fsync(f.fileno()) # Pushes data from OS buffer to physical disk
            
        # Increment sequence count for the next packet
        self.seq_count = (self.seq_count + 1) % 16384
        return len(packet)

class CCSDSReader:
    """
    Decodes stored CCSDS files into a Python-friendly format.
    
    This class allows for non-destructive reading of flight data, whether 
    processing a single active file or a folder full of archived logs.
    """

    def __init__(self, folder="data"):
        """
        Initializes the reader to look in a specific data directory.
        
        Args:
            folder (str): The directory containing .ccsds telemetry files.
        """
        self.folder = folder

    def stream_all_files(self):
        """
        A generator that iterates through all .ccsds files in the folder.
        
        REASONING: Allows the ground station to process the entire mission 
        history in chronological order by 'stitching' rotated files together.
        """
        files = sorted(glob.glob(os.path.join(self.folder, "*.ccsds")))
        
        for filepath in files:
            yield from self.stream_specific_file(filepath)

    def stream_specific_file(self, filepath):
        """
        Reads a binary file packet-by-packet using CCSDS header length definitions.
        
        REASONING: Because CCSDS packets have a length field in the header, 
        we can safely navigate the file even if it contains varying payload sizes.

        Args:
            filepath (str): Path to the target binary file.
        Yields:
            dict: A dictionary containing APID, Sequence Count, and the raw Payload.
        """
        if not os.path.exists(filepath):
            return

        with open(filepath, "rb") as f: # 'rb' ensures we do not modify the file
            while True:
                # Every CCSDS packet starts with exactly 6 bytes of header
                header_data = f.read(6)
                if len(header_data) < 6:
                    break 
                
                # Unpack metadata from header
                header = struct.unpack(">HHH", header_data)
                apid = header[0] & 0x07FF
                seq = header[1] & 0x3FFF
                length = header[2] + 1 # Add 1 back to get the true payload size
                
                # Read exactly the number of bytes defined by the header
                payload = f.read(length)
                if len(payload) < length:
                    break # Incomplete packet; end of file
                    
                yield {
                    "apid": apid, 
                    "seq": seq, 
                    "payload": payload, 
                    "source": os.path.basename(filepath)
                }