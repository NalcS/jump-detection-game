import cv2

# Global variables for previous face position
prev_square_y = 0.0

def start_jump_detection(jump_queue):
    global prev_square_y
    print("Starting jump detection...")

    cap = cv2.VideoCapture(0)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    scale_factor = 1.5

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Resize frame for better processing
        new_width = int(frame.shape[1] * scale_factor)
        new_height = int(frame.shape[0] * scale_factor)
        frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)

        # Detect faces
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        if len(faces) > 0:
            # Track the largest face
            largest_face = max(faces, key=lambda f: f[2] * f[3])
            x, y, w, h = largest_face

            # Calculate vertical movement and jump force
            delta_y = prev_square_y - y
            prev_square_y = y

            if delta_y > 30:  # Threshold for jump detection
                face_area = w * h
                scaling_factor = 10000  # Adjust based on desired sensitivity
                jump_force = (delta_y / face_area) * scaling_factor
                jump_queue.put(jump_force)
                print(f"Jump detected! Force: {jump_force:.2f}")

            # Draw bounding box
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        else:
            prev_square_y = 0.0  # Reset if no face detected

        cv2.imshow("Webcam", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()