# config.py
#!/usr/bin/env python3
"""
Configuration for the Jump Game.
All magic numbers and hard-coded values are centralized here.
"""

# Screen settings
SCREEN_WIDTH = int(800 * 1.25)
SCREEN_HEIGHT = int(600 * 1.5)

# Colors (RGB)
WHITE = (255, 255, 255)
RED   = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE  = (0, 0, 255)

# Physics constants
FIXED_DT = 1 / 60.0        # Fixed timestep (in seconds)
GRAVITY = 0.5              # Gravity per fixed update step
MAX_JUMP_FORCE = 30        # Maximum jump force (as detected)
JUMP_COOLDOWN_MS = 400     # Cooldown in milliseconds between jumps
MAX_FALL_SPEED = 25        # Terminal velocity

# Platform constants
PLATFORM_SIZE = 64         # Width/height of a platform block
PLATFORM_MARGIN = 4        # Margin used for collision resolution horizontally
COLLISION_PADDING = 2      # Padding from platform when landing

# Jump detection constants (used by jump_detection.py)
DETECTION_SCALE_FACTOR = 1.4
DETECTION_VELOCITY_THRESHOLD = 130  # Minimum velocity (after regression) to trigger a jump
DETECTION_COOLDOWN = 0.25           # In seconds
JUMP_FORCE_SCALE = 600              # Scale factor applied to computed velocity to get jump force
