import threading
import jump_dectection
import game_main

#Starting threads
thread_game = threading.Thread(target=game_main.start_game, args=())
thread_game.start()

thread_cv = threading.Thread(target=jump_dectection.start_jump_detection, args=())
thread_cv.start()



