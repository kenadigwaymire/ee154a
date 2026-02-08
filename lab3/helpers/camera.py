import time
from picamera2 import Picamera2

class HQCameraRecorder:
    def __init__(self, output_file="video.h264"):
        self.output_file = output_file
        self.picam2 = Picamera2()
        
    def setup_camera(self):
        # Configure the camera for video
        # We use a standard 1080p configuration for smooth recording
        config = self.picam2.create_video_configuration(main={"size": (1920, 1080)})
        self.picam2.configure(config)
        print("Camera configured for 1080p.")

    def record_video(self, duration_seconds=5):
        print(f"Starting recording: {self.output_file}")
        
        # Start the video encoder and save to file
        self.picam2.start_recording(self.output_file)
        
        # Wait for the duration
        time.sleep(duration_seconds)
        
        # Stop recording
        self.picam2.stop_recording()
        print("Recording finished.")

if __name__ == "__main__":
    # Initialize our class
    recorder = HQCameraRecorder("my_pi_video.h264")
    
    try:
        recorder.setup_camera()
        recorder.record_video(10) # Record for 10 seconds
    finally:
        # Ensure resources are released
        print("Closing camera.")
        self.picam2.close()