import threading
import queue
import jump_detection
import game_main

# Create a queue for communication between threads
jump_queue = queue.Queue()

# Starting threads
thread_game = threading.Thread(target=game_main.start_game, args=(jump_queue,))
thread_game.start()

thread_cv = threading.Thread(target=jump_detection.start_jump_detection, args=(jump_queue,))
thread_cv.start()