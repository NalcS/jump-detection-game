import cv2
import time
from collections import deque

scale_factor = 1.4

def start_jump_detection(jump_queue):
    print("Starting jump detection with visual feedback...")
    
    # Initialize camera with default parameters
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open camera!")
        return
    
    # Set up face detection
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    
    # Tracking variables
    position_history = deque(maxlen=30)  # Stores up to 1 second of data at 30fps
    last_detection_time = time.time()
    velocity_threshold = 100  # pixels per second
    cooldown = 0.2  # seconds between jump detections
    
    # Main loop
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Camera error!")
            break
        
        # Basic face detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(
            gray, 
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(50, 50))
        
        if len(faces) > 0:
            x, y, w, h = max(faces, key=lambda f: f[2]*f[3])
            face_size = w * h
            current_time = time.time()
            
            # Store position with timestamp
            position_history.append((current_time, y))
            
            # Calculate velocity over a 0.1s window
            window = 0.1
            cutoff = current_time - window
            recent_positions = [entry for entry in position_history if entry[0] >= cutoff]
            
            velocity = 0
            if len(recent_positions) >= 2:
                oldest_entry = recent_positions[0]
                newest_entry = recent_positions[-1]
                delta_time = newest_entry[0] - oldest_entry[0]
                delta_y = oldest_entry[1] - newest_entry[1]  # Positive if moving up
                
                if delta_time > 0:
                    velocity = delta_y / delta_time

            # Jump detection with cooldown
            if (velocity > velocity_threshold and 
                (current_time - last_detection_time) > cooldown):
                jump_force = min((velocity / face_size) * 250, 35)
                jump_queue.put(jump_force)
                last_detection_time = current_time
            
            # Draw face rectangle
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

        # Resize frame for better processing
        new_width = int(frame.shape[1] * scale_factor)
        new_height = int(frame.shape[0] * scale_factor)
        frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)

        # Always show the camera window
        cv2.imshow("Jump Detection - Face Tracking", frame)
        
        # Exit on 'q' press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()