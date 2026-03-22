"""Camera module for smooth player-following viewport.

The camera smoothly tracks the player's position, providing
a scrolling world view. Includes a screen shake effect that
can be triggered on impacts or explosions.
"""

import pygame
import random


class Camera:
    """Smooth-follow camera with screen shake support.

    The camera computes an offset vector that translates world
    coordinates to screen coordinates, keeping the player centered.
    """

    SMOOTHING = 0.1  # Lower = smoother/slower follow

    def __init__(self, screen_size):
        """Initialize the camera centered on the screen.

        Args:
            screen_size: Tuple (width, height) of the display.
        """
        self.offset = pygame.Vector2(0, 0)
        self.screen_size = pygame.Vector2(screen_size)
        self.shake_intensity = 0
        self.shake_decay = 0.85

    def update(self, target_pos):
        """Smoothly move the camera toward the target position.

        Args:
            target_pos: pygame.Vector2 of the player's world position.
        """
        desired = self.screen_size / 2 - target_pos
        self.offset += (desired - self.offset) * self.SMOOTHING

        # Apply screen shake
        if self.shake_intensity > 0.5:
            shake = pygame.Vector2(
                random.uniform(-self.shake_intensity, self.shake_intensity),
                random.uniform(-self.shake_intensity, self.shake_intensity),
            )
            self.offset += shake
            self.shake_intensity *= self.shake_decay
        else:
            self.shake_intensity = 0

    def trigger_shake(self, intensity=8):
        """Start a screen shake effect.

        Args:
            intensity: Initial shake magnitude in pixels.
        """
        self.shake_intensity = max(self.shake_intensity, intensity)

    def get_offset(self):
        """Return the current camera offset vector.

        Returns:
            pygame.Vector2 to add to world positions for screen positions.
        """
        return self.offset

    def resize(self, new_size):
        """Update camera for a new screen size.

        Args:
            new_size: Tuple (width, height) of the new display.
        """
        self.screen_size = pygame.Vector2(new_size)
