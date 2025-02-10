import pygame
import sys
import queue

class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 30, 50)
        self.velocity = pygame.math.Vector2(0, 0)
        self.facing = 'right'
        self.is_grounded = False
        self.speed = 5
        self.friction = 0.8

def load_level(filename):
    platforms = []
    start_x = 100  # Default start position
    start_y = 100
    found_start = False
    
    with open(filename, 'r') as f:
        for y, line in enumerate(f):
            for x, char in enumerate(line.strip()):
                # Create platform for G, P, or S
                if char in ('G', 'P', 'S'):
                    platforms.append(pygame.Rect(x*64, y*64, 64, 64))
                    # Set start position if we find S
                    if char == 'S' and not found_start:
                        # Center player on platform cell
                        start_x = x*64 + (64 - 30) // 2  # 30 is player width
                        start_y = y*64 - 50  # Position above platform
                        found_start = True
    return platforms, start_x, start_y

def start_game(jump_queue):
    pygame.init()
    screen_width = 800
    screen_height = 600
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("JIJI")

    # Colors
    WHITE = (255, 255, 255)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)  # Start platform color
    
    # Physics
    GRAVITY = 0.5

    # Load level and create player
    platforms, start_x, start_y = load_level('level2.txt')
    player = Player(start_x, start_y)
    camera = pygame.math.Vector2(0, 0)

    clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        # Input handling
        keys = pygame.key.get_pressed()
        
        # Horizontal look direction
        if keys[pygame.K_LEFT]:
            player.facing = 'left'
        if keys[pygame.K_RIGHT]:
            player.facing = 'right'

        # Process jump events from queue
        jump_forces = []
        while not jump_queue.empty():
            try:
                jump_force = jump_queue.get_nowait()
                jump_forces.append(jump_force)
            except queue.Empty:
                break

        if jump_forces and player.is_grounded:
            # Use the maximum jump force detected
            max_force = max(jump_forces)
            player.velocity.y = -max_force
            player.velocity.x = player.speed if player.facing == 'right' else -player.speed
            player.is_grounded = False

        # Apply friction when grounded
        if player.is_grounded:
            player.velocity.x *= player.friction
            if abs(player.velocity.x) < 0.5:
                player.velocity.x = 0

        # Apply gravity
        player.velocity.y += GRAVITY

        # Horizontal movement and collision
        player.rect.x += player.velocity.x
        for platform in platforms:
            if player.rect.colliderect(platform):
                if player.velocity.x > 0:
                    player.rect.right = platform.left
                elif player.velocity.x < 0:
                    player.rect.left = platform.right
                player.velocity.x = 0

        # Vertical movement and collision
        player.rect.y += player.velocity.y
        player.is_grounded = False
        for platform in platforms:
            if player.rect.colliderect(platform):
                if player.velocity.y > 0:
                    player.rect.bottom = platform.top
                    player.is_grounded = True
                elif player.velocity.y < 0:
                    player.rect.top = platform.bottom
                player.velocity.y = 0

        # Camera tracking
        camera.x = player.rect.centerx - screen_width // 2
        camera.y = player.rect.centery - screen_height // 2

        # Draw everything
        screen.fill(WHITE)
        
        # Draw platforms
        for platform in platforms:
            adjusted_pos = (platform.x - camera.x, platform.y - camera.y)
            color = BLUE if (platform.y == player.rect.bottom + 50) else GREEN
            pygame.draw.rect(screen, color, (*adjusted_pos, platform.width, platform.height))
        
        # Draw player
        player_pos = (player.rect.x - camera.x, player.rect.y - camera.y)
        pygame.draw.rect(screen, RED, (*player_pos, player.rect.width, player.rect.height))

        pygame.display.flip()
        clock.tick(60)