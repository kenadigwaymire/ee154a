import time
import datetime

class SpaceTime:
    def __init__(self):
        # A date in the past that acts as a "sanity check" (e.g., Jan 1 2025)
        self.LAUNCH_EPOCH = 1735689600 
        self.is_utc_valid = False
        self.update_sync_status()

    def update_sync_status(self):
        """Checks if the system clock is actually synced to UTC."""
        if time.time() > self.LAUNCH_EPOCH:
            self.is_utc_valid = True
        else:
            self.is_utc_valid = False
        return self.is_utc_valid

    def get_time(self):
        """
        Returns a dictionary with current best-guess time 
        and a 'valid' flag.
        """
        self.update_sync_status()
        current_now = time.time()
        
        # 'time.monotonic()' is essential; it never resets or drifts 
        # based on system clock updates.
        return {
            "timestamp": current_now,
            "mono": time.monotonic(),
            "is_utc": self.is_utc_valid,
            "readable": datetime.datetime.fromtimestamp(current_now).strftime('%Y-%m-%d %H:%M:%S')
        }

def test_spacetime_logic():
    print("--- SpaceTime Autonomy Test ---")
    clock = SpaceTime()
    
    # 1. Simulate "Startup in Space" (No Internet)
    # We pretend the system clock is stuck at 1970 (small timestamp)
    fake_startup_time = 500.0 
    print(f"Status: Booting... System Time is {fake_startup_time}")
    
    if fake_startup_time < clock.LAUNCH_EPOCH:
        print("Result: [!] UTC Unavailable. Using internal relative clock.")
    
    # 2. Simulate data logging during the 'Dark Period'
    # We use monotonic to track how many seconds have passed since boot
    start_mono = time.monotonic()
    time.sleep(2) # Wait 2 seconds
    elapsed = time.monotonic() - start_mono
    
    print(f"Status: 2 seconds elapsed in the dark. Internal counter: {elapsed:.2f}s")

    # 3. Simulate "Reconnection" (UTC Sync)
    print("Status: Simulated Ground Link Established. Syncing UTC...")
    real_utc = time.time() # This is the actual 2026 time
    
    # The Correction
    # If we know it's now 'real_utc' and 'elapsed' seconds passed since boot,
    # the actual time we booted was:
    corrected_boot_time = real_utc - elapsed
    
    print(f"Result: [OK] UTC Found: {real_utc}")
    print(f"Correction: Boot actually occurred at UTC {corrected_boot_time}")
    
    readable_boot = datetime.datetime.fromtimestamp(corrected_boot_time).strftime('%Y-%m-%d %H:%M:%S')
    print(f"Conclusion: Your '1970' data actually belongs to: {readable_boot}")

if __name__ == "__main__":
    test_spacetime_logic()