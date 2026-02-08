import time
import os
from picamera2 import Picamera2


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
        from picamera2.outputs import FileOutput
        self.picam2.start_recording(FileOutput(path))
        
        time.sleep(duration_seconds)
        self.picam2.stop_recording()
        print("Recording finished.")

    def setup_camera(self, mode="video"):
        """Configures the camera, ensuring it is stopped first if already running."""
        
        # 1. STOP THE CAMERA FIRST
        # If the camera is already running (from a previous take_picture), 
        # we must kill the stream before changing settings.
        try:
            self.picam2.stop()
            print("Stopping stream for reconfiguration...")
        except:
            # If it wasn't running yet, stop() might throw an error; we just ignore it.
            pass

        # 2. CONFIGURE
        if mode == "video":
            config = self.picam2.create_video_configuration(main={"size": (640, 480)})
            print("Camera configured for 480p Video.")
        else:
            config = self.picam2.create_still_configuration()
            print("Camera configured for High-Res Still.")
            
        self.picam2.configure(config)
        
        # 3. START
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
        
        # --- RECORD A VIDEO ---
        recorder.setup_camera(mode="video")
        recorder.record_video("mission_clip.h264", duration_seconds=10)
        
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        recorder.cleanup()