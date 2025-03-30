import cv2
import time
from collections import deque
import numpy as np

scale_factor = 1.4

def start_jump_detection(jump_queue, shutdown_event):
    print("Starting jump detection with enhanced motion tracking...")
    
    cv2.namedWindow("Jump Detection", cv2.WINDOW_GUI_NORMAL)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open camera!")
        return
    
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    
    # Improved tracking configuration
    tracker = None
    detection_interval = 8  # More frequent re-detection (every 8 frames)
    frame_count = 0
    lost_track_frames = 0
    
    position_history = deque(maxlen=20)  # Shorter history for faster response
    last_detection_time = time.time()
    velocity_threshold = 130  # Increased threshold for deliberate jumps
    cooldown = 0.25
    
    # Motion prediction variables
    last_velocity = 0
    predicted_pos = None

    while not shutdown_event.is_set():
        ret, frame = cap.read()
        if not ret:
            break

        # Flip the frame horizontally to mirror it
        frame = cv2.flip(frame, 1)

        # Resize frame early for consistent processing
        new_width = int(frame.shape[1] * scale_factor)
        new_height = int(frame.shape[0] * scale_factor)
        frame = cv2.resize(frame, (new_width, new_height))
        cv2.resizeWindow("Jump Detection", new_width, new_height)
        
        current_time = time.time()
        face_found = False
        y_pos = None
        
        # Tracking logic with motion prediction
        if tracker is not None:
            success, bbox = tracker.update(frame)
            if success:
                x, y, w, h = [int(v) for v in bbox]
                face_found = True
                y_pos = y + h//2
                frame_count += 1
                lost_track_frames = 0
                
                # Update motion prediction
                if len(position_history) > 1:
                    last_velocity = (position_history[-1][1] - y_pos) / (current_time - position_history[-1][0])
            else:
                # Use prediction when tracking fails temporarily
                lost_track_frames += 1
                if lost_track_frames < 3 and predicted_pos is not None:
                    y_pos = int(predicted_pos)
                    face_found = True
                
                # Emergency re-detection after 3 lost frames
                if lost_track_frames >= 3:
                    tracker = None

        # Always attempt detection when not tracking or predictions failing
        if not face_found or frame_count >= detection_interval:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(
                gray, 
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(50, 50))
            
            if len(faces) > 0:
                x, y, w, h = max(faces, key=lambda f: f[2]*f[3])
                # Initialize CSRT tracker (better for fast motion)
                tracker = cv2.TrackerCSRT.create()
                tracker.init(frame, (x, y, w, h))
                face_found = True
                y_pos = y + h//2
                frame_count = 0
                lost_track_frames = 0

        # Position processing with prediction
        if face_found:
            # Determine facing direction based on horizontal position
            frame_center_x = frame.shape[1] // 2
            face_center_x = x + w // 2
            facing_direction = "left" if face_center_x < frame_center_x else "right"
            # Send direction update message continuously
            jump_queue.put(("direction", facing_direction))

            # Store actual position
            position_history.append((current_time, y_pos))
            # Predict next position based on velocity
            predicted_pos = y_pos + last_velocity * (1/30)  # Assume 30fps
        elif predicted_pos is not None:
            # Use prediction for up to 3 frames
            position_history.append((current_time, int(predicted_pos)))
            predicted_pos += last_velocity * (1/30)

        # Velocity calculation with interpolation
        if len(position_history) >= 2:
            # Use last 0.2 seconds of data
            cutoff = current_time - 0.2
            valid_entries = [p for p in position_history if p[0] >= cutoff]
            
            if len(valid_entries) >= 2:
                # Linear regression for velocity
                times = np.array([p[0] for p in valid_entries])
                y_positions = np.array([p[1] for p in valid_entries])
                coeffs = np.polyfit(times, y_positions, 1)
                velocity = -coeffs[0]  # Negative slope = upward movement

                # Jump detection logic
                if (velocity > velocity_threshold and 
                    (current_time - last_detection_time) > cooldown):
                    face_size = w * h if face_found else 2500  # Fallback size
                    jump_force = min((velocity / face_size) * 800, 20)
                    # Send jump message with force and current direction
                    jump_queue.put(("jump", jump_force, facing_direction))
                    last_detection_time = current_time
                    position_history.clear()  # Reset after jump detection

        # Visual feedback
        if face_found:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        elif predicted_pos is not None:
            cv2.putText(frame, "PREDICTING", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        
        cv2.imshow("Jump Detection", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            shutdown_event.set()
            break

    cap.release()
    cv2.destroyAllWindows()