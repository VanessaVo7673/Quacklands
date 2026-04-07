"""Game logic and rendering"""

import glob
import os
import random
import math
import re

import pygame
import pygame_gui

from config import (
    BLACK,
    BLUE,
    GOLD,
    GREEN,
    HEIGHT,
    RED,
    WHITE,
    WIDTH,
    font,
    font_chapter,
    font_large,
    font_small,
    font_title,
    manager,
    scenes,
    screen,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Game:
    """Main game controller for Legend of the First Flock.
    
    Handles all game logic, scene management, puzzle gameplay, rendering,
    user input, and asset loading. Supports multiple game scenes (menu, story,
    action sequences) and various puzzle types (drag-drop, memory, tic-tac-toe).
    """
    # Reference resolution - coordinates are designed for 1920x1080 monitors
    REFERENCE_WIDTH = 1920
    REFERENCE_HEIGHT = 1080
    
    def __init__(self):
        """Initialize the game with default state and load all assets."""
        # --- CORE GAME STATE ---
        self.current_scene = 'main_menu'
        self.collected_elements = set()
        self.ui_elements = []
        self.running = True
        
        # --- DRAG-DROP PUZZLE STATE (Chapter 2) ---
        self.dragged_piece = None
        self.offset = (0, 0)
        self.pieces = []
        
        # --- RESOLUTION SCALING ---
        # Calculate resolution scaling factors for 1920x1080 reference
        self.scale_x = WIDTH / self.REFERENCE_WIDTH
        self.scale_y = HEIGHT / self.REFERENCE_HEIGHT
        
        # --- PUZZLE ASSETS AND UI ---
        self.puzzle_frame_image = None
        self.lock_glow_image = None
        self.puzzle_complete_image = None
        self.generated_complete_image = None
        self.generated_complete_rect = None
        self.chapter1_continue_rect = None
        self.skip_button_rect = None
        self.skip_button_action = None
        
        # --- CHAPTER 1: OBSTACLE DODGE STATE ---
        self.current_obstacles = []
        self.forest_obstacles = []
        self.goal_x = None
        
        # --- COMPLETION ANIMATION STATE ---
        self.completion_anim_active = False
        self.completion_anim_time = 0.0
        self.completion_anim_action = None
        self.completion_anim_reward = None
        self.completion_shake_duration = 0.35
        self.completion_fade_duration = 0.55

        # --- STORY SCENE TEXT RENDERING ---
        self.scene_start_time = 0.0
        self.typing_speed = 20  # characters per second (slower for reading)
        self.typed_chars = 0
        self.prev_typed_chars = 0
        self.current_sentence_idx = 0
        self.sentence_pause_time = 0.0
        self.sentence_pause_duration = 1.0  # Pause for 1 second after each sentence
        self.show_prompt = False
        self.continue_button_rect = None
        self.menu_button_rects = []  # Store menu button info: [(rect, next_scene), ...]
        self.chapter_title_hold_duration = 1.35
        self.chapter_title_fade_duration = 0.75
        self.chapter1_attempted = False  # True after first death/timeout in chapter 1

        # --- CHAPTER 3: MEMORY PAIRS GAME STATE ---
        self.memory_cards = []
        self.memory_card_images = {}
        self.memory_flipped = []
        self.memory_matched = 0
        self.memory_attempts = 0
        self.memory_mismatch_timer = 0.0

        # --- CHAPTER 4: TIC-TAC-TOE GAME STATE ---
        self.tictactoe_board = [None] * 9
        self.tictactoe_player_wins = 0
        self.tictactoe_ai_wins = 0
        self.tictactoe_current_turn = 'player'  # 'player' or 'ai'
        self.ttt_player_won = False
        self.ttt_win_continue_rect = None
        self.ttt_trophy_revealed = False
        self.ttt_trophy_anim_time = 0.0
        self.ttt_mark_anims = {}       # cell_idx -> elapsed seconds (pop-in animation)
        self.ttt_ai_delay_timer = 0.0  # countdown before AI places its mark

        # --- CHAPTER 7: ELEMENT ASCENSION STATE (Final Scene) ---
        self.ascension_elements = []
        self.ascension_time = 0.0
        self.final_trophy_active = False
        self.final_trophy_revealed = False
        self.final_trophy_anim_time = 0.0
        self.final_trophy_continue_rect = None

        # --- ASSET LOADING ---
        glow_path = self.find_asset_path('aura.png')
        if glow_path:
            try:
                self.lock_glow_image = pygame.image.load(glow_path).convert_alpha()
            except Exception:
                self.lock_glow_image = None

        # Load forest and character assets
        self.forest_sky_image = None
        self.forest_grass_image = None
        self.chapter1_background_image = None
        self.duck_image = None
        self.heart_images = [None, None, None]  # heart1, heart2, heart3
        self.enter_shrine_image = None
        
        # Try to load chapter 1 background
        bg_path = self.find_asset_path('background_chapter1.png')
        if bg_path:
            try:
                self.chapter1_background_image = pygame.image.load(bg_path).convert_alpha()
            except Exception:
                pass
        
        # Try to load forest assets
        sky_path = self.find_asset_path('sky_forest.png')
        if sky_path:
            try:
                self.forest_sky_image = pygame.image.load(sky_path).convert_alpha()
            except Exception:
                pass
        
        grass_path = self.find_asset_path('grass_forest.png')
        if grass_path:
            try:
                self.forest_grass_image = pygame.image.load(grass_path).convert_alpha()
            except Exception:
                pass
        
        # Try to load duck player image
        duck_path = self.find_asset_path('duck1.png')
        if duck_path:
            try:
                self.duck_image = pygame.image.load(duck_path).convert_alpha()
            except Exception:
                pass
        
        # Try to load heart images
        for i in range(1, 4):
            heart_path = self.find_asset_path(f'heart{i}.png')
            if heart_path:
                try:
                    self.heart_images[i-1] = pygame.image.load(heart_path).convert_alpha()
                except Exception:
                    pass
        
        # Try to load shrine entrance image
        shrine_path = self.find_asset_path('enter_shrine.png')
        if shrine_path:
            try:
                self.enter_shrine_image = pygame.image.load(shrine_path).convert_alpha()
            except Exception:
                pass
        
        # Try to load exit button image
        self.exit_button_image = None
        exit_btn_path = self.find_asset_path('exit_button.png')
        if exit_btn_path:
            try:
                self.exit_button_image = pygame.image.load(exit_btn_path).convert_alpha()
            except Exception:
                pass
        
        # Try to load star button image
        self.star_button_image = None
        star_btn_path = self.find_asset_path('star.png')
        if star_btn_path:
            try:
                self.star_button_image = pygame.image.load(star_btn_path).convert_alpha()
            except Exception:
                pass
        
        self.exit_button_rect = None
        
        # Load log and rock images for Chapter 2 dodge game
        self.log_images = [None, None]  # log1, log2
        self.rock_images = [None, None]  # rock1, rock2
        self.nature_element_image = None
        
        for i in range(1, 3):
            log_path = self.find_asset_path(f'log{i}.png')
            if log_path:
                try:
                    self.log_images[i-1] = pygame.image.load(log_path).convert_alpha()
                except Exception:
                    pass
            
            rock_path = self.find_asset_path(f'rock{i}.png')
            if rock_path:
                try:
                    self.rock_images[i-1] = pygame.image.load(rock_path).convert_alpha()
                except Exception:
                    pass
        
        nature_path = self.find_asset_path('nature_element.png')
        if nature_path:
            try:
                self.nature_element_image = pygame.image.load(nature_path).convert_alpha()
            except Exception:
                pass
        
        # Dodge game state
        self.dodge_obstacles = []
        self.dodge_collectibles = []
        self.dodge_spawn_timer = 0.0
        self.collectibles_collected = 0
        
        # Initialize mixer and load background music
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        
        music_path = self.find_asset_path('music.mp3')
        if music_path:
            try:
                pygame.mixer.music.load(music_path)
                pygame.mixer.music.play(-1)  # -1 loops infinitely
            except Exception:
                pass

        # Chapter 4 (tic-tac-toe) assets
        self.ttt_board_image = None
        self.ttt_player_mark_image = None
        self.ttt_enemy_mark_image = None
        self.ttt_trophy_image = None
        for _fname, _attr in [
            ('board.png', 'ttt_board_image'),
            ('player_mark.png', 'ttt_player_mark_image'),
            ('enemy_mark.png', 'ttt_enemy_mark_image'),
            ('trophy.png', 'ttt_trophy_image'),
        ]:
            _path = self.find_asset_path(_fname)
            if _path:
                try:
                    setattr(self, _attr, pygame.image.load(_path).convert_alpha())
                except Exception:
                    pass

        self.lives = 3
        self.score = 0
        self.time_remaining = 0
        self.player_x = WIDTH // 2
        self.player_y = HEIGHT - 100
        self.player_move_speed = 360
        self.forest_distance = 0.0
        self.forest_target_distance = 0.0
        self.forest_speed = 0.0
        self.forest_spawn_timer = 0.0
        self.chapter_complete = False

        self.drops = []
        self.player_sequence = []
        self.symbol_sequence = []
        self.attempts_remaining = 3

    def check_tictactoe_winner(self, board):
        """Determine tic-tac-toe winner by checking all lines.
        
        Args:
            board: List of 9 elements representing tic-tac-toe board state
            
        Returns:
            'X' if player wins, 'O' if AI wins, None if no winner
        """
        lines = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],  # rows
            [0, 3, 6], [1, 4, 7], [2, 5, 8],  # columns
            [0, 4, 8], [2, 4, 6]               # diagonals
        ]
        for line in lines:
            if board[line[0]] == board[line[1]] == board[line[2]] and board[line[0]] is not None:
                return board[line[0]]
        return None

    def get_tictactoe_ai_move(self, board):
        """Calculate AI move for tic-tac-toe using strategic heuristics.
        
        Strategy: Try to win, block player, take center, take corners, then random.
        
        Args:
            board: List of 9 elements representing tic-tac-toe board state
            
        Returns:
            Index (0-8) where AI places its mark, or None if board full
        """
        empty = [i for i in range(9) if board[i] is None]
        if not empty:
            return None
        # Try to win
        for idx in empty:
            test_board = board[:]
            test_board[idx] = 'O'
            if self.check_tictactoe_winner(test_board) == 'O':
                return idx
        # Try to block player
        for idx in empty:
            test_board = board[:]
            test_board[idx] = 'X'
            if self.check_tictactoe_winner(test_board) == 'X':
                return idx
        # Take center
        if board[4] is None:
            return 4
        # Take corners
        corners = [0, 2, 6, 8]
        available_corners = [c for c in corners if board[c] is None]
        if available_corners:
            return random.choice(available_corners)
        # Take any available
        return random.choice(empty)

    def scale_point(self, point, design_width=1920, design_height=1080):
        """Scale a single point from design resolution to current screen resolution.
        
        Args:
            point: [x, y] coordinate in design resolution
            design_width: Original design width (default 1920)
            design_height: Original design height (default 1080)
            
        Returns:
            [x, y] coordinate scaled to current screen size
        """
        sx = WIDTH / float(design_width)
        sy = HEIGHT / float(design_height)
        return [int(round(point[0] * sx)), int(round(point[1] * sy))]

    def scale_size(self, size, design_width=1920, design_height=1080):
        """Scale dimensions while preserving aspect ratio.
        
        Args:
            size: [width, height] in design resolution
            design_width: Original design width (default 1920)
            design_height: Original design height (default 1080)
            
        Returns:
            [width, height] scaled to current screen (uniform scaling)
        """
        sx = WIDTH / float(design_width)
        sy = HEIGHT / float(design_height)
        # Use uniform scaling to preserve original aspect ratio.
        s = min(sx, sy)
        return [max(24, int(round(size[0] * s))), max(24, int(round(size[1] * s)))]

    def scale_coordinates(self, pos):
        """Scale a position from 1920x1080 reference to current screen resolution."""
        if pos is None:
            return pos
        return [int(round(pos[0] * self.scale_x)), int(round(pos[1] * self.scale_y))]

    def snap_threshold(self):
        return max(36, int(min(WIDTH, HEIGHT) * 0.06))

    def completion_tolerance(self):
        return max(12, int(self.snap_threshold() * 0.35))

    def is_piece_aligned(self, piece, tolerance=None):
        tol = self.completion_tolerance() if tolerance is None else tolerance
        dx = abs(piece['current_pos'][0] - piece['correct_pos'][0])
        dy = abs(piece['current_pos'][1] - piece['correct_pos'][1])
        return dx <= tol and dy <= tol

    def lock_piece(self, piece):
        piece['current_pos'] = piece['correct_pos'][:]
        piece['locked'] = True

    def reconcile_piece_locks(self):
        snap_tol = self.snap_threshold()
        for piece in self.pieces:
            if not piece.get('locked') and self.is_piece_aligned(piece, snap_tol):
                self.lock_piece(piece)

    def build_completed_puzzle_fallback(self):
        """Render completed puzzle by compositing all pieces at their correct positions."""
        if not self.pieces:
            self.generated_complete_image = None
            self.generated_complete_rect = None
            return

        min_x = min(piece['correct_pos'][0] for piece in self.pieces)
        min_y = min(piece['correct_pos'][1] for piece in self.pieces)
        max_x = max(piece['correct_pos'][0] + piece['size'][0] for piece in self.pieces)
        max_y = max(piece['correct_pos'][1] + piece['size'][1] for piece in self.pieces)
        width = max(1, max_x - min_x)
        height = max(1, max_y - min_y)

        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        for piece in self.pieces:
            x = piece['correct_pos'][0] - min_x
            y = piece['correct_pos'][1] - min_y
            if piece.get('image'):
                surface.blit(piece['image'], (x, y))
            else:
                pygame.draw.rect(surface, (120, 100, 80), (x, y, piece['size'][0], piece['size'][1]))
                pygame.draw.rect(surface, BLACK, (x, y, piece['size'][0], piece['size'][1]), 2)

        self.generated_complete_image = surface
        self.generated_complete_rect = pygame.Rect(min_x, min_y, width, height)

    def draw_scaled_aura(self, target_rect):
        """Draw a pulsing glow/aura effect around a target rectangle for locked pieces."""
        if target_rect is None:
            return

        pulse = 0.5 + 0.5 * (pygame.time.get_ticks() % 1400) / 1400.0
        aura_scale = 1.08 + (0.10 * pulse)
        aura_w = max(40, int(target_rect.width * aura_scale))
        aura_h = max(40, int(target_rect.height * aura_scale))
        aura_x = target_rect.centerx - aura_w // 2
        aura_y = target_rect.centery - aura_h // 2

        if self.lock_glow_image is not None:
            aura_img = pygame.transform.smoothscale(self.lock_glow_image, (aura_w, aura_h))
            aura_img.set_alpha(175)
            screen.blit(aura_img, (aura_x, aura_y))
            return

        aura_surface = pygame.Surface((aura_w, aura_h), pygame.SRCALPHA)
        outer_rect = aura_surface.get_rect()
        inner_rect = outer_rect.inflate(-max(10, aura_w // 7), -max(10, aura_h // 7))
        pygame.draw.ellipse(aura_surface, (255, 220, 110, 90), outer_rect)
        pygame.draw.ellipse(aura_surface, (255, 238, 170, 120), inner_rect)
        screen.blit(aura_surface, (aura_x, aura_y))

    def draw_chapter1_completion_prompt(self):
        """Render the completion prompt panel for Chapter 1 puzzle success."""
        if self.current_scene != 'chapter1' or not self.chapter_complete or self.completion_anim_active:
            self.chapter1_continue_rect = None
            return

        panel_w = min(1180, WIDTH - 120)
        panel_h = 220
        panel_rect = pygame.Rect((WIDTH - panel_w) // 2, HEIGHT - panel_h - 26, panel_w, panel_h)

        panel_surface = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)
        panel_surface.fill((18, 24, 34, 215))
        screen.blit(panel_surface, panel_rect.topleft)
        pygame.draw.rect(screen, (255, 215, 0), panel_rect, 3, border_radius=14)

        message = (
            'Puzzle complete! You obtained the Earth element from the ruins. '
            'Now we need to travel through the foliage to reach the next element. '
            'Would you like to continue to Chapter 2: Forest?'
        )
        text_lines = self.wrap_text(message, font_small, panel_rect.width - 40)
        text_y = panel_rect.y + 18
        for line in text_lines[:5]:
            line_surf = font_small.render(line, True, (245, 245, 245))
            screen.blit(line_surf, (panel_rect.x + 20, text_y))
            text_y += 28

        button_w = 420
        button_h = 52
        button_x = panel_rect.centerx - button_w // 2
        button_y = panel_rect.bottom - button_h - 18
        self.chapter1_continue_rect = pygame.Rect(button_x, button_y, button_w, button_h)

        pygame.draw.rect(screen, (220, 220, 100), self.chapter1_continue_rect, border_radius=12)
        pygame.draw.rect(screen, (255, 165, 0), self.chapter1_continue_rect, 3, border_radius=12)
        btn_text = font_small.render('Continue to Chapter 2: Forest', True, (60, 40, 20))
        screen.blit(btn_text, (self.chapter1_continue_rect.centerx - btn_text.get_width() // 2, self.chapter1_continue_rect.centery - btn_text.get_height() // 2))

    def start_completion_animation(self, action, reward=None):
        """Initiate a completion animation sequence (shake + fade effects)."""
        if self.completion_anim_active:
            return
        self.completion_anim_active = True
        self.completion_anim_time = 0.0
        self.completion_anim_action = action
        self.completion_anim_reward = reward

    def get_completion_durations(self):
        shake_duration = self.completion_shake_duration
        if self.completion_anim_action == 'chapter_complete':
            shake_duration = 0.0
        return shake_duration, self.completion_fade_duration

    def spawn_forest_obstacle(self):
        lane_positions = [-0.75, -0.38, 0.0, 0.38, 0.75]
        obstacle_kind = random.choice(['trunk', 'roots'])
        self.forest_obstacles.append(
            {
                'x': random.choice(lane_positions),
                'depth': 1.15,
                'kind': obstacle_kind,
                'width': 0.18 if obstacle_kind == 'trunk' else 0.28,
            }
        )

    def draw_forest_run_scene(self, shake_x, shake_y):
        """Render the forest obstacle avoidance minigame with perspective effects."""
        horizon_y = int(HEIGHT * 0.34) + shake_y
        center_x = WIDTH // 2 + shake_x

        # Draw sky and ground background
        if self.forest_sky_image:
            sky_scaled = pygame.transform.scale(self.forest_sky_image, (WIDTH, horizon_y))
            screen.blit(sky_scaled, (0, 0))
        else:
            pygame.draw.rect(screen, (162, 212, 242), pygame.Rect(0, 0, WIDTH, horizon_y))
        
        # Draw ground
        pygame.draw.rect(screen, (54, 88, 43), pygame.Rect(0, horizon_y, WIDTH, HEIGHT - horizon_y))

        path_top_half = int(WIDTH * 0.08)
        path_bottom_half = int(WIDTH * 0.34)
        path_points = [
            (center_x - path_top_half, horizon_y),
            (center_x + path_top_half, horizon_y),
            (center_x + path_bottom_half, HEIGHT),
            (center_x - path_bottom_half, HEIGHT),
        ]
        pygame.draw.polygon(screen, (120, 95, 64), path_points)
        pygame.draw.polygon(screen, (78, 56, 30), path_points, 4)

        for band in range(6):
            stripe_y = horizon_y + int((HEIGHT - horizon_y) * (band / 6.0))
            stripe_w = int(path_top_half + (path_bottom_half - path_top_half) * (band / 6.0))
            pygame.draw.line(screen, (144, 120, 84), (center_x - stripe_w, stripe_y), (center_x + stripe_w, stripe_y), 2)

        for side in (-1, 1):
            for row in range(5):
                depth = 0.22 + row * 0.18
                scale = 0.45 + row * 0.22
                tree_x = center_x + side * int(WIDTH * (0.19 + row * 0.07))
                tree_y = horizon_y + int((HEIGHT - horizon_y) * depth)
                trunk_w = int(16 * scale)
                trunk_h = int(70 * scale)
                canopy_r = int(28 * scale)
                trunk_rect = pygame.Rect(tree_x - trunk_w // 2, tree_y - trunk_h, trunk_w, trunk_h)
                pygame.draw.rect(screen, (87, 57, 32), trunk_rect, border_radius=6)
                pygame.draw.circle(screen, (44, 112, 55), (tree_x, tree_y - trunk_h), canopy_r)
                pygame.draw.circle(screen, (58, 138, 69), (tree_x - canopy_r // 2, tree_y - trunk_h + 5), canopy_r // 2)
                pygame.draw.circle(screen, (58, 138, 69), (tree_x + canopy_r // 2, tree_y - trunk_h + 5), canopy_r // 2)

        for obstacle in sorted(self.forest_obstacles, key=lambda item: item['depth'], reverse=True):
            depth_ratio = max(0.0, min(1.0, obstacle['depth']))
            perspective = 1.0 - depth_ratio
            lane_half_width = path_top_half + int((path_bottom_half - path_top_half) * perspective)
            obstacle_x = center_x + int(obstacle['x'] * lane_half_width)
            obstacle_y = horizon_y + int((HEIGHT - horizon_y) * perspective)
            scale = 0.35 + perspective * 1.6

            if obstacle['kind'] == 'trunk':
                trunk_w = int(28 * scale)
                trunk_h = int(110 * scale)
                trunk_rect = pygame.Rect(obstacle_x - trunk_w // 2, obstacle_y - trunk_h, trunk_w, trunk_h)
                pygame.draw.rect(screen, (74, 49, 28), trunk_rect, border_radius=8)
                pygame.draw.rect(screen, (109, 75, 47), trunk_rect, 3, border_radius=8)
            else:
                root_w = int(80 * scale)
                root_h = int(24 * scale)
                root_rect = pygame.Rect(obstacle_x - root_w // 2, obstacle_y - root_h // 2, root_w, root_h)
                pygame.draw.ellipse(screen, (101, 72, 41), root_rect)
                pygame.draw.ellipse(screen, (132, 98, 60), root_rect, 3)

        marker_y = HEIGHT - 80 + shake_y
        marker_x = center_x + int(self.player_x * path_bottom_half * 0.75)
        
        # Draw duck player or fallback to circle
        if self.duck_image:
            duck_size = 100
            duck_scaled = pygame.transform.scale(self.duck_image, (duck_size, duck_size))
            screen.blit(duck_scaled, (marker_x - duck_size // 2, marker_y - duck_size // 2))
        else:
            pygame.draw.circle(screen, (255, 244, 193), (marker_x, marker_y), 20)
            pygame.draw.circle(screen, (176, 129, 46), (marker_x, marker_y), 5)
        
        # Draw grass overlay
        if self.forest_grass_image:
            grass_scaled = pygame.transform.scale(self.forest_grass_image, (WIDTH, int(HEIGHT * 0.15)))
            screen.blit(grass_scaled, (0, HEIGHT - int(HEIGHT * 0.15)))
        
        # Draw hearts HUD (lives indicator)
        heart_size = 50
        for i in range(3):
            heart_x = 30 + i * 70
            heart_y = 30
            if self.heart_images[2]:  # Always use heart3
                heart_img = pygame.transform.scale(self.heart_images[2], (heart_size, heart_size))
                screen.blit(heart_img, (heart_x, heart_y))
        
        # Draw distance progress text
        distance_text = font.render(f"Distance: {int(self.forest_distance)}m", True, (60, 40, 20))
        screen.blit(distance_text, (WIDTH - 300, 30))

    def draw_dodge_scene(self, shake_x, shake_y):
        """Render the dodge and collect minigame for Chapter 2."""
        # Draw background image if available
        if self.chapter1_background_image:
            bg_scaled = pygame.transform.scale(self.chapter1_background_image, (WIDTH, HEIGHT))
            screen.blit(bg_scaled, (0, 0))
        else:
            # Fallback to forest-like background
            if self.forest_sky_image:
                sky_scaled = pygame.transform.scale(self.forest_sky_image, (WIDTH, int(HEIGHT * 0.5)))
                screen.blit(sky_scaled, (0, 0))
            else:
                pygame.draw.rect(screen, (162, 212, 242), pygame.Rect(0, 0, WIDTH, int(HEIGHT * 0.5)))
            
            # Draw ground
            pygame.draw.rect(screen, (54, 88, 43), pygame.Rect(0, int(HEIGHT * 0.5), WIDTH, int(HEIGHT * 0.5)))
        
        # Draw obstacles (logs and rocks)
        for obstacle in self.dodge_obstacles:
            obstacle_x = int(obstacle['x'])
            obstacle_y = int(obstacle['y'])
            
            if obstacle['type'] == 'log' and self.log_images[obstacle['variant']]:
                img = self.log_images[obstacle['variant']]
                img_scaled = pygame.transform.scale(img, (obstacle['width'], obstacle['height']))
                screen.blit(img_scaled, (obstacle_x - obstacle['width'] // 2, obstacle_y - obstacle['height'] // 2))
            elif obstacle['type'] == 'rock' and self.rock_images[obstacle['variant']]:
                img = self.rock_images[obstacle['variant']]
                img_scaled = pygame.transform.scale(img, (obstacle['width'], obstacle['height']))
                screen.blit(img_scaled, (obstacle_x - obstacle['width'] // 2, obstacle_y - obstacle['height'] // 2))
            else:
                # Fallback circle
                color = (139, 69, 19) if obstacle['type'] == 'log' else (128, 128, 128)
                pygame.draw.circle(screen, color, (obstacle_x, obstacle_y), obstacle['width'] // 2)
        
        # Draw collectibles (nature elements)
        for collectible in self.dodge_collectibles:
            collectible_x = int(collectible['x'])
            collectible_y = int(collectible['y'])
            
            if self.nature_element_image:
                img_scaled = pygame.transform.scale(self.nature_element_image, (collectible['size'], collectible['size']))
                screen.blit(img_scaled, (collectible_x - collectible['size'] // 2, collectible_y - collectible['size'] // 2))
            else:
                # Fallback star
                pygame.draw.circle(screen, (255, 215, 0), (collectible_x, collectible_y), collectible['size'] // 2)
        
        # Draw player (duck)
        marker_x = self.player_x + shake_x
        marker_y = self.player_y + shake_y
        
        if self.duck_image:
            duck_scaled = pygame.transform.scale(self.duck_image, (220, 220))  # Increased from 180
            screen.blit(duck_scaled, (marker_x - 110, marker_y - 110))
        else:
            pygame.draw.circle(screen, (255, 244, 193), (marker_x, marker_y), 55)  # Increased from 45
        
        # Draw HUD hearts: full lives use heart1, lost lives use heart3 (broken)
        heart_size = 64
        heart_y = 16
        for i in range(3):
            heart_x = 20 + i * 72
            is_full_heart = i < self.lives
            heart_img_src = self.heart_images[0] if is_full_heart else self.heart_images[2]

            if heart_img_src:
                heart_img = pygame.transform.scale(heart_img_src, (heart_size, heart_size))
                screen.blit(heart_img, (heart_x, heart_y))
            else:
                color = (220, 40, 40) if is_full_heart else (100, 100, 100)
                pygame.draw.circle(screen, color, (heart_x + heart_size // 2, heart_y + heart_size // 2), heart_size // 2)
        
        # Draw collected count and time
        puzzle_cfg = scenes.get(self.current_scene, {}).get('puzzle', {})
        required_orbs = puzzle_cfg.get('required_score', 15)
        collected_text = font_large.render(f"Orbs: {self.collectibles_collected}/{required_orbs}", True, (60, 40, 20))
        screen.blit(collected_text, (20, 100))
        
        time_text = font.render(f"Time: {max(0, int(self.time_remaining))}s", True, (60, 40, 20))
        screen.blit(time_text, (20, 150))

    def draw_star(self, surface, center_x, center_y, size, color, outline_color=None, outline_width=3):
        """Draw a 5-pointed star"""
        import math
        points = []
        for i in range(10):
            angle = math.pi / 2 + (i * math.pi / 5)
            if i % 2 == 0:
                radius = size
            else:
                radius = size * 0.4
            x = center_x + radius * math.cos(angle)
            y = center_y - radius * math.sin(angle)
            points.append((x, y))
        
        # Draw filled star
        pygame.draw.polygon(surface, color, points)
        
        # Draw outline if specified
        if outline_color:
            pygame.draw.polygon(surface, outline_color, points, outline_width)

    def spawn_dodge_collectible(self):
        """Spawn a collectible nature element"""
        collectible_x = random.randint(60, WIDTH - 60)
        collectible_y = -30
        
        self.dodge_collectibles.append({
            'x': collectible_x,
            'y': collectible_y,
            'size': 100,
            'speed': random.uniform(320, 500)
        })

    def spawn_dodge_obstacle(self):
        """Spawn an obstacle (log or rock) for dodge_and_collect game"""
        obstacle_x = random.randint(40, WIDTH - 40)
        obstacle_y = -30
        obstacle_type = random.choice(['log', 'rock'])
        variant = 0 if obstacle_type == 'log' else random.randint(0, 1)  # log1 or rock1/rock2
        
        self.dodge_obstacles.append({
            'x': obstacle_x,
            'y': obstacle_y,
            'width': 130,  # Increased from 100
            'height': 130,  # Increased from 100
            'speed': random.uniform(380, 620),
            'type': obstacle_type,
            'variant': variant
        })



    def finish_completion_animation(self):
        self.completion_anim_active = False
        self.completion_anim_time = 0.0
        action = self.completion_anim_action
        reward = self.completion_anim_reward
        self.completion_anim_action = None
        self.completion_anim_reward = None

        if reward:
            self.collected_elements.add(reward)

        if action == 'chapter_complete':
            self.chapter_complete = True
            # Auto-advance to next chapter intro
            current_scene = self.current_scene
            if current_scene == 'chapter1':
                self.current_scene = 'chapter2_intro'
                self.load_ui()
            elif current_scene == 'chapter2':
                self.current_scene = 'chapter3_intro'
                self.load_ui()
            elif current_scene == 'chapter3':
                self.current_scene = 'chapter4_intro'
                self.load_ui()
            elif current_scene == 'chapter4':
                self.current_scene = 'final_intro'
                self.load_ui()
        elif action == 'victory':
            self.current_scene = 'victory'
            self.load_ui()

    def get_next_chapter_scene(self):
        scene_order = {
            'chapter1': 'chapter2_intro',
            'chapter2': 'chapter3_intro',
            'chapter3': 'chapter4_intro',
            'chapter4': 'final_intro',
            'final': 'victory',
        }
        return scene_order.get(self.current_scene)

    def skip_current_chapter_game(self):
        scene = scenes.get(self.current_scene, {})
        if scene.get('type') not in ['action', 'puzzle']:
            return False

        next_scene = self.get_next_chapter_scene()
        if not next_scene:
            return False

        reward = scene.get('puzzle', {}).get('reward')
        if reward and reward != 'victory':
            self.collected_elements.add(reward)

        self.chapter_complete = True
        self.current_scene = next_scene
        self.load_ui()
        return True

    def get_scene_choice_next(self, scene):
        choices = scene.get('choices', [])
        next_scene = None
        if isinstance(choices, list) and choices:
            first_choice = choices[0]
            if isinstance(first_choice, dict):
                next_scene = first_choice.get('next')
        elif isinstance(choices, dict):
            next_scene = choices.get('next')
        return next_scene

    def skip_current_script(self):
        scene = scenes.get(self.current_scene, {})
        if scene.get('type') != 'story':
            return False

        next_scene = self.get_scene_choice_next(scene)
        if not next_scene:
            return False

        if next_scene == 'quit':
            self.running = False
        else:
            self.current_scene = next_scene
            self.load_ui()
        return True

    def find_piece_image_path(self, piece_id):
        filename_candidates = [f'{piece_id}.png', f'piece_{piece_id}.png']

        piece_id_str = str(piece_id)
        trailing_number = re.search(r'(\d+)$', piece_id_str)
        if trailing_number:
            filename_candidates.append(f'piece_{trailing_number.group(1)}.png')

        for filename in filename_candidates:
            candidate = os.path.join(BASE_DIR, 'assets', 'puzzle_pieces', filename)
            if os.path.exists(candidate):
                return candidate

        for filename in filename_candidates:
            nested_matches = glob.glob(
                os.path.join(BASE_DIR, 'assets', '**', 'puzzle_pieces', filename),
                recursive=True,
            )
            if nested_matches:
                return nested_matches[0]

        return None

    def find_asset_path(self, asset_name):
        candidate = os.path.join(BASE_DIR, 'assets', asset_name)
        if os.path.exists(candidate):
            return candidate
        nested_matches = glob.glob(os.path.join(BASE_DIR, 'assets', '**', asset_name), recursive=True)
        return nested_matches[0] if nested_matches else None

    def load_memory_card_images(self, puzzle):
        self.memory_card_images = {}
        card_glob = puzzle.get('card_glob')
        if not card_glob:
            return
        if not os.path.isabs(card_glob):
            card_glob = os.path.join(BASE_DIR, card_glob)
        card_paths = sorted(glob.glob(card_glob))
        for idx, card_path in enumerate(card_paths):
            try:
                self.memory_card_images[idx] = pygame.image.load(card_path).convert_alpha()
            except Exception:
                continue

    def resize_image(self, image, width, height):
        if width <= 0 or height <= 0:
            return image
        original_w, original_h = image.get_size()
        target_aspect = original_w / original_h
        desired_aspect = width / height
        if desired_aspect > target_aspect:
            scaled_height = height
            scaled_width = int(target_aspect * scaled_height)
        else:
            scaled_width = width
            scaled_height = int(scaled_width / target_aspect)
        return pygame.transform.smoothscale(image, (scaled_width, scaled_height))

    def wrap_text(self, text, font_obj, max_width):
        lines = []
        for paragraph in text.split('\n'):
            words = paragraph.split()
            if not words:
                continue

            current_line = []
            for word in words:
                test_line = ' '.join(current_line + [word])
                if font_obj.size(test_line)[0] <= max_width:
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                    current_line = [word]

            else:
                if current_line:
                    lines.append(' '.join(current_line))
        return lines

    def get_memory_layout(self):
        card_count = len(self.memory_cards)
        if card_count <= 0:
            return 120, 160, 4, 0, 0, 15

        area_x = 60
        area_y = 130
        area_w = WIDTH - 120
        area_h = HEIGHT - 200
        gap = 10
        ratio = 120 / 160.0

        best = None
        for cols in range(4, min(card_count, 14) + 1):
            rows = int(math.ceil(card_count / float(cols)))
            max_w = (area_w - (cols - 1) * gap) // cols
            max_h = (area_h - (rows - 1) * gap) // rows
            if max_w <= 0 or max_h <= 0:
                continue

            card_w = min(max_w, int(max_h * ratio))
            card_h = int(card_w / ratio)
            if card_w < 24 or card_h < 32:
                continue

            area = card_w * card_h
            if best is None or area > best[0]:
                best = (area, card_w, card_h, cols, rows, gap)

        if best is None:
            card_w, card_h, cols, rows, gap = 60, 80, 8, int(math.ceil(card_count / 8.0)), 8
        else:
            _, card_w, card_h, cols, rows, gap = best

        grid_w = cols * card_w + (cols - 1) * gap
        grid_h = rows * card_h + (rows - 1) * gap
        start_x = area_x + max(0, (area_w - grid_w) // 2)
        start_y = area_y + max(0, (area_h - grid_h) // 2)
        return card_w, card_h, cols, start_x, start_y, gap

    def split_story_chapter_text(self, scene):
        full_text = scene.get('text', '')
        chapter_title = None

        if scene.get('type') == 'story' and 'chapter' in scene:
            raw_lines = full_text.split('\n')
            first_non_empty_idx = None
            for idx, line in enumerate(raw_lines):
                if line.strip():
                    first_non_empty_idx = idx
                    break

            if first_non_empty_idx is not None:
                first_line = raw_lines[first_non_empty_idx].strip()
                if first_line.startswith('~') and first_line.endswith('~') and len(first_line) > 1:
                    first_line = first_line[1:-1].strip()
                chapter_title = first_line

                remainder = '\n'.join(raw_lines[first_non_empty_idx + 1:]).strip()
                if remainder:
                    full_text = remainder

        return chapter_title, full_text

    def load_ui(self):
        scene = scenes[self.current_scene]
        self.clear_ui()
        self.pieces = []
        self.drops = []
        self.puzzle_frame_image = None
        self.puzzle_complete_image = None
        self.generated_complete_image = None
        self.generated_complete_rect = None
        self.chapter1_continue_rect = None
        self.current_obstacles = []
        self.forest_obstacles = []
        self.goal_x = None
        self.completion_anim_active = False
        self.completion_anim_time = 0.0
        self.completion_anim_action = None
        self.completion_anim_reward = None
        self.scene_start_time = 0.0
        self.typed_chars = 0
        self.prev_typed_chars = 0
        self.current_sentence_idx = 0
        self.sentence_pause_time = 0.0
        self.show_prompt = False
        self.continue_button_rect = None
        self.skip_button_rect = None
        self.skip_button_action = None
        self.memory_card_images = {}
        self.ttt_player_won = False
        self.ttt_win_continue_rect = None
        self.ttt_trophy_revealed = False
        self.ttt_mark_anims = {}
        self.ttt_ai_delay_timer = 0.0

        if self.current_scene == 'chapter1_intro' and self.chapter1_attempted:
            # Skip description on retry — go straight to the prompt
            self.show_prompt = True

        if self.current_scene == 'chapter1':
            self.chapter_complete = False

        # Reset chapter_complete for all action/puzzle scenes
        if scene.get('type') in ['action', 'puzzle']:
            self.chapter_complete = False

        complete_path = self.find_asset_path('puzzle_complete.png')
        if complete_path:
            try:
                self.puzzle_complete_image = pygame.image.load(complete_path).convert_alpha()
            except Exception:
                self.puzzle_complete_image = None

        if scene.get('type') in ['puzzle', 'action', 'story', 'menu']:
            # Store exit button rect for custom rendering instead of pygame_gui
            self.exit_button_rect = pygame.Rect((WIDTH - 130, 10), (120, 60))

        y_offset = HEIGHT - 150
        # Create choice buttons for main_menu or non-story/menu scenes
        if self.current_scene == 'main_menu':
            # For main menu, store button info for custom drawing, don't use pygame_gui
            self.menu_button_rects = []
            choices = scene.get('choices')
            if not isinstance(choices, list):
                choices = []
            num_choices = len(choices)
            if num_choices > 0:
                button_width = 280
                button_height = 70
                total_width = num_choices * button_width + (num_choices - 1) * 30  # 30px spacing
                start_x = (WIDTH - total_width) // 2  # Center horizontally
                
                for i, choice in enumerate(choices):
                    x_pos = start_x + i * (button_width + 30)
                    button_rect = pygame.Rect(x_pos, y_offset, button_width, button_height)
                    self.menu_button_rects.append((button_rect, choice['next']))
        elif scene.get('type') not in ['story', 'menu']:
            choices = scene.get('choices')
            if not isinstance(choices, list):
                choices = []
            num_choices = len(choices)
            if num_choices > 0:
                button_width = 280
                button_height = 70
                total_width = num_choices * button_width + (num_choices - 1) * 30  # 30px spacing
                start_x = (WIDTH - total_width) // 2  # Center horizontally
                
                for i, choice in enumerate(choices):
                    x_pos = start_x + i * (button_width + 30)
                    button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((x_pos, y_offset), (button_width, button_height)), text=choice['text'], manager=manager)
                    self.ui_elements.append(('choice', button, choice['next']))

        if 'puzzle' in scene:
            puzzle = scene['puzzle']
            piece_scale = float(puzzle.get('piece_scale', 1.0))
            if puzzle['type'] == 'dragdrop':
                self.pieces = [dict(piece) for piece in puzzle['pieces']]
                for piece in self.pieces:
                    piece['size'] = [
                        max(24, int(round(piece['size'][0] * piece_scale))),
                        max(24, int(round(piece['size'][1] * piece_scale))),
                    ]
                    # Apply resolution scaling to coordinates
                    piece['start_pos'] = self.scale_coordinates(piece['start_pos'][:])
                    piece['correct_pos'] = self.scale_coordinates(piece['correct_pos'][:])
                    piece['current_pos'] = piece['start_pos'][:]
                    piece['locked'] = False
                    piece_image_path = self.find_piece_image_path(piece['id'])
                    if piece_image_path:
                        try:
                            piece_img = pygame.image.load(piece_image_path)
                            piece_img = pygame.transform.scale(piece_img, (piece['size'][0], piece['size'][1]))
                            piece['image'] = piece_img
                        except Exception:
                            piece['image'] = None
                    else:
                        piece['image'] = None
            elif puzzle['type'] == 'final_dragdrop':
                self.pieces = [dict(elem) for elem in puzzle['elements']]
                for piece in self.pieces:
                    piece['size'] = [
                        max(24, int(round(piece['size'][0] * piece_scale))),
                        max(24, int(round(piece['size'][1] * piece_scale))),
                    ]
                    # Apply resolution scaling to coordinates
                    piece['start_pos'] = self.scale_coordinates(piece['start_pos'][:])
                    piece['correct_pos'] = self.scale_coordinates(piece['correct_pos'][:])
                    piece['current_pos'] = piece['start_pos'][:]
                    piece['locked'] = False
                    piece_image_path = self.find_piece_image_path(piece['id'])
                    if piece_image_path:
                        try:
                            piece_img = pygame.image.load(piece_image_path)
                            piece_img = pygame.transform.scale(piece_img, (piece['size'][0], piece['size'][1]))
                            piece['image'] = piece_img
                        except Exception:
                            piece['image'] = None
                    else:
                        piece['image'] = None
            elif puzzle['type'] == 'memory_sequence':
                self.symbol_sequence = puzzle.get('sequence', [])
                self.player_sequence = []
                self.attempts_remaining = puzzle.get('attempts', 3)
            elif puzzle['type'] == 'movement':
                self.lives = puzzle.get('lives', 3)
                self.player_x = 100
                self.player_y = HEIGHT // 2
                self.goal_x = puzzle.get('goal_x', WIDTH - 180)
                self.current_obstacles = [pygame.Rect(obs['x'], obs['y'], obs['width'], obs['height']) for obs in puzzle.get('obstacles', [])]
            elif puzzle['type'] == 'forest_run':
                self.lives = puzzle.get('lives', 3)
                self.player_x = 0.0
                self.player_y = 0.0
                self.forest_distance = 0.0
                self.forest_target_distance = float(puzzle.get('distance_goal', 1800))
                self.forest_speed = float(puzzle.get('speed', 340))
                self.forest_spawn_timer = 0.35
                self.forest_obstacles = []
            elif puzzle['type'] == 'catch_drops':
                self.time_remaining = puzzle.get('time_limit', 30)
                self.score = 0
                self.player_x = WIDTH // 2
                self.player_y = HEIGHT - 50
            elif puzzle['type'] == 'card_collection':
                self.time_remaining = puzzle.get('time_limit', 40)
                self.score = 0
                self.player_x = WIDTH // 2
                self.player_y = HEIGHT - 50
            elif puzzle['type'] == 'platform_jump':
                self.lives = puzzle.get('lives', 3)
                self.player_x = 100
                self.player_y = 350
            elif puzzle['type'] == 'memory_pairs':
                self.memory_attempts = puzzle.get('attempts', 3)
                self.memory_matched = 0
                self.memory_flipped = []
                self.memory_mismatch_timer = 0.0
                num_pairs = puzzle.get('pairs', 6)
                self.load_memory_card_images(puzzle)
                use_image_matching = bool(self.memory_card_images) and puzzle.get('match_by_image', True)
                if use_image_matching:
                    image_keys = sorted(self.memory_card_images.keys())
                    pair_values = [image_keys[i % len(image_keys)] for i in range(num_pairs)]
                else:
                    pair_values = list(range(num_pairs))
                cards = pair_values * 2
                random.shuffle(cards)
                self.memory_cards = [
                    {'id': card, 'match_key': card, 'flipped': False, 'matched': False}
                    for card in cards
                ]
            elif puzzle['type'] == 'tictactoe':
                self.tictactoe_board = [None] * 9
                self.tictactoe_player_wins = 0
                self.tictactoe_ai_wins = 0
                self.tictactoe_current_turn = 'player'
                self.ttt_trophy_revealed = False
                self.ttt_trophy_anim_time = 0.0
                self.ttt_mark_anims = {}
                self.ttt_ai_delay_timer = 0.0
            elif puzzle['type'] == 'dodge_and_collect':
                self.lives = puzzle.get('lives', 3)
                self.score = 0
                self.collectibles_collected = 0
                self.time_remaining = puzzle.get('time_limit', 60)
                self.player_x = WIDTH // 2
                self.player_y = HEIGHT - 80
                self.dodge_obstacles = []
                self.dodge_collectibles = []
                self.dodge_spawn_timer = 0.6
            elif puzzle['type'] == 'element_ascension':
                self.ascension_elements = ['element_earth', 'element_nature', 'element_water', 'element_fire']
                self.ascension_time = 0.0
                self.final_trophy_active = True
                self.final_trophy_revealed = False
                self.final_trophy_anim_time = 0.0
                self.final_trophy_continue_rect = None
                self.current_sentence_idx = 0
                self.typed_chars = 0
                self.sentence_pause_time = 0.0
                self.scene_start_time = 0.0
                self.show_prompt = False

            frame_path = self.find_asset_path('puzzle_frame.png')
            if frame_path and puzzle['type'] in ['dragdrop', 'final_dragdrop']:
                try:
                    frame_img = pygame.image.load(frame_path).convert_alpha()
                    if self.pieces:
                        min_x = min(piece['correct_pos'][0] for piece in self.pieces)
                        min_y = min(piece['correct_pos'][1] for piece in self.pieces)
                        max_x = max(piece['correct_pos'][0] + piece['size'][0] for piece in self.pieces)
                        max_y = max(piece['correct_pos'][1] + piece['size'][1] for piece in self.pieces)
                        frame_scale = scene.get('puzzle', {}).get('frame_scale', 1.0)
                        target_w = int((max_x - min_x + 20) * frame_scale)
                        target_h = int((max_y - min_y + 20) * frame_scale)
                    else:
                        target_w = WIDTH - 100
                        target_h = HEIGHT - 200
                    max_frame_w = WIDTH - 20
                    max_frame_h = HEIGHT - 40
                    aspect = frame_img.get_width() / frame_img.get_height()
                    if target_w > max_frame_w:
                        target_w = max_frame_w
                        target_h = int(target_w / aspect)
                    if target_h > max_frame_h:
                        target_h = max_frame_h
                        target_w = int(target_h * aspect)
                    self.puzzle_frame_image = self.resize_image(frame_img, target_w, target_h)
                except Exception:
                    self.puzzle_frame_image = None

    def draw_scene(self):
        scene = scenes[self.current_scene]
        scene_type = scene.get('type', 'story')
        self.skip_button_rect = None
        self.skip_button_action = None
        shake_x = 0
        shake_y = 0
        fade_alpha = 0

        if self.completion_anim_active:
            shake_duration, fade_duration = self.get_completion_durations()
            if shake_duration > 0 and self.completion_anim_time < shake_duration:
                shake_strength = int(12 * (1.0 - (self.completion_anim_time / shake_duration)))
                shake_x = random.randint(-shake_strength, shake_strength)
                shake_y = random.randint(-shake_strength, shake_strength)
            else:
                fade_progress = (self.completion_anim_time - shake_duration) / fade_duration
                fade_progress = max(0.0, min(1.0, fade_progress))
                fade_alpha = int(255 * fade_progress)

        if scene_type == 'menu':
            # Display quacklands banner fullscreen
            banner_path = self.find_asset_path('quacklands_banner.png')
            if banner_path:
                try:
                    banner_img = pygame.image.load(banner_path)
                    banner_img = pygame.transform.scale(banner_img, (WIDTH, HEIGHT))
                    screen.blit(banner_img, (0, 0))
                except Exception:
                    # Fallback to text if image fails
                    title = font_title.render(scene.get('title', 'Legend of the First Flock'), True, GOLD)
                    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 80))
            else:
                title = font_title.render(scene.get('title', 'Legend of the First Flock'), True, GOLD)
                screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 80))
            
            # Draw custom menu buttons with orange borders and pastel yellow fill
            scene_choices = scene.get('choices')
            if not isinstance(scene_choices, list):
                scene_choices = []
            for i, (button_rect, next_scene) in enumerate(self.menu_button_rects):
                # Draw light yellow background
                pygame.draw.rect(screen, (220, 220, 100), button_rect, border_radius=12)
                # Draw orange border
                pygame.draw.rect(screen, (255, 165, 0), button_rect, 3, border_radius=12)
                
                # Draw orange text
                button_text = scene_choices[i]['text'] if i < len(scene_choices) else 'Button'
                btn_text_surf = font.render(button_text, True, (60, 40, 20))
                text_rect = btn_text_surf.get_rect(center=button_rect.center)
                screen.blit(btn_text_surf, text_rect)

        elif scene_type == 'story':
            # Draw background image if available
            if self.chapter1_background_image:
                bg_scaled = pygame.transform.scale(self.chapter1_background_image, (WIDTH, HEIGHT))
                screen.blit(bg_scaled, (0, 0))
            else:
                # Fallback to nature-like background (forest green)
                pygame.draw.rect(screen, (100, 150, 80), pygame.Rect(0, 0, WIDTH, HEIGHT))

            chapter_title, full_text = self.split_story_chapter_text(scene)
            chapter_intro_total = self.chapter_title_hold_duration + self.chapter_title_fade_duration
            show_chapter_title = (
                chapter_title is not None
                and self.current_sentence_idx == 0
                and not self.show_prompt
                and self.scene_start_time < chapter_intro_total
            )

            start_y_offset = 50

            if show_chapter_title:
                title_surface = font_chapter.render(chapter_title, True, (60, 40, 20))
                if self.scene_start_time > self.chapter_title_hold_duration:
                    fade_t = (self.scene_start_time - self.chapter_title_hold_duration) / self.chapter_title_fade_duration
                    fade_t = max(0.0, min(1.0, fade_t))
                    title_alpha = int(255 * (1.0 - fade_t))
                else:
                    title_alpha = 255
                title_surface.set_alpha(title_alpha)
                screen.blit(
                    title_surface,
                    (
                        WIDTH // 2 - title_surface.get_width() // 2,
                        HEIGHT // 2 - title_surface.get_height() // 2 - 120,
                    ),
                )

            # Split by periods and remove empty sentences
            sentences = [s.strip() + '.' for s in full_text.split('.') if s.strip()]
            if len(sentences) > 1:
                sentences = sentences[:-1]
            
            # Get current sentence being displayed
            if self.current_sentence_idx < len(sentences):
                current_sentence = sentences[self.current_sentence_idx]
                displayed_text = '' if show_chapter_title else current_sentence[:self.typed_chars]
            else:
                displayed_text = ""
            
            wrapped_text = self.wrap_text(displayed_text, font_large, WIDTH - 200)
            
            # Calculate total height to center vertically
            line_height = 65
            total_height = len(wrapped_text) * line_height
            start_y = (HEIGHT - 150 - total_height) // 2 + start_y_offset
            
            # Apply fade effect to all text (new sentence appearing)
            fade_progress = min(1.0, (self.scene_start_time - 0.1) / 0.5)
            fade_alpha = int(255 * fade_progress)
            
            for line in wrapped_text:
                text_surf = font_large.render(line, True, (60, 40, 20))  # Dark brown text
                text_surf.set_alpha(fade_alpha)
                screen.blit(text_surf, (WIDTH // 2 - text_surf.get_width() // 2, start_y))
                start_y += line_height
            
            # Show prompt and button if ready
            if self.show_prompt:
                prompt_message = scene.get('prompt', 'Would you like to continue?')
                prompt_text = font_large.render(prompt_message, True, (60, 40, 20))  # Dark brown text
                prompt_y = start_y + 80
                screen.blit(prompt_text, (WIDTH // 2 - prompt_text.get_width() // 2, prompt_y))
                
                # Draw continue button as a star at bottom center
                star_x = WIDTH // 2
                star_y = HEIGHT - 200
                star_size = 70
                
                # Create circular hitbox around star for click detection
                self.continue_button_rect = pygame.Rect(star_x - star_size, star_y - star_size, star_size * 2, star_size * 2)
                
                # Draw the star button with image or fallback to drawn star
                if self.star_button_image:
                    star_scaled = pygame.transform.scale(self.star_button_image, (star_size * 2, star_size * 2))
                    screen.blit(star_scaled, (star_x - star_size, star_y - star_size))
                else:
                    self.draw_star(screen, star_x, star_y, star_size, (220, 220, 100), (255, 165, 0), 4)

            
            image_path = scene.get('image', '')
            if image_path and not os.path.isabs(image_path):
                image_path = os.path.join(BASE_DIR, image_path)
            if image_path and os.path.exists(image_path):
                try:
                    image = pygame.image.load(image_path)
                    image = pygame.transform.scale(image, (400, 300))
                    screen.blit(image, (WIDTH // 2 - 200, start_y + 30))
                except Exception:
                    pass

            next_scene = self.get_scene_choice_next(scene)
            if next_scene:
                skip_w = 250
                skip_h = 56
                skip_x = WIDTH - skip_w - 24
                skip_y = HEIGHT - skip_h - 24
                self.skip_button_rect = pygame.Rect(skip_x, skip_y, skip_w, skip_h)
                self.skip_button_action = 'script'
                pygame.draw.rect(screen, (220, 220, 100), self.skip_button_rect, border_radius=10)
                pygame.draw.rect(screen, (255, 165, 0), self.skip_button_rect, 3, border_radius=10)
                skip_text = font.render('Skip Script', True, (60, 40, 20))
                screen.blit(
                    skip_text,
                    (
                        self.skip_button_rect.centerx - skip_text.get_width() // 2,
                        self.skip_button_rect.centery - skip_text.get_height() // 2,
                    ),
                )
        elif scene_type in ['puzzle', 'action']:
            puzzle_type = scene.get('puzzle', {}).get('type')
            show_action_text = not (self.current_scene == 'chapter2' and puzzle_type == 'dragdrop')
            if show_action_text:
                if 'chapter' in scene:
                    chapter_text = font.render(f"Chapter {scene['chapter']}", True, (60, 40, 20))  # Dark brown
                    screen.blit(chapter_text, (50, 20))
                wrapped_text = self.wrap_text(scene['text'], font_small, WIDTH - 250)
                y = 60
                for line in wrapped_text:
                    text_surf = font_small.render(line, True, (60, 40, 20))
                    screen.blit(text_surf, (50, y))
                    y += 25

            if puzzle_type == 'forest_run':
                self.draw_forest_run_scene(shake_x, shake_y)
            elif puzzle_type == 'dodge_and_collect':
                self.draw_dodge_scene(shake_x, shake_y)


            if puzzle_type not in ['forest_run', 'dodge_and_collect', 'dragdrop', 'final_dragdrop'] and self.lives > 0 and not (self.current_scene == 'chapter3' and puzzle_type == 'memory_pairs'):
                lives_text = font_small.render(f'Lives: {self.lives}', True, RED)
                screen.blit(lives_text, (WIDTH - 200, 60))
            if self.current_scene == 'chapter3' and puzzle_type == 'memory_pairs':
                attempts_text = font_small.render(f'Attempts: {self.memory_attempts}', True, RED)
                screen.blit(attempts_text, (WIDTH - 240, 60))
            if puzzle_type not in ['forest_run', 'dodge_and_collect'] and self.score > 0:
                score_text = font_small.render(f'Score: {self.score}', True, GREEN)
                screen.blit(score_text, (WIDTH - 200, 100))
            if puzzle_type == 'forest_run' and self.forest_target_distance > 0:
                distance_left = max(0, int(self.forest_target_distance - self.forest_distance))
                distance_text = font_small.render(f'Distance: {distance_left}m', True, (60, 40, 20))
                screen.blit(distance_text, (WIDTH - 230, 180))

            frame_rect = None
            if self.puzzle_frame_image and puzzle_type in ['dragdrop', 'final_dragdrop']:
                frame_rect = self.puzzle_frame_image.get_rect()
                frame_rect.center = (WIDTH // 2 + shake_x, HEIGHT // 2 + shake_y)
                screen.blit(self.puzzle_frame_image, frame_rect)

            complete_source_image = self.puzzle_complete_image or self.generated_complete_image
            complete_target_rect = frame_rect
            if complete_target_rect is None and self.generated_complete_rect is not None:
                complete_target_rect = self.generated_complete_rect.move(shake_x, shake_y)

            show_completed_puzzle = (
                puzzle_type == 'dragdrop'
                and self.chapter_complete
                and not self.completion_anim_active
                and complete_source_image is not None
                and complete_target_rect is not None
            )

            if not show_completed_puzzle:
                for piece in self.pieces:
                    rect = pygame.Rect(piece['current_pos'][0] + shake_x, piece['current_pos'][1] + shake_y, piece['size'][0], piece['size'][1])
                    if piece.get('locked') or self.is_piece_aligned(piece):
                        if self.lock_glow_image:
                            glow_w = piece['size'][0] + 26
                            glow_h = piece['size'][1] + 26
                            glow_img = pygame.transform.smoothscale(self.lock_glow_image, (glow_w, glow_h))
                            screen.blit(glow_img, (rect.x - 13, rect.y - 13))
                        else:
                            glow_surface = pygame.Surface((piece['size'][0] + 20, piece['size'][1] + 20), pygame.SRCALPHA)
                            pygame.draw.rect(glow_surface, (255, 215, 0, 85), glow_surface.get_rect(), border_radius=12)
                            screen.blit(glow_surface, (rect.x - 10, rect.y - 10))
                    if piece.get('image'):
                        screen.blit(piece['image'], (rect.x, rect.y))
                    else:
                        pygame.draw.rect(screen, (120, 100, 80), rect)
                        pygame.draw.rect(screen, BLACK, rect, 2)

            if show_completed_puzzle:
                if self.puzzle_complete_image is not None and frame_rect is not None:
                    complete_image = pygame.transform.smoothscale(self.puzzle_complete_image, (frame_rect.width, frame_rect.height))
                else:
                    complete_image = complete_source_image
                self.draw_scaled_aura(complete_target_rect)
                screen.blit(complete_image, complete_target_rect)

            for i, symbol in enumerate(self.symbol_sequence):
                pos = [(200, 250), (400, 250), (200, 400), (400, 400)][symbol]
                pos = (pos[0] + shake_x, pos[1] + shake_y)
                pygame.draw.circle(screen, GOLD, pos, 40)
                symbol_text = font_large.render(['1', '2', '3', '4'][symbol], True, (60, 40, 20))
                screen.blit(symbol_text, (pos[0] - 20, pos[1] - 20))

            if puzzle_type == 'memory_pairs':
                card_w, card_h, cards_per_row, start_x, start_y, card_gap = self.get_memory_layout()
                for idx, card in enumerate(self.memory_cards):
                    row = idx // cards_per_row
                    col = idx % cards_per_row
                    x = start_x + col * (card_w + card_gap) + shake_x
                    y = start_y + row * (card_h + card_gap) + shake_y
                    card_rect = pygame.Rect(x, y, card_w, card_h)
                    flip_value = max(0.0, min(1.0, card.get('flip_value', 0.0)))
                    show_front = flip_value >= 0.5
                    width_factor = max(0.05, abs(2.0 * flip_value - 1.0))
                    draw_w = max(6, int(card_w * width_factor))
                    draw_rect = pygame.Rect(0, 0, draw_w, card_h)
                    draw_rect.center = card_rect.center

                    card_surface = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
                    if show_front:
                        if card['matched']:
                            pygame.draw.rect(card_surface, (100, 100, 100), card_surface.get_rect(), border_radius=8)
                            pygame.draw.rect(card_surface, (50, 50, 50), card_surface.get_rect(), 2, border_radius=8)
                        else:
                            pygame.draw.rect(card_surface, (100, 200, 255), card_surface.get_rect(), border_radius=8)
                            pygame.draw.rect(card_surface, BLUE, card_surface.get_rect(), 3, border_radius=8)

                        card_img = self.memory_card_images.get(card['id'])
                        if card_img is None and self.memory_card_images:
                            image_keys = sorted(self.memory_card_images.keys())
                            card_img = self.memory_card_images.get(image_keys[card['id'] % len(image_keys)])
                        if card_img is not None:
                            img = pygame.transform.smoothscale(card_img, (card_w - 12, card_h - 12))
                            card_surface.blit(img, (6, 6))
                        else:
                            num_text = font_large.render(str(card['id'] + 1), True, (60, 40, 20))
                            card_surface.blit(num_text, (card_w // 2 - 15, card_h // 2 - 15))
                    else:
                        pygame.draw.rect(card_surface, (200, 200, 200), card_surface.get_rect(), border_radius=8)
                        pygame.draw.rect(card_surface, (100, 100, 100), card_surface.get_rect(), 3, border_radius=8)

                    scaled = pygame.transform.smoothscale(card_surface, (draw_rect.width, draw_rect.height))
                    screen.blit(scaled, draw_rect.topleft)

            if puzzle_type == 'tictactoe':
                wins_needed = int(scene.get('puzzle', {}).get('wins_needed', 3))
                if self.ttt_player_won:
                    self.ttt_win_continue_rect = None
                    if self.chapter1_background_image:
                        bg_scaled = pygame.transform.scale(self.chapter1_background_image, (WIDTH, HEIGHT))
                        screen.blit(bg_scaled, (0, 0))
                    else:
                        pygame.draw.rect(screen, (100, 150, 80), pygame.Rect(0, 0, WIDTH, HEIGHT))

                    victory_sentences = [
                        "Congratulations! You earned a trophy for saving the flock's land.",
                        "Peace will now be restored to Quacklands.",
                        "Through steadfast courage and wisdom, you silenced the temple guardian.",
                        "The ancient powers awaken, and the First Flock honors your name.",
                    ]
                    if not self.ttt_trophy_revealed:
                        displayed_text = ''
                        if self.current_sentence_idx < len(victory_sentences):
                            current_sentence = victory_sentences[self.current_sentence_idx]
                            displayed_text = current_sentence[:self.typed_chars]

                        wrapped_text = self.wrap_text(displayed_text, font_large, WIDTH - 200)
                        line_height = 65
                        total_height = len(wrapped_text) * line_height
                        start_y = (HEIGHT - 150 - total_height) // 2 + 40

                        fade_progress = min(1.0, (self.scene_start_time - 0.1) / 0.5)
                        text_alpha = int(255 * fade_progress)
                        for line in wrapped_text:
                            text_surf = font_large.render(line, True, (60, 40, 20))
                            text_surf.set_alpha(text_alpha)
                            screen.blit(text_surf, (WIDTH // 2 - text_surf.get_width() // 2, start_y))
                            start_y += line_height

                    if self.ttt_trophy_revealed:
                        trophy_w = 300
                        trophy_h = int(trophy_w * 1262 / 1130)
                        _TROPHY_ANIM_DUR = 0.5
                        _t = min(1.0, self.ttt_trophy_anim_time / _TROPHY_ANIM_DUR)
                        if _t < 0.75:
                            _anim_scale = (_t / 0.75) ** 0.55
                        else:
                            _tp = (_t - 0.75) / 0.25
                            _anim_scale = 1.0 + 0.14 * math.sin(_tp * math.pi)
                        draw_w = max(4, int(trophy_w * _anim_scale))
                        draw_h = max(4, int(trophy_h * _anim_scale))
                        trophy_rect = pygame.Rect(
                            WIDTH // 2 - draw_w // 2,
                            HEIGHT // 2 - draw_h // 2 - 170,
                            draw_w, draw_h,
                        )
                        self.draw_scaled_aura(trophy_rect)
                        if self.ttt_trophy_image:
                            trophy_scaled = pygame.transform.smoothscale(self.ttt_trophy_image, (draw_w, draw_h))
                            screen.blit(trophy_scaled, trophy_rect.topleft)

                    if self.show_prompt:
                        btn_w, btn_h = 360, 54
                        btn_rect = pygame.Rect(WIDTH // 2 - btn_w // 2, HEIGHT - 110, btn_w, btn_h)
                        self.ttt_win_continue_rect = btn_rect
                        pygame.draw.rect(screen, (220, 220, 100), btn_rect, border_radius=12)
                        pygame.draw.rect(screen, (255, 165, 0), btn_rect, 3, border_radius=12)
                        btn_text = font_small.render('Return to Menu', True, (60, 40, 20))
                        screen.blit(btn_text, (btn_rect.centerx - btn_text.get_width() // 2, btn_rect.centery - btn_text.get_height() // 2))
                else:
                    # Draw board texture
                    board_size = 560
                    cell_size = board_size // 3
                    board_x = (WIDTH - board_size) // 2 + shake_x
                    board_y = (HEIGHT - board_size) // 2 + shake_y
                    if self.ttt_board_image:
                        board_img = pygame.transform.smoothscale(self.ttt_board_image, (board_size, board_size))
                        screen.blit(board_img, (board_x, board_y))
                    else:
                        pygame.draw.rect(screen, BLACK, (board_x, board_y, board_size, board_size), 3)
                        for i in range(1, 3):
                            pygame.draw.line(screen, BLACK, (board_x + i * cell_size, board_y), (board_x + i * cell_size, board_y + board_size), 2)
                            pygame.draw.line(screen, BLACK, (board_x, board_y + i * cell_size), (board_x + board_size, board_y + i * cell_size), 2)
                    # Draw marks with pop-in animation (scale from 0 → 1 with a small overshoot bounce)
                    _ANIM_DUR = 0.22
                    mark_size = int(cell_size * 0.78)
                    for idx, cell in enumerate(self.tictactoe_board):
                        row = idx // 3
                        col = idx % 3
                        cx = board_x + col * cell_size + cell_size // 2
                        cy = board_y + row * cell_size + cell_size // 2
                        _t = min(1.0, self.ttt_mark_anims.get(idx, _ANIM_DUR) / _ANIM_DUR)
                        # Ease-out with a small bounce overshoot
                        if _t < 0.75:
                            _anim_scale = (_t / 0.75) ** 0.55
                        else:
                            _tp = (_t - 0.75) / 0.25
                            _anim_scale = 1.0 + 0.14 * math.sin(_tp * math.pi)
                        _draw_size = max(4, int(mark_size * _anim_scale))
                        if cell == 'X':
                            if self.ttt_player_mark_image:
                                mark_img = pygame.transform.smoothscale(self.ttt_player_mark_image, (_draw_size, _draw_size))
                                screen.blit(mark_img, (cx - _draw_size // 2, cy - _draw_size // 2))
                            else:
                                pygame.draw.line(screen, RED, (cx - 40, cy - 40), (cx + 40, cy + 40), 4)
                                pygame.draw.line(screen, RED, (cx + 40, cy - 40), (cx - 40, cy + 40), 4)
                        elif cell == 'O':
                            if self.ttt_enemy_mark_image:
                                mark_img = pygame.transform.smoothscale(self.ttt_enemy_mark_image, (_draw_size, _draw_size))
                                screen.blit(mark_img, (cx - _draw_size // 2, cy - _draw_size // 2))
                            else:
                                pygame.draw.circle(screen, BLUE, (cx, cy), 40, 4)
                    status_text = f"Your Wins: {self.tictactoe_player_wins}/{wins_needed} | AI Wins: {self.tictactoe_ai_wins}/{wins_needed}"
                    status_surf = font_small.render(status_text, True, (60, 40, 20))
                    screen.blit(status_surf, (WIDTH // 2 - status_surf.get_width() // 2, 30))

            if puzzle_type == 'element_ascension':
                if self.chapter1_background_image:
                    bg_scaled = pygame.transform.scale(self.chapter1_background_image, (WIDTH, HEIGHT))
                    screen.blit(bg_scaled, (0, 0))
                final_sentences = [
                    "You have done the impossible.",
                    "The four sacred forces — Earth, Nature, Water, and Fire — are restored.",
                    "Peace and balance return to Quacklands at last.",
                    "The First Flock honors your courage, forever.",
                ]
                if not self.final_trophy_revealed:
                    displayed_text = ''
                    if self.current_sentence_idx < len(final_sentences):
                        displayed_text = final_sentences[self.current_sentence_idx][:self.typed_chars]
                    wrapped_text = self.wrap_text(displayed_text, font_large, WIDTH - 200)
                    line_height = 65
                    total_height = len(wrapped_text) * line_height
                    start_y = (HEIGHT - 150 - total_height) // 2 + 40
                    fade_progress = min(1.0, (self.scene_start_time - 0.1) / 0.5)
                    text_alpha = int(255 * fade_progress)
                    for line in wrapped_text:
                        text_surf = font_large.render(line, True, (60, 40, 20))
                        text_surf.set_alpha(text_alpha)
                        screen.blit(text_surf, (WIDTH // 2 - text_surf.get_width() // 2, start_y))
                        start_y += line_height
                if self.final_trophy_revealed:
                    trophy_w = 300
                    trophy_h = int(trophy_w * 1262 / 1130)
                    _TROPHY_ANIM_DUR = 0.5
                    _t = min(1.0, self.final_trophy_anim_time / _TROPHY_ANIM_DUR)
                    if _t < 0.75:
                        _anim_scale = (_t / 0.75) ** 0.55
                    else:
                        _tp = (_t - 0.75) / 0.25
                        _anim_scale = 1.0 + 0.14 * math.sin(_tp * math.pi)
                    draw_w = max(4, int(trophy_w * _anim_scale))
                    draw_h = max(4, int(trophy_h * _anim_scale))
                    trophy_rect = pygame.Rect(
                        WIDTH // 2 - draw_w // 2,
                        HEIGHT // 2 - draw_h // 2 - 170,
                        draw_w, draw_h,
                    )
                    self.draw_scaled_aura(trophy_rect)
                    if self.ttt_trophy_image:
                        trophy_scaled = pygame.transform.smoothscale(self.ttt_trophy_image, (draw_w, draw_h))
                        screen.blit(trophy_scaled, trophy_rect.topleft)
                if self.show_prompt:
                    btn_w, btn_h = 360, 54
                    btn_rect = pygame.Rect(WIDTH // 2 - btn_w // 2, HEIGHT - 110, btn_w, btn_h)
                    self.final_trophy_continue_rect = btn_rect
                    pygame.draw.rect(screen, (220, 220, 100), btn_rect, border_radius=12)
                    pygame.draw.rect(screen, (255, 165, 0), btn_rect, 3, border_radius=12)
                    btn_text = font_small.render('Return to Menu', True, (60, 40, 20))
                    screen.blit(btn_text, (btn_rect.centerx - btn_text.get_width() // 2, btn_rect.centery - btn_text.get_height() // 2))

            if puzzle_type in ['movement', 'catch_drops', 'card_collection', 'platform_jump', 'glide']:
                pygame.draw.circle(screen, (255, 200, 100), (int(self.player_x) + shake_x, int(self.player_y) + shake_y), 20)

            if puzzle_type == 'movement':
                for obstacle in self.current_obstacles:
                    draw_rect = obstacle.move(shake_x, shake_y)
                    pygame.draw.rect(screen, (70, 45, 25), draw_rect, border_radius=6)
                    pygame.draw.rect(screen, BLACK, draw_rect, 2, border_radius=6)
                if self.goal_x is not None:
                    goal_rect = pygame.Rect(self.goal_x + shake_x, 140 + shake_y, 80, HEIGHT - 280)
                    goal_surface = pygame.Surface((goal_rect.width, goal_rect.height), pygame.SRCALPHA)
                    goal_surface.fill((34, 177, 76, 110))
                    screen.blit(goal_surface, (goal_rect.x, goal_rect.y))
                    pygame.draw.rect(screen, (20, 120, 45), goal_rect, 3)

            for drop in self.drops:
                if puzzle_type == 'catch_drops':
                    color = BLUE if drop['type'] == 'clean' else (100, 100, 100)
                elif puzzle_type == 'card_collection':
                    color = RED if drop['type'] == 'card' else (255, 165, 0)  # RED for cards, ORANGE for hazards
                else:
                    color = BLUE
                pygame.draw.circle(screen, color, (int(drop['x']) + shake_x, int(drop['y']) + shake_y), 10)

            if self.completion_anim_active and fade_alpha > 0:
                if self.completion_anim_action == 'chapter_complete' and complete_source_image is not None and complete_target_rect is not None:
                    if self.puzzle_complete_image is not None and frame_rect is not None:
                        complete_overlay = pygame.transform.smoothscale(self.puzzle_complete_image, (frame_rect.width, frame_rect.height))
                    else:
                        complete_overlay = complete_source_image.copy()
                    complete_overlay.set_alpha(fade_alpha)
                    self.draw_scaled_aura(complete_target_rect)
                    screen.blit(complete_overlay, complete_target_rect)
                else:
                    fade_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                    fade_surface.fill((255, 255, 255, fade_alpha))
                    screen.blit(fade_surface, (0, 0))

            if (
                'chapter' in scene
                and self.get_next_chapter_scene() is not None
                and not self.completion_anim_active
            ):
                skip_w = 250
                skip_h = 56
                skip_x = WIDTH - skip_w - 24
                skip_y = HEIGHT - skip_h - 24
                self.skip_button_rect = pygame.Rect(skip_x, skip_y, skip_w, skip_h)
                self.skip_button_action = 'chapter'
                pygame.draw.rect(screen, (220, 220, 100), self.skip_button_rect, border_radius=10)
                pygame.draw.rect(screen, (255, 165, 0), self.skip_button_rect, 3, border_radius=10)
                skip_text = font.render('Skip Chapter', True, (60, 40, 20))
                screen.blit(
                    skip_text,
                    (
                        self.skip_button_rect.centerx - skip_text.get_width() // 2,
                        self.skip_button_rect.centery - skip_text.get_height() // 2,
                    ),
                )

            self.draw_chapter1_completion_prompt()
        
        # Draw exit button
        if self.exit_button_rect:
            if self.exit_button_image:
                exit_img_scaled = pygame.transform.scale(self.exit_button_image, (self.exit_button_rect.width, self.exit_button_rect.height))
                screen.blit(exit_img_scaled, self.exit_button_rect)
            else:
                # Fallback if image not loaded
                pygame.draw.rect(screen, (220, 220, 100), self.exit_button_rect, border_radius=8)
                pygame.draw.rect(screen, (255, 165, 0), self.exit_button_rect, 3, border_radius=8)
                exit_text = font.render('Exit', True, (60, 40, 20))
                screen.blit(exit_text, (self.exit_button_rect.centerx - exit_text.get_width() // 2, self.exit_button_rect.centery - exit_text.get_height() // 2))

    def clear_ui(self):
        for elem in self.ui_elements:
            elem[1].kill()
        self.ui_elements = []

    def update(self, time_delta):
        scene = scenes[self.current_scene]
        puzzle = scene.get('puzzle', {})
        
        # Track scene open time for fade effect
        self.scene_start_time += time_delta
        
        # Update typing animation for story scenes
        scene_type = scene.get('type', 'story')
        if scene_type == 'story':
            chapter_title, full_text = self.split_story_chapter_text(scene)
            chapter_intro_delay = 0.0
            if chapter_title and self.current_sentence_idx == 0:
                chapter_intro_delay = self.chapter_title_hold_duration + self.chapter_title_fade_duration
            # Split by periods and remove empty sentences
            sentences = [s.strip() + '.' for s in full_text.split('.') if s.strip()]
            if len(sentences) > 1:
                sentences = sentences[:-1]
            
            # Get current sentence text
            if self.current_sentence_idx < len(sentences):
                current_sentence = sentences[self.current_sentence_idx]
                
                # If we're showing the prompt, don't update typing
                if not self.show_prompt:
                    elapsed_typing_time = max(0.0, self.scene_start_time - chapter_intro_delay)
                    max_chars = int(elapsed_typing_time * self.typing_speed)
                    self.typed_chars = min(max_chars, len(current_sentence))
                    
                    # If we've finished typing current sentence, start pause
                    if self.typed_chars >= len(current_sentence):
                        self.sentence_pause_time += time_delta
                        
                        # After pause, show prompt only if this is the last sentence
                        if self.sentence_pause_time >= self.sentence_pause_duration:
                            if self.current_sentence_idx == len(sentences) - 1:
                                self.show_prompt = True
                            else:
                                # Move to next sentence
                                self.current_sentence_idx += 1
                                self.scene_start_time = 0.0
                                self.typed_chars = 0
                                self.sentence_pause_time = 0.0
                else:
                    # Show prompt and wait for button click
                    pass
            else:
                self.typed_chars = 0

        if self.completion_anim_active:
            self.completion_anim_time += time_delta
            shake_duration, fade_duration = self.get_completion_durations()
            if self.completion_anim_time >= shake_duration + fade_duration:
                self.finish_completion_animation()
            return

        puzzle_type = puzzle.get('type')
        keys = pygame.key.get_pressed()
        if puzzle_type in ['movement', 'catch_drops', 'platform_jump', 'glide', 'combined_hazards']:
            move_step = self.player_move_speed * time_delta
            if keys[pygame.K_LEFT]:
                self.player_x -= move_step
            if keys[pygame.K_RIGHT]:
                self.player_x += move_step
            if keys[pygame.K_UP]:
                self.player_y -= move_step
            if keys[pygame.K_DOWN]:
                self.player_y += move_step
        elif puzzle_type == 'forest_run':
            steer_speed = 1.9 * time_delta
            if keys[pygame.K_LEFT]:
                self.player_x -= steer_speed
            if keys[pygame.K_RIGHT]:
                self.player_x += steer_speed
            self.player_x = max(-1.0, min(1.0, self.player_x))
            self.forest_distance += self.forest_speed * time_delta
            self.forest_spawn_timer -= time_delta
            if self.forest_spawn_timer <= 0:
                self.spawn_forest_obstacle()
                self.forest_spawn_timer = random.uniform(0.38, 0.72)
            for obstacle in self.forest_obstacles[:]:
                obstacle['depth'] -= time_delta * 0.9
                if obstacle['depth'] <= 0.0:
                    self.forest_obstacles.remove(obstacle)
                    continue
                if obstacle['depth'] <= 0.18 and abs(self.player_x - obstacle['x']) <= obstacle['width']:
                    self.lives -= 1
                    self.forest_obstacles.remove(obstacle)
                    self.player_x = 0.0
                    if self.lives <= 0:
                        self.current_scene = 'chapter1_intro'
                        self.load_ui()
                        return
            if self.forest_distance >= self.forest_target_distance and not self.chapter_complete:
                reward = puzzle.get('reward')
                self.start_completion_animation('chapter_complete', reward)
                return
        elif puzzle_type == 'dodge_and_collect':
            required_score = puzzle.get('required_score', 15)
            player_half = 110
            # Handle player movement
            move_speed = 560 * time_delta
            if keys[pygame.K_LEFT]:
                self.player_x = max(player_half, self.player_x - move_speed)
            if keys[pygame.K_RIGHT]:
                self.player_x = min(WIDTH - player_half, self.player_x + move_speed)
            
            # Update time
            self.time_remaining -= time_delta
            
            # Spawn obstacles
            self.dodge_spawn_timer -= time_delta
            if self.dodge_spawn_timer <= 0:
                if random.random() < 0.6:
                    self.spawn_dodge_obstacle()
                else:
                    self.spawn_dodge_collectible()
                self.dodge_spawn_timer = random.uniform(0.22, 0.4)
            
            # Update obstacles
            for obstacle in self.dodge_obstacles[:]:
                obstacle['y'] += obstacle['speed'] * time_delta
                
                # Check collision with player
                obstacle_rect = pygame.Rect(obstacle['x'] - obstacle['width'] // 2, obstacle['y'] - obstacle['height'] // 2, obstacle['width'], obstacle['height'])
                player_rect = pygame.Rect(self.player_x - player_half, self.player_y - player_half, player_half * 2, player_half * 2)
                
                if obstacle_rect.colliderect(player_rect):
                    self.lives -= 1
                    self.dodge_obstacles.remove(obstacle)
                    if self.lives <= 0:
                        self.chapter1_attempted = True
                        self.current_scene = 'chapter1_intro'
                        self.load_ui()
                        return
                elif obstacle['y'] > HEIGHT:
                    self.dodge_obstacles.remove(obstacle)
            
            # Update collectibles
            for collectible in self.dodge_collectibles[:]:
                collectible['y'] += collectible['speed'] * time_delta
                
                # Check collision with player
                collectible_rect = pygame.Rect(collectible['x'] - collectible['size'] // 2, collectible['y'] - collectible['size'] // 2, collectible['size'], collectible['size'])
                player_rect = pygame.Rect(self.player_x - player_half, self.player_y - player_half, player_half * 2, player_half * 2)
                
                if collectible_rect.colliderect(player_rect):
                    self.collectibles_collected += 1
                    self.dodge_collectibles.remove(collectible)
                elif collectible['y'] > HEIGHT:
                    self.dodge_collectibles.remove(collectible)
            
            # Check win condition
            if self.collectibles_collected >= required_score and not self.chapter_complete:
                reward = puzzle.get('reward')
                self.start_completion_animation('chapter_complete', reward)
                return
            
            # Check time out
            if self.time_remaining <= 0 and not self.chapter_complete:
                self.chapter1_attempted = True
                self.current_scene = 'chapter1_intro'
                self.load_ui()
                return

        if puzzle_type == 'catch_drops' and random.random() < 0.05:
            drop_type = 'clean' if random.random() < 0.7 else 'polluted'
            self.drops.append({'x': random.randint(100, WIDTH - 100), 'y': 0, 'type': drop_type})

        if puzzle_type == 'card_collection' and random.random() < 0.06:
            card_type = 'card' if random.random() < 0.75 else 'hazard'
            self.drops.append({'x': random.randint(100, WIDTH - 100), 'y': 0, 'type': card_type})

        for drop in self.drops[:]:
            drop['y'] += 5
            if drop['y'] > HEIGHT:
                self.drops.remove(drop)
            elif abs(self.player_x - drop['x']) < 40 and abs(self.player_y - drop['y']) < 40:
                if puzzle_type == 'catch_drops':
                    if drop['type'] == 'clean':
                        self.score += 1
                    else:
                        self.lives -= 1
                elif puzzle_type == 'card_collection':
                    if drop['type'] == 'card':
                        self.score += 1
                    else:
                        self.lives -= 1
                self.drops.remove(drop)

        if puzzle_type == 'dragdrop' and self.pieces:
            self.reconcile_piece_locks()
            if all(piece.get('locked') for piece in self.pieces) and not self.chapter_complete:
                self.build_completed_puzzle_fallback()
                self.start_completion_animation('chapter_complete', puzzle.get('reward'))

        if puzzle_type == 'movement':
            player_rect = pygame.Rect(int(self.player_x) - 18, int(self.player_y) - 18, 36, 36)
            hit_obstacle = any(player_rect.colliderect(obstacle) for obstacle in self.current_obstacles)
            if hit_obstacle:
                self.lives -= 1
                self.player_x = 100
                self.player_y = HEIGHT // 2
                if self.lives <= 0:
                    self.current_scene = 'chapter2_intro'
                    self.load_ui()
                    return
            if self.goal_x is not None and self.player_x >= self.goal_x:
                reward = puzzle.get('reward')
                if reward:
                    self.collected_elements.add(reward)
                self.current_scene = 'chapter3_intro'
                self.load_ui()
                return

        if puzzle_type == 'final_dragdrop' and self.pieces:
            self.reconcile_piece_locks()
            if all(piece.get('locked') for piece in self.pieces):
                self.start_completion_animation('victory')

        if puzzle_type == 'memory_sequence' and len(self.player_sequence) == len(self.symbol_sequence):
            if self.player_sequence == self.symbol_sequence:
                reward = puzzle.get('reward')
                if reward:
                    self.collected_elements.add(reward)
                self.chapter_complete = True
            elif self.attempts_remaining <= 0:
                self.chapter_complete = False

        if puzzle_type in ['catch_drops', 'card_collection']:
            required_score = puzzle.get('required_score', 10)
            if self.score >= required_score and not self.chapter_complete:
                reward = puzzle.get('reward')
                self.start_completion_animation('chapter_complete', reward)
                return
            elif self.time_remaining <= 0:
                if self.score < required_score:
                    self.lives -= 1
                    if self.lives <= 0:
                        self.current_scene = 'chapter3_intro'
                        self.load_ui()
                        return
                    else:
                        self.time_remaining = puzzle.get('time_limit', 30)
                        self.score = 0
                        self.drops = []
                        self.player_x = WIDTH // 2
                        self.player_y = HEIGHT - 50
                else:
                    reward = puzzle.get('reward')
                    self.start_completion_animation('chapter_complete', reward)
                    return
            elif self.lives <= 0:
                self.current_scene = 'chapter3_intro'
                self.load_ui()
                return

        if puzzle_type == 'memory_pairs':
            flip_speed = 6.0
            for idx, card in enumerate(self.memory_cards):
                target = 1.0 if (card.get('matched') or idx in self.memory_flipped) else 0.0
                current = card.get('flip_value', 0.0)
                if current < target:
                    current = min(target, current + flip_speed * time_delta)
                elif current > target:
                    current = max(target, current - flip_speed * time_delta)
                card['flip_value'] = current

            if self.memory_mismatch_timer > 0:
                self.memory_mismatch_timer = max(0.0, self.memory_mismatch_timer - time_delta)
                if self.memory_mismatch_timer == 0.0:
                    self.memory_flipped = []
            if self.memory_matched == len(self.memory_cards) // 2 and not self.chapter_complete:
                reward = puzzle.get('reward')
                self.start_completion_animation('chapter_complete', reward)
                return
            elif (
                puzzle.get('fail_on_miss', True)
                and self.memory_attempts <= 0
                and self.memory_matched < len(self.memory_cards) // 2
                and self.memory_mismatch_timer <= 0
            ):
                if self.current_scene == 'chapter3':
                    self.current_scene = 'chapter3'
                else:
                    self.current_scene = 'chapter4_intro'
                self.load_ui()
                return

        if puzzle_type == 'tictactoe':
            wins_needed = int(puzzle.get('wins_needed', 3))
            if self.tictactoe_player_wins >= wins_needed and not self.chapter_complete:
                reward = puzzle.get('reward')
                if reward:
                    self.collected_elements.add(reward)
                self.chapter_complete = True
                self.ttt_player_won = True
                self.ttt_trophy_revealed = False
                self.ttt_trophy_anim_time = 0.0
                self.current_sentence_idx = 0
                self.typed_chars = 0
                self.sentence_pause_time = 0.0
                self.scene_start_time = 0.0
                self.show_prompt = False
                return
            elif self.tictactoe_ai_wins >= wins_needed:
                if self.current_scene == 'chapter4':
                    self.current_scene = 'chapter4_intro'
                else:
                    self.current_scene = 'final_intro'
                self.load_ui()
                return

            if self.ttt_player_won:
                victory_sentences = [
                    "Congratulations! You earned a trophy for saving the flock's land.",
                    "Peace will now be restored to Quacklands.",
                    "Through steadfast courage and wisdom, you silenced the temple guardian.",
                    "The ancient powers awaken, and the First Flock honors your name.",
                ]
                if self.ttt_trophy_revealed:
                    _TROPHY_ANIM_DUR = 0.5
                    self.ttt_trophy_anim_time += time_delta
                    if self.ttt_trophy_anim_time >= _TROPHY_ANIM_DUR and not self.show_prompt:
                        self.show_prompt = True
                    return
                if self.current_sentence_idx < len(victory_sentences):
                    current_sentence = victory_sentences[self.current_sentence_idx]
                    if not self.show_prompt:
                        max_chars = int(self.scene_start_time * self.typing_speed)
                        self.typed_chars = min(max_chars, len(current_sentence))

                        if self.typed_chars >= len(current_sentence):
                            self.sentence_pause_time += time_delta
                            if self.sentence_pause_time >= self.sentence_pause_duration:
                                if self.current_sentence_idx == len(victory_sentences) - 1:
                                    self.ttt_trophy_revealed = True
                                    self.ttt_trophy_anim_time = 0.0
                                else:
                                    self.current_sentence_idx += 1
                                    self.scene_start_time = 0.0
                                    self.typed_chars = 0
                                    self.sentence_pause_time = 0.0
                return
            
            # AI move logic
            if self.tictactoe_current_turn == 'ai':
                # Advance all mark pop-in animations
                for k in list(self.ttt_mark_anims.keys()):
                    self.ttt_mark_anims[k] += time_delta

                # Wait for the delay before placing
                self.ttt_ai_delay_timer -= time_delta
                if self.ttt_ai_delay_timer > 0:
                    return

                ai_idx = self.get_tictactoe_ai_move(self.tictactoe_board)
                if ai_idx is not None:
                    self.tictactoe_board[ai_idx] = 'O'
                    self.ttt_mark_anims[ai_idx] = 0.0

                # Check for win/draw
                winner = self.check_tictactoe_winner(self.tictactoe_board)
                if winner == 'X':
                    self.tictactoe_player_wins += 1
                    if self.tictactoe_player_wins < wins_needed:
                        self.tictactoe_board = [None] * 9
                        self.ttt_mark_anims = {}
                elif winner == 'O':
                    self.tictactoe_ai_wins += 1
                    if self.tictactoe_ai_wins < wins_needed:
                        self.tictactoe_board = [None] * 9
                        self.ttt_mark_anims = {}
                elif all(cell is not None for cell in self.tictactoe_board):
                    # Draw - reset
                    self.tictactoe_board = [None] * 9
                    self.ttt_mark_anims = {}
                else:
                    self.tictactoe_current_turn = 'player'
                    return

                if self.tictactoe_player_wins < wins_needed and self.tictactoe_ai_wins < wins_needed:
                    self.tictactoe_current_turn = 'player'
            else:
                # Advance all mark pop-in animations while it's the player's turn too
                for k in list(self.ttt_mark_anims.keys()):
                    self.ttt_mark_anims[k] += time_delta

        if puzzle_type == 'element_ascension':
            final_sentences = [
                "You have done the impossible.",
                "The four sacred forces — Earth, Nature, Water, and Fire — are restored.",
                "Peace and balance return to Quacklands at last.",
                "The First Flock honors your courage, forever.",
            ]
            if self.final_trophy_revealed:
                _TROPHY_ANIM_DUR = 0.5
                self.final_trophy_anim_time += time_delta
                if self.final_trophy_anim_time >= _TROPHY_ANIM_DUR and not self.show_prompt:
                    self.show_prompt = True
                return
            if self.current_sentence_idx < len(final_sentences):
                current_sentence = final_sentences[self.current_sentence_idx]
                if not self.show_prompt:
                    max_chars = int(self.scene_start_time * self.typing_speed)
                    self.typed_chars = min(max_chars, len(current_sentence))
                    if self.typed_chars >= len(current_sentence):
                        self.sentence_pause_time += time_delta
                        if self.sentence_pause_time >= self.sentence_pause_duration:
                            if self.current_sentence_idx == len(final_sentences) - 1:
                                self.final_trophy_revealed = True
                                self.final_trophy_anim_time = 0.0
                            else:
                                self.current_sentence_idx += 1
                                self.scene_start_time = 0.0
                                self.typed_chars = 0
                                self.sentence_pause_time = 0.0
            return

        if puzzle_type == 'forest_run':
            self.player_x = max(-1.0, min(1.0, self.player_x))
        else:
            self.player_x = max(20, min(WIDTH - 20, self.player_x))
            self.player_y = max(20, min(HEIGHT - 20, self.player_y))

    def handle_events(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pygame.mouse.get_pos()
            if self.exit_button_rect and self.exit_button_rect.collidepoint(mouse_pos):
                self.current_scene = 'main_menu'
                self.load_ui()
                return
            if self.skip_button_rect and self.skip_button_rect.collidepoint(mouse_pos):
                if self.skip_button_action == 'chapter':
                    if self.skip_current_chapter_game():
                        return
                elif self.skip_button_action == 'script':
                    if self.skip_current_script():
                        return

        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            for elem in self.ui_elements:
                if elem[0] == 'choice' and elem[1] == event.ui_element:
                    next_scene = elem[2]
                    if next_scene == 'quit':
                        self.running = False
                    else:
                        self.current_scene = next_scene
                        self.load_ui()
                elif elem[0] == 'exit' and elem[1] == event.ui_element:
                    self.current_scene = 'main_menu'
                    self.load_ui()

        # Skip typing animation with any key or click
        scene = scenes[self.current_scene]
        if scene.get('type') == 'story':
            if event.type == pygame.KEYDOWN or (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1):
                # If prompt is showing and button is clicked, advance to next scene
                if self.show_prompt and event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    if self.continue_button_rect and self.continue_button_rect.collidepoint(mouse_pos):
                        # Get next scene from choices
                        choices = scene.get('choices', [])
                        next_scene = None
                        if isinstance(choices, list) and choices:
                            first_choice = choices[0]
                            if isinstance(first_choice, dict):
                                next_scene = first_choice.get('next')
                        elif isinstance(choices, dict):
                            next_scene = choices.get('next')

                        if next_scene:
                            if next_scene == 'quit':
                                self.running = False
                            else:
                                self.current_scene = next_scene
                                self.load_ui()
                        return
                # Otherwise skip typing to show full sentence
                _, full_text = self.split_story_chapter_text(scene)
                sentences = [s.strip() + '.' for s in full_text.split('.') if s.strip()]
                if len(sentences) > 1:
                    sentences = sentences[:-1]
                if self.current_sentence_idx < len(sentences):
                    current_sentence = sentences[self.current_sentence_idx]
                    if self.typed_chars < len(current_sentence):
                        self.typed_chars = len(current_sentence)
                        return

        if self.completion_anim_active and event.type in [pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION, pygame.KEYDOWN]:
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pygame.mouse.get_pos()
            
            # Check menu button clicks
            if self.current_scene == 'main_menu':
                for button_rect, next_scene in self.menu_button_rects:
                    if button_rect.collidepoint(mouse_pos):
                        if next_scene == 'quit':
                            self.running = False
                        else:
                            self.current_scene = next_scene
                            self.load_ui()
                        return
            
            if (
                self.current_scene == 'chapter1'
                and self.chapter_complete
                and self.chapter1_continue_rect is not None
                and self.chapter1_continue_rect.collidepoint(mouse_pos)
            ):
                self.current_scene = 'chapter2_intro'
                self.load_ui()
                return
            for piece in self.pieces:
                if piece.get('locked'):
                    continue
                rect = pygame.Rect(piece['current_pos'][0], piece['current_pos'][1], piece['size'][0], piece['size'][1])
                if rect.collidepoint(mouse_pos):
                    self.dragged_piece = piece
                    self.offset = (mouse_pos[0] - piece['current_pos'][0], mouse_pos[1] - piece['current_pos'][1])
                    break
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.dragged_piece:
                if self.is_piece_aligned(self.dragged_piece, self.snap_threshold()):
                    self.lock_piece(self.dragged_piece)
                self.dragged_piece = None
        elif event.type == pygame.MOUSEMOTION and self.dragged_piece:
            mouse_pos = pygame.mouse.get_pos()
            self.dragged_piece['current_pos'][0] = mouse_pos[0] - self.offset[0]
            self.dragged_piece['current_pos'][1] = mouse_pos[1] - self.offset[1]

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pygame.mouse.get_pos()
            scene = scenes[self.current_scene]
            puzzle = scene.get('puzzle', {})
            puzzle_type = scene.get('puzzle', {}).get('type')
            symbol_positions = [(200, 250), (400, 250), (200, 400), (400, 400)]
            for idx, pos in enumerate(symbol_positions):
                dist = ((mouse_pos[0] - pos[0]) ** 2 + (mouse_pos[1] - pos[1]) ** 2) ** 0.5
                if dist < 50 and len(self.player_sequence) < len(self.symbol_sequence):
                    self.player_sequence.append(idx)
                    if idx != self.symbol_sequence[len(self.player_sequence) - 1]:
                        self.attempts_remaining -= 1
                        self.player_sequence = []

            if puzzle_type == 'memory_pairs':
                if self.memory_mismatch_timer > 0:
                    return

                card_w, card_h, cards_per_row, start_x, start_y, card_gap = self.get_memory_layout()
                for idx, card in enumerate(self.memory_cards):
                    if card['matched']:
                        continue
                    row = idx // cards_per_row
                    col = idx % cards_per_row
                    x = start_x + col * (card_w + card_gap)
                    y = start_y + row * (card_h + card_gap)
                    card_rect = pygame.Rect(x, y, card_w, card_h)
                    if card_rect.collidepoint(mouse_pos) and len(self.memory_flipped) < 2:
                        if idx not in self.memory_flipped:
                            self.memory_flipped.append(idx)
                            if len(self.memory_flipped) == 2:
                                if self.memory_cards[self.memory_flipped[0]].get('match_key') == self.memory_cards[self.memory_flipped[1]].get('match_key'):
                                    self.memory_cards[self.memory_flipped[0]]['matched'] = True
                                    self.memory_cards[self.memory_flipped[1]]['matched'] = True
                                    self.memory_matched += 1
                                    self.memory_flipped = []
                                else:
                                    if puzzle.get('fail_on_miss', True):
                                        self.memory_attempts -= 1
                                    self.memory_mismatch_timer = 0.7

            if puzzle_type == 'element_ascension' and self.final_trophy_active:
                if self.final_trophy_continue_rect and self.final_trophy_continue_rect.collidepoint(mouse_pos):
                    self.current_scene = 'main_menu'
                    self.load_ui()
                    return
                final_sentences = [
                    "You have done the impossible.",
                    "The four sacred forces \u2014 Earth, Nature, Water, and Fire \u2014 are restored.",
                    "Peace and balance return to Quacklands at last.",
                    "The First Flock honors your courage, forever.",
                ]
                if not self.show_prompt and self.current_sentence_idx < len(final_sentences):
                    current_sentence = final_sentences[self.current_sentence_idx]
                    if self.typed_chars < len(current_sentence):
                        self.typed_chars = len(current_sentence)
                return

            if puzzle_type == 'tictactoe' and self.ttt_player_won:
                if self.ttt_win_continue_rect and self.ttt_win_continue_rect.collidepoint(mouse_pos):
                    self.current_scene = 'main_menu'
                    self.load_ui()
                    return
                victory_sentences = [
                    "Congratulations! You earned a trophy for saving the flock's land.",
                    "Peace will now be restored to Quacklands.",
                    "Through steadfast courage and wisdom, you silenced the temple guardian.",
                    "The ancient powers awaken, and the First Flock honors your name.",
                ]
                if not self.show_prompt and self.current_sentence_idx < len(victory_sentences):
                    current_sentence = victory_sentences[self.current_sentence_idx]
                    if self.typed_chars < len(current_sentence):
                        self.typed_chars = len(current_sentence)
                return

            if puzzle_type == 'tictactoe' and self.tictactoe_current_turn == 'player' and not self.ttt_player_won:
                board_size = 560
                cell_size = board_size // 3
                board_x = (WIDTH - board_size) // 2
                board_y = (HEIGHT - board_size) // 2
                for idx in range(9):
                    if self.tictactoe_board[idx] is not None:
                        continue
                    row = idx // 3
                    col = idx % 3
                    x = board_x + col * cell_size
                    y = board_y + row * cell_size
                    cell_rect = pygame.Rect(x, y, cell_size, cell_size)
                    if cell_rect.collidepoint(mouse_pos):
                        self.tictactoe_board[idx] = 'X'
                        self.ttt_mark_anims[idx] = 0.0
                        # Check if player won immediately
                        if self.check_tictactoe_winner(self.tictactoe_board) == 'X':
                            puzzle = scenes[self.current_scene].get('puzzle', {})
                            wins_needed = int(puzzle.get('wins_needed', 3))
                            self.tictactoe_player_wins += 1
                            if self.tictactoe_player_wins < wins_needed:
                                self.tictactoe_board = [None] * 9
                                self.ttt_mark_anims = {}
                                self.tictactoe_current_turn = 'player'
                            else:
                                self.tictactoe_current_turn = 'ai'
                        else:
                            self.ttt_ai_delay_timer = 0.85
                            self.tictactoe_current_turn = 'ai'
                        break

    def run(self):
        clock = pygame.time.Clock()
        self.current_scene = 'main_menu'
        self.load_ui()
        while self.running:
            time_delta = clock.tick(60) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                manager.process_events(event)
                self.handle_events(event)
            self.update(time_delta)
            manager.update(time_delta)
            screen.fill(WHITE)
            self.draw_scene()
            manager.draw_ui(screen)
            pygame.display.flip()
        pygame.quit()
