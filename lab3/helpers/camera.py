import time
from picamera2 import Picamera2
from picamera2.outputs import FileOutput # Needed for recording

class HQCameraRecorder:
    def __init__(self, output_file="video.h264"):
        self.output_file = output_file
        self.picam2 = Picamera2()
        
    def setup_camera(self):
        config = self.picam2.create_video_configuration(main={"size": (1920, 1080)})
        self.picam2.configure(config)
        # Start the camera preview/stream (required before recording)
        self.picam2.start() 
        print("Camera configured and started.")

    def record_video(self, duration_seconds=5):
        print(f"Starting recording: {self.output_file}")
        
        # FIX: Explicitly tell it to use a FileOutput for the recording
        self.picam2.start_recording(FileOutput(self.output_file))
        
        time.sleep(duration_seconds)
        
        self.picam2.stop_recording()
        print("Recording finished.")

    def close(self):
        """Cleanly release hardware"""
        self.picam2.stop()
        self.picam2.close()

if __name__ == "__main__":
    recorder = HQCameraRecorder("my_pi_video.h264")
    
    try:
        recorder.setup_camera()
        recorder.record_video(10) 
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # FIX: Use 'recorder' instead of 'self'
        print("Closing camera.")
        recorder.close()