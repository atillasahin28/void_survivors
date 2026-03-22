"""Heads-Up Display (HUD) for in-game information.

Renders the player's score, health bar, current wave number,
active powerup indicators, and wave announcements on screen.
"""

import pygame
import time


class HUD:
    """Draws game information overlays on the screen.

    Shows health bar, score, wave number, and active powerup
    timers. Displays a wave announcement at the start of each wave.
    """

    def __init__(self):
        """Initialize the HUD with default fonts."""
        self.font_large = None
        self.font_medium = None
        self.font_small = None
        self.wave_announce_time = 0
        self.wave_announce_number = 0
        self._init_fonts()

    def _init_fonts(self):
        """Load fonts for HUD text rendering."""
        pygame.font.init()
        self.font_large = pygame.font.SysFont("Arial", 42, bold=True)
        self.font_medium = pygame.font.SysFont("Arial", 24, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 18)

    def announce_wave(self, wave_number):
        """Trigger a wave announcement display.

        Args:
            wave_number: The wave number to announce.
        """
        self.wave_announce_time = time.time()
        self.wave_announce_number = wave_number

    def draw(self, surface, player, wave_number):
        """Render all HUD elements on the surface.

        Args:
            surface: pygame.Surface to draw on.
            player: Player instance for health/score/powerup data.
            wave_number: Current wave number.
        """
        self._draw_health_bar(surface, player)
        self._draw_score(surface, player.score)
        self._draw_wave_indicator(surface, wave_number)
        self._draw_powerup_indicators(surface, player)
        self._draw_wave_announcement(surface)

    def _draw_health_bar(self, surface, player):
        """Draw the main health bar at the top-left.

        Args:
            surface: pygame.Surface to draw on.
            player: Player instance for health data.
        """
        x, y = 20, 20
        bar_width = 200
        bar_height = 20
        ratio = player.health / player.max_health

        # Background
        pygame.draw.rect(surface, (40, 40, 40), (x - 2, y - 2, bar_width + 4, bar_height + 4), border_radius=4)
        pygame.draw.rect(surface, (80, 0, 0), (x, y, bar_width, bar_height), border_radius=3)

        # Health fill
        bar_color = (0, 200, 50) if ratio > 0.5 else (200, 200, 0) if ratio > 0.25 else (200, 0, 0)
        fill_width = max(0, int(bar_width * ratio))
        if fill_width > 0:
            pygame.draw.rect(surface, bar_color, (x, y, fill_width, bar_height), border_radius=3)

        # Health text
        hp_text = self.font_small.render(f"{player.health}/{player.max_health}", True, (255, 255, 255))
        surface.blit(hp_text, (x + bar_width / 2 - hp_text.get_width() / 2, y + 1))

    def _draw_score(self, surface, score):
        """Draw the score display at the top-right.

        Args:
            surface: pygame.Surface to draw on.
            score: Integer score value.
        """
        screen_w = surface.get_width()
        score_text = self.font_medium.render(f"Score: {score}", True, (255, 255, 255))
        surface.blit(score_text, (screen_w - score_text.get_width() - 20, 20))

    def _draw_wave_indicator(self, surface, wave_number):
        """Draw the current wave number at the top-center.

        Args:
            surface: pygame.Surface to draw on.
            wave_number: Current wave number.
        """
        if wave_number > 0:
            screen_w = surface.get_width()
            wave_text = self.font_medium.render(f"Wave {wave_number}", True, (200, 200, 200))
            surface.blit(wave_text, (screen_w / 2 - wave_text.get_width() / 2, 20))

    def _draw_powerup_indicators(self, surface, player):
        """Draw active powerup timers below the health bar.

        Args:
            surface: pygame.Surface to draw on.
            player: Player instance for powerup timer data.
        """
        y_offset = 48
        now = time.time()

        if now < player.speed_boost_end:
            remaining = player.speed_boost_end - now
            text = self.font_small.render(f"Speed Boost: {remaining:.1f}s", True, (255, 220, 0))
            surface.blit(text, (20, y_offset))
            y_offset += 22

        if now < player.multi_shot_end:
            remaining = player.multi_shot_end - now
            text = self.font_small.render(f"Multi-Shot: {remaining:.1f}s", True, (100, 150, 255))
            surface.blit(text, (20, y_offset))

    def _draw_wave_announcement(self, surface):
        """Draw a large wave announcement that fades over 2 seconds.

        Args:
            surface: pygame.Surface to draw on.
        """
        elapsed = time.time() - self.wave_announce_time
        if elapsed < 2.0:
            alpha = max(0, 1 - elapsed / 2.0)
            screen_w = surface.get_width()
            screen_h = surface.get_height()
            text = self.font_large.render(f"WAVE {self.wave_announce_number}", True,
                                          (int(255 * alpha), int(255 * alpha), int(100 * alpha)))
            surface.blit(text, (screen_w / 2 - text.get_width() / 2,
                                screen_h / 3 - text.get_height() / 2))

    def draw_game_over(self, surface, score, wave_number):
        """Draw the game over screen.

        Args:
            surface: pygame.Surface to draw on.
            score: Final score.
            wave_number: Wave reached.
        """
        screen_w = surface.get_width()
        screen_h = surface.get_height()

        # Dimmed overlay
        overlay = pygame.Surface((screen_w, screen_h))
        overlay.set_alpha(150)
        overlay.fill((0, 0, 0))
        surface.blit(overlay, (0, 0))

        # Game Over text
        go_text = self.font_large.render("GAME OVER", True, (255, 60, 60))
        surface.blit(go_text, (screen_w / 2 - go_text.get_width() / 2, screen_h / 3))

        score_text = self.font_medium.render(f"Score: {score}  |  Wave: {wave_number}", True, (255, 255, 255))
        surface.blit(score_text, (screen_w / 2 - score_text.get_width() / 2, screen_h / 3 + 60))

        restart_text = self.font_small.render("Press R to restart or Q to quit", True, (180, 180, 180))
        surface.blit(restart_text, (screen_w / 2 - restart_text.get_width() / 2, screen_h / 3 + 100))
