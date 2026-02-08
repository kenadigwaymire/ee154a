import time
import os
from picamera2 import Picamera2

class HQCameraRecorder:
    def __init__(self, folder="media"):
        self.picam2 = Picamera2()
        self.folder = folder
        if not os.path.exists(self.folder):
            os.makedirs(self.folder)
        
    def setup_camera(self, mode="video"):
        """Configures the camera, ensuring it is stopped first if already running."""
        # Check if the camera is currently streaming
        if self.picam2.running:
            print("Stopping camera for reconfiguration...")
            self.picam2.stop()

        if mode == "video":
            config = self.picam2.create_video_configuration(main={"size": (1920, 1080)})
            print("Camera configured for 1080p Video.")
        else:
            config = self.picam2.create_still_configuration()
            print("Camera configured for High-Res Still.")
            
        self.picam2.configure(config)
        self.picam2.start()

    def take_picture(self, filename="image.jpg"):
        """Captures a single high-resolution frame to disk."""
        path = os.path.join(self.folder, filename)
        print(f"Capturing image: {path}")
        self.picam2.capture_file(path)
        print("Image saved.")

    def record_video(self, filename="video.h264", duration_seconds=5):
        """Records H.264 video for a set duration."""
        path = os.path.join(self.folder, filename)
        print(f"Starting recording: {path}")
        self.picam2.start_recording(path)
        time.sleep(duration_seconds)
        self.picam2.stop_recording()
        print("Recording finished.")

    def cleanup(self):
        """Safe shutdown of the camera hardware."""
        print("Closing camera.")
        self.picam2.stop()
        self.picam2.close()

if __name__ == "__main__":
    recorder = HQCameraRecorder()
    
    try:
        # --- TAKE A PICTURE ---
        recorder.setup_camera(mode="still")
        recorder.take_picture("snapshot.jpg")
        
        # Give the sensor a second to switch gears
        time.sleep(1) 
        
        # --- RECORD A VIDEO ---
        recorder.setup_camera(mode="video")
        recorder.record_video("mission_clip.h264", duration_seconds=10)
        
    finally:
        recorder.cleanup()