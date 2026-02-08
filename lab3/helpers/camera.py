import time
import os
from picamera2 import Picamera2
from picamera2.outputs import FileOutput

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

    def record_video(self, filename="video.h264", duration_seconds=5):
        path = os.path.join(self.folder, filename)
        print(f"Starting recording: {path}")
        
        # FIX: start_recording requires an output object, not just a string
        self.picam2.start_recording(FileOutput(path))
        
        time.sleep(duration_seconds)
        self.picam2.stop_recording()
        print("Recording finished.")

    def setup_camera(self, mode="video"):
        """Configures the camera, stopping it first if it's already active."""
        # Use getattr to safely check for the running state
        if getattr(self.picam2, "_running", False):
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
        recorder.take_picture("snapshot.jpg")
        
        time.sleep(1) 
        
        # --- RECORD A VIDEO ---
        recorder.setup_camera(mode="video")
        recorder.record_video("mission_clip.h264", duration_seconds=10)
        
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        recorder.cleanup()