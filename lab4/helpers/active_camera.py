import cv2

# Set your resolution here
WIDTH = 640
HEIGHT = 480

# '0' is the default index for the Pi Camera on modern OS
cap = cv2.VideoCapture(0)

# Set the resolution
cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)

print(f"Starting feed at {WIDTH}x{HEIGHT}. Press 'q' to quit.")

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame.")
            break

        # Display the frame in the VNC window
        cv2.imshow('Pi Camera Feed', frame)

        # Wait for 1ms; if 'q' is pressed, exit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
finally:
    cap.release()
    cv2.destroyAllWindows()