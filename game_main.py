# game_main.py
import time
import pygame
import sys
import queue
from collections import deque
import os
import state  # our pause flag

# (Player, ParallaxBackground, load_textures, and load_level remain unchanged)
class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 30, 50)
        self.velocity = pygame.math.Vector2(0, 0)
        self.facing = 'right'
        self.is_grounded = False
        self.speed = 5
        self.friction = 0.7
        self.sprite_right = pygame.image.load(os.path.join('textures', 'player_right.png'))
        self.sprite_left = pygame.image.load(os.path.join('textures', 'player_left.png'))
        self.sprite_right = pygame.transform.scale(self.sprite_right, (self.rect.width, self.rect.height))
        self.sprite_left = pygame.transform.scale(self.sprite_left, (self.rect.width, self.rect.height))
        self.current_sprite = self.sprite_right

    def update_sprite(self):
        if self.facing == 'right':
            self.current_sprite = self.sprite_right
        else:
            self.current_sprite = self.sprite_left

class ParallaxBackground:
    def __init__(self, image_path, screen_width, screen_height, level_height, parallax_factor=0.4):
        self.original_image = pygame.image.load(image_path)
        self.original_width = self.original_image.get_width()
        self.original_height = self.original_image.get_height()
        width_scale = (screen_width * 1.7) / self.original_width
        self.width = int(self.original_width * width_scale)
        self.height = int(self.original_height * width_scale)
        self.screen_height = screen_height
        self.level_height = level_height
        self.image = pygame.transform.scale(self.original_image, (self.width, self.height))
        self.parallax_factor = parallax_factor

    def draw(self, screen, camera, level_width, level_height):
        level_center_x = level_width / 2
        bg_x = -camera.x * self.parallax_factor + (level_center_x - self.width / 2)
        bottom_offset = self.screen_height * 0.5
        bg_y = level_height - self.height + bottom_offset
        bg_y = bg_y - camera.y * self.parallax_factor
        screen.blit(self.image, (bg_x, bg_y))

def load_textures():
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

# Modified game_main.py sections

def render_text_with_outline(surface, text, font, text_color, outline_color, position):
    """Render text with an outline effect by drawing the text multiple times with offsets."""
    text_surface = font.render(text, True, outline_color)
    offset = 2  # Thickness of outline
    
    # Draw outline positions
    for dx, dy in [(-offset, -offset), (-offset, 0), (-offset, offset), 
                   (0, -offset), (0, offset),
                   (offset, -offset), (offset, 0), (offset, offset)]:
        outline_rect = text_surface.get_rect(topright=(position[0] + dx, position[1] + dy))
        surface.blit(text_surface, outline_rect)
    
    # Draw main text
    main_text_surface = font.render(text, True, text_color)
    main_rect = main_text_surface.get_rect(topright=position)
    surface.blit(main_text_surface, main_rect)


def load_level(filename):
    platforms = []
    walls = []
    start_platforms = []
    end_triggers = []  # New list for end trigger areas
    start_x = 100
    start_y = 100
    found_start = False
    
    with open(filename, 'r') as f:
        for y, line in enumerate(f):
            for x, char in enumerate(line.strip()):
                if char in ('G', 'P', 'S', 'W', 'E'):  # Added 'E' for end trigger
                    if (x * 64) % 64 == 0 and (y * 64) % 64 == 0:
                        platform = pygame.Rect(x*64, y*64, 64, 64)
                        if char == 'G':
                            walls.append(platform)
                        elif char == 'S':
                            start_platforms.append(platform)
                            if not found_start:
                                start_x = x*64 + (64 - 30) // 2
                                start_y = y*64 - 50
                                found_start = True
                        elif char == 'E':  # Handle end trigger areas
                            end_triggers.append(platform)
                        else:
                            platforms.append(platform)
    
    if not any(p.y == 0 for p in platforms) and not any(w.y == 0 for w in walls):
        walls.append(pygame.Rect(0, 0, 800, 10))
    
    return platforms, walls, start_platforms, end_triggers, start_x, start_y

def load_textures():
    textures = {
        'platform': pygame.transform.scale(
            pygame.image.load(os.path.join('textures', 'platform.png')), (64, 64)
        ),
        'wall': pygame.transform.scale(
            pygame.image.load(os.path.join('textures', 'wall.png')), (64, 64)
        ),
        'start': pygame.transform.scale(
            pygame.image.load(os.path.join('textures', 'platform.png')), (64, 64)
        ),
        'end': pygame.transform.scale(  # New texture for end trigger
            pygame.image.load(os.path.join('textures', 'platform.png')), (64, 64)
        )
    }
    # Add a color overlay to the end texture to distinguish it
    end_surface = textures['end'].copy()
    overlay = pygame.Surface((64, 64), pygame.SRCALPHA)
    overlay.fill((0, 255, 0, 100))  # Green semi-transparent overlay
    end_surface.blit(overlay, (0, 0))
    textures['end'] = end_surface
    
    return textures

def show_completion_screen(screen, clock, screen_width, screen_height, completion_time):
    overlay = pygame.Surface((screen_width, screen_height))
    overlay.set_alpha(150)
    overlay.fill((0, 0, 0))

    font_large = pygame.font.SysFont(None, 60)
    font_medium = pygame.font.SysFont(None, 40)
    
    # Format completion time (seconds) to minutes:seconds.milliseconds
    minutes = int(completion_time // 60)
    seconds = int(completion_time % 60)
    milliseconds = int((completion_time % 1) * 1000)
    time_text = f"{minutes:02d}:{seconds:02d}.{milliseconds:03d}"
    
    title_text = font_large.render("Level Complete!", True, (255, 255, 255))
    time_display = font_medium.render(f"Your Time: {time_text}", True, (255, 255, 255))
    continue_text = font_medium.render("Press any key to continue", True, (255, 255, 255))
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                return "main_menu"
        
        screen.blit(overlay, (0, 0))
        screen.blit(title_text, title_text.get_rect(center=(screen_width//2, screen_height//2 - 60)))
        screen.blit(time_display, time_display.get_rect(center=(screen_width//2, screen_height//2)))
        screen.blit(continue_text, continue_text.get_rect(center=(screen_width//2, screen_height//2 + 60)))
        
        pygame.display.flip()
        clock.tick(60)

def format_time(seconds):
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    milliseconds = int((seconds % 1) * 100)
    return f"{minutes:02d}:{seconds:02d}.{milliseconds:02d}"

def pause_menu(screen, clock, screen_width, screen_height):
    # Set pause flag so jump detection stops
    import state
    state.paused = True
    overlay = pygame.Surface((screen_width, screen_height))
    overlay.set_alpha(50)  # Slightly more transparent overlay
    overlay.fill((0, 0, 0))

    font = pygame.font.SysFont(None, 40)
    resume_rect = pygame.Rect(screen_width//2 - 100, screen_height//2 - 60, 200, 50)
    menu_rect = pygame.Rect(screen_width//2 - 100, screen_height//2 + 10, 200, 50)
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    state.paused = False
                    return "resume"
            if event.type == pygame.MOUSEBUTTONDOWN:
                if resume_rect.collidepoint(event.pos):
                    state.paused = False
                    return "resume"
                if menu_rect.collidepoint(event.pos):
                    # Do not quit completely, just return to main menu.
                    return "main_menu"

        screen.blit(overlay, (0, 0))
        pygame.draw.rect(screen, (150, 150, 150), resume_rect)
        pygame.draw.rect(screen, (150, 150, 150), menu_rect)
        resume_text = font.render("Resume", True, (255, 255, 255))
        menu_text = font.render("Quit", True, (255, 255, 255))
        screen.blit(resume_text, resume_text.get_rect(center=resume_rect.center))
        screen.blit(menu_text, menu_text.get_rect(center=menu_rect.center))
        pygame.display.flip()
        clock.tick(60)

def start_game(jump_queue, shutdown_event):
    pygame.init()
    screen_width = int(800*1.25)
    screen_height = int(600*1.5)
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("JIJI - Enhanced Graphics Version")
    WHITE = (255, 255, 255)
    
    GRAVITY = 0.5
    MAX_JUMP_FORCE = 30
    JUMP_COOLDOWN = 400  # ms
    COLLISION_PADDING = 2
    PLATFORM_MARGIN = 4
    MAX_FALL_SPEED = 25

    textures = load_textures()
    platforms, walls, start_platforms, end_triggers, start_x, start_y = load_level('level1.txt')
    player = Player(start_x, start_y)
    camera = pygame.math.Vector2(0, 0)
    
    jump_force_buffer = deque(maxlen=3)
    last_jump_time = 0
    
    all_objects = platforms + walls + start_platforms + end_triggers
    level_width = max(p.x for p in all_objects) + 64 if all_objects else 800
    level_height = max(p.y for p in all_objects) + 64 if all_objects else 600

    background = ParallaxBackground(os.path.join('textures', 'background.png'), 
                                   screen_width, screen_height, level_height, 0.3)

    clock = pygame.time.Clock()
    # Define pause button on the left side
    pause_button = pygame.Rect(10, 10, 40, 40)  # Positioned at top-left

    # Timer variables
    start_time = time.time()
    pause_start_time = 0
    total_pause_time = 0
    level_completed = False
    completion_time = 0
    
    # Font for timer display
    timer_font = pygame.font.SysFont(None, 36)

    running = True
    while running and not shutdown_event.is_set():
        delta_time = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                shutdown_event.set()
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pause_start_time = time.time()
                    action = pause_menu(screen, clock, screen_width, screen_height)
                    total_pause_time += time.time() - pause_start_time
                    if action == "main_menu":
                        shutdown_event.set()
                        running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if pause_button.collidepoint(event.pos):
                    pause_start_time = time.time()
                    action = pause_menu(screen, clock, screen_width, screen_height)
                    total_pause_time += time.time() - pause_start_time
                    if action == "main_menu":
                        shutdown_event.set()
                        running = False

        # Skip game logic if level is completed
        if not level_completed:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT]:
                player.facing = 'left'
            if keys[pygame.K_RIGHT]:
                player.facing = 'right'
            
            player.update_sprite()

            current_time = pygame.time.get_ticks()
            try:
                while True:
                    msg = jump_queue.get_nowait()
                    if isinstance(msg, tuple):
                        if msg[0] == "direction":
                            player.facing = msg[1]
                        elif msg[0] == "jump":
                            force, direction = msg[1], msg[2]
                            player.facing = direction
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

            player.velocity.y = min(player.velocity.y + GRAVITY * delta_time * 60, MAX_FALL_SPEED)
            
            if player.is_grounded:
                player.velocity.x *= player.friction ** (delta_time * 60)
                if abs(player.velocity.x) < 0.5:
                    player.velocity.x = 0

            player.rect.x += player.velocity.x
            for obj in platforms + walls + start_platforms:
                if player.rect.colliderect(obj):
                    if player.velocity.x > 0:
                        player.rect.right = obj.left - PLATFORM_MARGIN
                    elif player.velocity.x < 0:
                        player.rect.left = obj.right + PLATFORM_MARGIN
                    player.velocity.x = 0
                    break

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

            # Check for collision with end triggers
            for end_trigger in end_triggers:
                if player.rect.colliderect(end_trigger):
                    level_completed = True
                    completion_time = time.time() - start_time - total_pause_time
                    break

            player.rect.x = max(0, min(player.rect.x, level_width - player.rect.width))
            player.rect.y = max(0, min(player.rect.y, level_height - player.rect.height))

            target_x = player.rect.centerx - screen_width // 2
            target_y = player.rect.centery - screen_height // 2
            lerp_speed = 0.1  # Lower value = smoother but slower camera
            max_movement = 15  # Maximum camera movement per frame

            # Calculate desired movement
            dx = (target_x - camera.x) * lerp_speed
            dy = (target_y - camera.y) * lerp_speed

            # Clamp movement to prevent large jumps
            dx = max(min(dx, max_movement), -max_movement)
            dy = max(min(dy, max_movement), -max_movement)

            # Apply movement
            camera.x += dx
            camera.y += dy

        screen.fill(WHITE)
        background.draw(screen, camera, level_width, level_height)
        for platform in platforms:
            adj_pos = (platform.x - camera.x, platform.y - camera.y)
            screen.blit(textures['platform'], adj_pos)
        for wall in walls:
            adj_pos = (wall.x - camera.x, wall.y - camera.y)
            screen.blit(textures['wall'], adj_pos)
        for start_platform in start_platforms:
            adj_pos = (start_platform.x - camera.x, start_platform.y - camera.y)
            screen.blit(textures['start'], adj_pos)
        for end_trigger in end_triggers:
            adj_pos = (end_trigger.x - camera.x, end_trigger.y - camera.y)
            screen.blit(textures['end'], adj_pos)
        
        player_pos = (player.rect.x - camera.x, player.rect.y - camera.y)
        screen.blit(player.current_sprite, player_pos)

        # Draw pause button
        button_color = (50, 50, 50)
        bar_width = 10
        bar_height = 20
        gap = 10
        total_width = bar_width * 2 + gap
        x_offset = pause_button.x + (pause_button.width - total_width) // 2
        y_offset = pause_button.y + (pause_button.height - bar_height) // 2

        first_bar = pygame.Rect(x_offset, y_offset, bar_width, bar_height)
        second_bar = pygame.Rect(x_offset + bar_width + gap, y_offset, bar_width, bar_height)
        pygame.draw.rect(screen, button_color, first_bar)
        pygame.draw.rect(screen, button_color, second_bar)
        pygame.draw.rect(screen, button_color, pause_button, 2)

        # Display timer in top right corner
        if not level_completed:
            current_time = time.time() - start_time - total_pause_time
            timer_text = format_time(current_time)
        else:
            timer_text = format_time(completion_time)
        
        render_text_with_outline(
            screen, 
            timer_text, 
            timer_font, 
            (0, 0, 0),  # Text color (black)
            (255, 255, 255),  # Outline color (white)
            (screen_width - 20, 20)  # Position (top right)
        )

        pygame.display.flip()
        
        # Show completion screen if level is completed
        if level_completed:
            action = show_completion_screen(screen, clock, screen_width, screen_height, completion_time)
            if action == "main_menu":
                shutdown_event.set()
                running = False

    pygame.quit()