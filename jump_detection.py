# jump_detection.py
import cv2
import time
from collections import deque
import numpy as np
import state  # import our pause flag
import os
import sys

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


scale_factor = 1.4

def start_jump_detection(jump_queue, shutdown_event):
    print("Starting jump detection with enhanced motion tracking...")
    
    cv2.namedWindow("Jump Detection", cv2.WINDOW_GUI_NORMAL)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open camera!")
        return
    
    # WHEN RUNNING PROGRAM:
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    # WHEN BUILDING THE EXE:
    # cascade_path = resource_path("cv2/data/haarcascade_frontalface_default.xml")
    # face_cascade = cv2.CascadeClassifier(cascade_path)
    
    tracker = None
    detection_interval = 8
    frame_count = 0
    lost_track_frames = 0
    
    position_history = deque(maxlen=20)
    last_detection_time = time.time()
    velocity_threshold = 130
    cooldown = 0.25
    
    last_velocity = 0
    predicted_pos = None

    while not shutdown_event.is_set():
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        new_width = int(frame.shape[1] * scale_factor)
        new_height = int(frame.shape[0] * scale_factor)
        frame = cv2.resize(frame, (new_width, new_height))
        cv2.resizeWindow("Jump Detection", new_width, new_height)
        
        current_time = time.time()
        face_found = False
        y_pos = None
        
        if tracker is not None:
            success, bbox = tracker.update(frame)
            if success:
                x, y, w, h = [int(v) for v in bbox]
                face_found = True
                y_pos = y + h//2
                frame_count += 1
                lost_track_frames = 0
                
                if len(position_history) > 1:
                    last_velocity = (position_history[-1][1] - y_pos) / (current_time - position_history[-1][0])
            else:
                lost_track_frames += 1
                if lost_track_frames < 3 and predicted_pos is not None:
                    y_pos = int(predicted_pos)
                    face_found = True
                if lost_track_frames >= 3:
                    tracker = None

        if not face_found or frame_count >= detection_interval:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(
                gray, 
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(50, 50))
            
            if len(faces) > 0:
                x, y, w, h = max(faces, key=lambda f: f[2]*f[3])
                tracker = cv2.TrackerCSRT_create()
                tracker.init(frame, (x, y, w, h))
                face_found = True
                y_pos = y + h//2
                frame_count = 0
                lost_track_frames = 0

        if face_found:
            frame_center_x = frame.shape[1] // 2
            face_center_x = x + w // 2
            facing_direction = "left" if face_center_x < frame_center_x else "right"
            if not state.paused:  # Only add to the queue when not paused
                jump_queue.put(("direction", facing_direction))
            position_history.append((current_time, y_pos))
            predicted_pos = y_pos + last_velocity * (1/30)
        elif predicted_pos is not None:
            position_history.append((current_time, int(predicted_pos)))
            predicted_pos += last_velocity * (1/30)

        if len(position_history) >= 2:
            cutoff = current_time - 0.2
            valid_entries = [p for p in position_history if p[0] >= cutoff]
            
            if len(valid_entries) >= 2:
                times = np.array([p[0] for p in valid_entries])
                y_positions = np.array([p[1] for p in valid_entries])
                coeffs = np.polyfit(times, y_positions, 1)
                velocity = -coeffs[0]

                if (velocity > velocity_threshold and 
                    (current_time - last_detection_time) > cooldown):
                    face_size = w * h if face_found else 2500
                    jump_force = min((velocity / face_size) * 800, 20)
                    if not state.paused:
                        jump_queue.put(("jump", jump_force, facing_direction))
                    last_detection_time = current_time
                    position_history.clear()

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
