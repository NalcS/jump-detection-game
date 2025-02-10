import pygame
import sys
import queue
from collections import deque

class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 30, 50)
        self.velocity = pygame.math.Vector2(0, 0)
        self.facing = 'right'
        self.is_grounded = False
        self.speed = 5
        self.friction = 0.7

def load_level(filename):
    platforms = []
    start_x = 100
    start_y = 100
    found_start = False
    
    with open(filename, 'r') as f:
        for y, line in enumerate(f):
            for x, char in enumerate(line.strip()):
                if char in ('G', 'P', 'S'):
                    # Create platform with grid alignment check
                    if (x * 64) % 64 == 0 and (y * 64) % 64 == 0:
                        platform = pygame.Rect(x*64, y*64, 64, 64)
                        platforms.append(platform)
                        
                        if char == 'S' and not found_start:
                            start_x = x*64 + (64 - 30) // 2
                            start_y = y*64 - 50
                            found_start = True
    
    # Add safety walls if missing
    if not any(p.y == 0 for p in platforms):
        platforms.append(pygame.Rect(0, 0, 800, 10))
    return platforms, start_x, start_y

def start_game(jump_queue):
    pygame.init()
    screen_width = 800*1.25
    screen_height = 600*1.5
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("JIJI - Stable Version")

    # Colors
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

    # Load level
    platforms, start_x, start_y = load_level('level2.txt')
    player = Player(start_x, start_y)
    camera = pygame.math.Vector2(0, 0)
    
    # Jump system
    jump_force_buffer = deque(maxlen=3)
    last_jump_time = 0
    clock = pygame.time.Clock()
    
    # Calculate level boundaries
    level_width = max(p.x for p in platforms) + 64 if platforms else 800
    level_height = max(p.y for p in platforms) + 64 if platforms else 600

    while True:
        delta_time = clock.tick(60) / 1000.0

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        # Input processing
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            player.facing = 'left'
        if keys[pygame.K_RIGHT]:
            player.facing = 'right'

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
        for platform in platforms:
            if player.rect.colliderect(platform):
                if player.velocity.x > 0:
                    player.rect.right = platform.left - PLATFORM_MARGIN
                elif player.velocity.x < 0:
                    player.rect.left = platform.right + PLATFORM_MARGIN
                player.velocity.x = 0
                break

        # Vertical movement and collision
        player.rect.y += player.velocity.y
        player.is_grounded = False
        for platform in platforms:
            if player.rect.colliderect(platform):
                if player.velocity.y > 0:
                    player.rect.bottom = platform.top - COLLISION_PADDING
                    player.is_grounded = True
                elif player.velocity.y < 0:
                    player.rect.top = platform.bottom + COLLISION_PADDING
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

        # Drawing
        screen.fill(WHITE)
        
        # Draw platforms
        for platform in platforms:
            adj_pos = (platform.x - camera.x, platform.y - camera.y)
            color = GREEN
            if platform.width == 64 and platform.height == 64:  # Regular platforms
                color = BLUE if 'S' in [c for row in open('level2.txt') for c in row] else GREEN
            pygame.draw.rect(screen, color, (*adj_pos, platform.width, platform.height))
        
        # Draw player
        player_pos = (player.rect.x - camera.x, player.rect.y - camera.y)
        pygame.draw.rect(screen, RED, (*player_pos, player.rect.width, player.rect.height))

        pygame.display.flip()

if __name__ == "__main__":
    start_game(queue.Queue())