import time
import os
import cv2
import numpy as np
from picamera2 import Picamera2

picam2 = Picamera2()
# Use a smaller size for the analysis to keep it fast
config = picam2.create_still_configuration(main={"size": (1280, 720)})
picam2.configure(config)
picam2.start()

print("--- HQ Camera Focus Assistant ---")
print("1. Open 'focus.jpg' in your Image Viewer.")
print("2. Watch the 'Sharpness Score' below.")
print("3. Adjust lens until the score is MAXIMIZED.\n")

try:
    while True:
        # Capture to a numpy array for analysis
        frame = picam2.capture_array()
        
        # Save the file for your visual inspection
        cv2.imwrite("focus.jpg", frame)
        
        # Calculate Sharpness (Laplacian Variance)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        score = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # Print score - try to get this number as high as possible
        print(f"Sharpness Score: {score:.2f}    ", end="\r")
        
        time.sleep(0.1) # Faster refresh for easier focusing
except KeyboardInterrupt:
    print("\nClosing camera...")
    picam2.close()