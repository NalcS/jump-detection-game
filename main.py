# main.py
import threading
import queue
import jump_detection
import game_main
import menu
import os
import sys

if __name__ == "__main__":
    choice = menu.main_menu()
    if choice == "quit":
        exit()

    # Create a queue for communication between threads
    jump_queue = queue.Queue()

    # Create a shutdown event to signal both threads to stop
    shutdown_event = threading.Event()

    # Starting threads only when "Play" is selected
    thread_game = threading.Thread(target=game_main.start_game, args=(jump_queue, shutdown_event))
    thread_game.start()

    thread_cv = threading.Thread(target=jump_detection.start_jump_detection, args=(jump_queue, shutdown_event))
    thread_cv.start()

    # Wait for both threads to finish
    thread_game.join()
    thread_cv.join()




def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

