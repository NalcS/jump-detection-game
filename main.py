import threading
import queue
import jump_detection
import game_main

# Create communication queue
jump_queue = queue.Queue()

# Start threads with proper arguments
thread_game = threading.Thread(target=game_main.start_game, args=(jump_queue,))
thread_cv = threading.Thread(target=jump_detection.start_jump_detection, args=(jump_queue,))

thread_game.start()
thread_cv.start()

# Wait for both threads to completeq
thread_game.join()
thread_cv.join()