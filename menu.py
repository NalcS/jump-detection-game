# menu.py
import pygame
import sys

# Simple button class for menus
class Button:
    def __init__(self, rect, text, callback, font, bg_color=(100, 100, 100), text_color=(255,255,255)):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.callback = callback
        self.font = font
        self.bg_color = bg_color
        self.text_color = text_color

    def draw(self, screen):
        pygame.draw.rect(screen, self.bg_color, self.rect)
        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.callback()

def main_menu():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("JIJI - Main Menu")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 40)

    menu_choice = None

    def play_callback():
        nonlocal menu_choice
        menu_choice = "play"

    def quit_callback():
        nonlocal menu_choice
        menu_choice = "quit"

    play_button = Button(rect=(300, 200, 200, 50), text="Play", callback=play_callback, font=font)
    quit_button = Button(rect=(300, 300, 200, 50), text="Quit", callback=quit_callback, font=font)

    while menu_choice is None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                menu_choice = "quit"
            play_button.handle_event(event)
            quit_button.handle_event(event)

        screen.fill((0, 0, 0))
        play_button.draw(screen)
        quit_button.draw(screen)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    return menu_choice
