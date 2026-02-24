"""
-------------------------------------------------------------------------------
Project: Raspberry Pi HQCamera Class for High-Altitude Balloon Mission

File:    camera.py

Purpose: Handles initialization and control of the Raspberry Pi HQ Camera.
         Provides a clean interface for taking still images and recording video.

Logic:   1. Initializes the Picamera2 and sets up a folder for media storage.
         2. Provides methods to take pictures and start/stop video recording.
         3. Configures the camera for still or video mode with appropriate settings.
         4. Ensures safe cleanup of camera resources on shutdown.

If run as main:
         1. Takes a few test pictures to verify functionality.
         2. (Optional) Could add a test video recording here as well.
-------------------------------------------------------------------------------
Author:  James Scott and Kenadi Waymire
Date:    February 2026
-------------------------------------------------------------------------------
"""

import time
import os
from picamera2 import Picamera2
from picamera2.outputs import FfmpegOutput, FileOutput
from picamera2.encoders import H264Encoder

class HQCameraRecorder:
    def __init__(self, folder="media"):
        self.picam2 = Picamera2()
        self.folder = folder
        if not os.path.exists(self.folder):
            os.makedirs(self.folder)

    def take_picture(self, filename="image.jpg"):
        path = os.path.join(self.folder, filename)
        print(f"Capturing image: {path}")
        self.picam2.capture_file(path)
        print("Image saved.")

    def start_video(self, filename="video.h264"):
        path = os.path.join(self.folder, filename)
        # Bitrate: 10Mbps
        encoder = H264Encoder(10000000)
        # video_output = FfmpegOutput(path)
        
        print(f"Starting recording: {path}")
        # Passing encoder and output as explicit arguments fixes the TypeError
        # self.picam2.start_recording(encoder, output=video_output)
        self.picam2.start_recording(encoder, output=path)

    def stop_video(self):
        self.picam2.stop_recording()
        print("Recording finished.")

    def setup_camera(self, mode="still", fps=60):
        """Configures the camera, ensuring it is stopped first if already running."""
        try:
            self.picam2.stop()
        except:
            pass

        if mode == "video":
            # Force the frame rate in the configuration controls
            config = self.picam2.create_video_configuration(
                main={"size": (640, 480)},
                controls={"FrameRate": fps,
                          "AwbMode": 5}        
            )
            print(f"Camera configured for 480p Video at {fps} FPS.")
        else:
            config = self.picam2.create_still_configuration(main={"size": (640, 480)},
                                                            controls={"AwbMode": 5})
            print("Camera configured for High-Res Still.")
            
        self.picam2.configure(config)
        self.picam2.start()

    def cleanup(self):
        """Safe shutdown that won't crash if already stopped."""
        print("Closing camera.")
        try:
            # We don't even need to check; if it's running, it stops. 
            # If it's not, Picamera2 usually handles it gracefully or we catch the error.
            self.picam2.stop()
        except Exception:
            pass 
        self.picam2.close()

if __name__ == "__main__":
    recorder = HQCameraRecorder()
    
    try:
        # --- TAKE A PICTURE ---
        recorder.setup_camera(mode="still")
        recorder.take_picture("1.jpg")
        
        time.sleep(1) 

        recorder.take_picture("2.jpg")

        time.sleep(1)

        recorder.take_picture("3.jpg")
        
        # # --- RECORD A VIDEO ---
        # recorder.setup_camera(mode="video")
        # recorder.record_video("mission_clip.h264", duration_seconds=10)
        
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        recorder.cleanup()
