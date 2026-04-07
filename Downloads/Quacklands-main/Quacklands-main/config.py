"""Game configuration and settings

Central configuration module for Legend of the First Flock.
Initializes pygame, screen display, GUI manager, colors, fonts,
and loads story data from JSON files.
"""

import pygame
import pygame_gui
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- SCREEN SETTINGS ---
pygame.init()
info = pygame.display.Info()
WIDTH = info.current_w
HEIGHT = info.current_h
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Legend of the First Flock")

# --- GUI MANAGER ---
# Create temporary theme with absolute paths for pygame_gui
import warnings
warnings.filterwarnings('ignore', category=UserWarning, module='pygame_gui')

manager = pygame_gui.UIManager((WIDTH, HEIGHT))

# --- COLOR PALETTE ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LIGHT_GRAY = (200, 200, 200)
GOLD = (255, 215, 0)
RED = (255, 0, 0)
GREEN = (0, 200, 0)
BLUE = (0, 150, 255)

# --- FONT LOADING ---
# Font file paths with fallback to system fonts
_FONT_TITLE = os.path.join(BASE_DIR, 'assets', 'font', 'Delius_Swash_Caps', 'DeliusSwashCaps-Regular.ttf')
_FONT_BODY  = os.path.join(BASE_DIR, 'assets', 'font', 'Delius', 'Delius-Regular.ttf')

# Load fonts with fallback to system fonts if custom fonts not found
try:
    if os.path.exists(_FONT_TITLE):
        font_title = pygame.font.Font(_FONT_TITLE, 60)
        font_chapter = pygame.font.Font(_FONT_TITLE, 92)
    else:
        font_title = pygame.font.Font(None, 60)
        font_chapter = pygame.font.Font(None, 92)
except Exception:
    font_title = pygame.font.Font(None, 60)
    font_chapter = pygame.font.Font(None, 92)

try:
    if os.path.exists(_FONT_BODY):
        font_large = pygame.font.Font(_FONT_BODY, 40)
        font       = pygame.font.Font(_FONT_BODY, 36)
        font_small = pygame.font.Font(_FONT_BODY, 26)
    else:
        font_large = pygame.font.Font(None, 40)
        font       = pygame.font.Font(None, 36)
        font_small = pygame.font.Font(None, 26)
except Exception:
    font_large = pygame.font.Font(None, 40)
    font       = pygame.font.Font(None, 36)
    font_small = pygame.font.Font(None, 26)

# --- STORY DATA LOADING ---
# Load game narrative and puzzle definitions from JSON
story_path = os.path.join(BASE_DIR, 'story', 'story.json')
if not os.path.exists(story_path):
    story_path = os.path.join(BASE_DIR, 'json', 'story.json')

with open(story_path, 'r', encoding='utf-8-sig') as f:
    story_data = json.load(f)

# Extract scenes and game elements from loaded data
scenes = story_data['scenes']
elements = story_data['elements']
