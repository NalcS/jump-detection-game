import threading
import queue
import jump_detection
import game_main

# Create a queue for communication between threads
jump_queue = queue.Queue()

# Create a shutdown event to signal both threads to stop
shutdown_event = threading.Event()

# Starting threads
thread_game = threading.Thread(target=game_main.start_game, args=(jump_queue, shutdown_event))
thread_game.start()

thread_cv = threading.Thread(target=jump_detection.start_jump_detection, args=(jump_queue, shutdown_event))
thread_cv.start()

# Optionally, wait for both threads to finish
thread_game.join()
thread_cv.join()
