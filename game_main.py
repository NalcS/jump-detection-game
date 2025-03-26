import pygame
import sys
import queue
from collections import deque
import os

class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 30, 50)
        self.velocity = pygame.math.Vector2(0, 0)
        self.facing = 'right'
        self.is_grounded = False
        self.speed = 5
        self.friction = 0.7
        # Load player sprites
        self.sprite_right = pygame.image.load(os.path.join('textures', 'player_right.png'))
        self.sprite_left = pygame.image.load(os.path.join('textures', 'player_left.png'))
        # Scale sprites to match player size
        self.sprite_right = pygame.transform.scale(self.sprite_right, (30, 50))
        self.sprite_left = pygame.transform.scale(self.sprite_left, (30, 50))
        self.current_sprite = self.sprite_right

    def update_sprite(self):
        # Update the current sprite based on facing direction
        if self.facing == 'right':
            self.current_sprite = self.sprite_right
        else:
            self.current_sprite = self.sprite_left

class ParallaxBackground:
    def __init__(self, image_path, screen_width, screen_height, level_height, parallax_factor=0.4):
        # Load the background image
        self.original_image = pygame.image.load(image_path)
        self.original_width = self.original_image.get_width()
        self.original_height = self.original_image.get_height()
        
        # Calculate scaling factor while maintaining aspect ratio
        # Make background at least 1.5x the screen width, height calculated to maintain ratio
        width_scale = (screen_width * 1.7) / self.original_width
        
        # Calculate new dimensions preserving aspect ratio
        self.width = int(self.original_width * width_scale)
        self.height = int(self.original_height * width_scale)
        
        # Store screen and level parameters for position calculations
        self.screen_height = screen_height
        self.level_height = level_height
        
        # Scale the image maintaining aspect ratio
        self.image = pygame.transform.scale(self.original_image, (self.width, self.height))
        self.parallax_factor = parallax_factor  # How much slower the background moves

    def draw(self, screen, camera, level_width, level_height):
        # Calculate horizontal center of the level
        level_center_x = level_width / 2
        
        # For horizontal positioning: center the background
        bg_x = -camera.x * self.parallax_factor + (level_center_x - self.width / 2)
        
        # For vertical positioning: align the bottom of the background with bottom of level plus a small offset
        # This ensures the background bottom is just outside camera view when at level bottom
        bottom_offset = self.screen_height * 0.5  # 50% of screen height as offset
        bg_y = level_height - self.height + bottom_offset
        
        # Apply parallax effect to vertical position too
        bg_y = bg_y - camera.y * self.parallax_factor
        
        # Draw the background
        screen.blit(self.image, (bg_x, bg_y))

def load_textures():
    # Load and scale platform and wall textures
    textures = {
        'platform': pygame.transform.scale(
            pygame.image.load(os.path.join('textures', 'platform.png')), (64, 64)
        ),
        'wall': pygame.transform.scale(
            pygame.image.load(os.path.join('textures', 'wall.png')), (64, 64)
        ),
        'start': pygame.transform.scale(
            pygame.image.load(os.path.join('textures', 'platform.png')), (64, 64)
        )
    }
    return textures

def load_level(filename):
    platforms = []
    walls = []
    start_platforms = []
    start_x = 100
    start_y = 100
    found_start = False
    
    with open(filename, 'r') as f:
        for y, line in enumerate(f):
            for x, char in enumerate(line.strip()):
                if char in ('G', 'P', 'S', 'W'):
                    # Create platform with grid alignment check
                    if (x * 64) % 64 == 0 and (y * 64) % 64 == 0:
                        platform = pygame.Rect(x*64, y*64, 64, 64)
                        
                        if char == 'G':  # Wall
                            walls.append(platform)
                        elif char == 'S':  # Start platform
                            start_platforms.append(platform)
                            if not found_start:
                                start_x = x*64 + (64 - 30) // 2
                                start_y = y*64 - 50
                                found_start = True
                        else:  # Regular platform
                            platforms.append(platform)
    
    # Add safety walls if missing
    if not any(p.y == 0 for p in platforms) and not any(w.y == 0 for w in walls):
        walls.append(pygame.Rect(0, 0, 800, 10))
    
    return platforms, walls, start_platforms, start_x, start_y

def start_game(jump_queue, shutdown_event):
    pygame.init()
    screen_width = 800*1.25
    screen_height = 600*1.5
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("JIJI - Enhanced Graphics Version")

    # Colors (for fallback)
    WHITE = (255, 255, 255)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    
    # Physics constants
    GRAVITY = 0.5
    MAX_JUMP_FORCE = 30
    JUMP_COOLDOWN = 400  # ms
    COLLISION_PADDING = 2
    PLATFORM_MARGIN = 4
    MAX_FALL_SPEED = 25

    # Load textures
    textures = load_textures()

    # Load level
    platforms, walls, start_platforms, start_x, start_y = load_level('level3.txt')
    player = Player(start_x, start_y)
    camera = pygame.math.Vector2(0, 0)
    
    # Jump system
    jump_force_buffer = deque(maxlen=3)
    last_jump_time = 0
    clock = pygame.time.Clock()
    
    # Calculate level boundaries - include walls in calculation
    all_objects = platforms + walls + start_platforms
    level_width = max(p.x for p in all_objects) + 64 if all_objects else 800
    level_height = max(p.y for p in all_objects) + 64 if all_objects else 600

    # Load parallax background
    background = ParallaxBackground(os.path.join('textures', 'background.png'), 
                                   screen_width, screen_height, level_height, 0.3)

    while not shutdown_event.is_set():
        delta_time = clock.tick(60) / 1000.0

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                shutdown_event.set()
                pygame.quit()
                sys.exit()

        # Input processing
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            player.facing = 'left'
        if keys[pygame.K_RIGHT]:
            player.facing = 'right'
        
        # Update player sprite based on direction
        player.update_sprite()

        # Jump processing
        current_time = pygame.time.get_ticks()
        try:
            while True:
                force = jump_queue.get_nowait()
                if 5 <= force <= MAX_JUMP_FORCE:
                    jump_force_buffer.append(force)
        except queue.Empty:
            pass

        if jump_force_buffer and player.is_grounded:
            if (current_time - last_jump_time) > JUMP_COOLDOWN:
                avg_force = sum(jump_force_buffer) / len(jump_force_buffer)
                player.velocity.y = -avg_force
                player.velocity.x = player.speed if player.facing == 'right' else -player.speed
                player.is_grounded = False
                last_jump_time = current_time
                jump_force_buffer.clear()

        # Physics updates
        player.velocity.y = min(player.velocity.y + GRAVITY * delta_time * 60, MAX_FALL_SPEED)
        
        if player.is_grounded:
            player.velocity.x *= player.friction ** (delta_time * 60)
            if abs(player.velocity.x) < 0.5:
                player.velocity.x = 0

        # Horizontal movement and collision
        player.rect.x += player.velocity.x
        for obj in platforms + walls + start_platforms:
            if player.rect.colliderect(obj):
                if player.velocity.x > 0:
                    player.rect.right = obj.left - PLATFORM_MARGIN
                elif player.velocity.x < 0:
                    player.rect.left = obj.right + PLATFORM_MARGIN
                player.velocity.x = 0
                break

        # Vertical movement and collision
        player.rect.y += player.velocity.y
        player.is_grounded = False
        for obj in platforms + walls + start_platforms:
            if player.rect.colliderect(obj):
                if player.velocity.y > 0:
                    player.rect.bottom = obj.top - COLLISION_PADDING
                    player.is_grounded = True
                elif player.velocity.y < 0:
                    player.rect.top = obj.bottom + COLLISION_PADDING
                player.velocity.y = 0
                break

        # World boundaries
        player.rect.x = max(0, min(player.rect.x, level_width - player.rect.width))
        player.rect.y = max(0, min(player.rect.y, level_height - player.rect.height))

        # Camera smoothing
        target_x = player.rect.centerx - screen_width // 2
        target_y = player.rect.centery - screen_height // 2
        camera.x += (target_x - camera.x) * 0.5 * delta_time * 60
        camera.y += (target_y - camera.y) * 0.5 * delta_time * 60

        # Drawing - START WITH BACKGROUND
        screen.fill(WHITE)
        
        # Draw parallax background
        background.draw(screen, camera, level_width, level_height)
        
        # Draw platforms with textures
        for platform in platforms:
            adj_pos = (platform.x - camera.x, platform.y - camera.y)
            screen.blit(textures['platform'], adj_pos)
        
        # Draw walls with textures
        for wall in walls:
            adj_pos = (wall.x - camera.x, wall.y - camera.y)
            screen.blit(textures['wall'], adj_pos)
        
        # Draw start platforms with textures
        for start_platform in start_platforms:
            adj_pos = (start_platform.x - camera.x, start_platform.y - camera.y)
            screen.blit(textures['start'], adj_pos)
        
        # Draw player with appropriate sprite
        player_pos = (player.rect.x - camera.x, player.rect.y - camera.y)
        screen.blit(player.current_sprite, player_pos)

        pygame.display.flip()

if __name__ == "__main__":
    start_game(queue.Queue())