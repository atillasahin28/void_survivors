"""PowerUp units that grant temporary or permanent boosts.

PowerUps spawn when enemies are killed (with a random chance).
They float in place with a pulsing animation and despawn after
a timeout. Three types:
- HealthPowerUp: Restores 30 HP.
- SpeedPowerUp: 6 seconds of increased movement speed.
- MultiShotPowerUp: 8 seconds of triple-bullet spread.
"""

import pygame
import math
import time
from units.unit import Unit


class PowerUpBase(Unit):
    """Abstract base for all powerup types.

    PowerUps pulse in size, have a lifetime, and are collected
    on contact with the player.
    """

    LIFETIME = 8.0  # seconds before despawning

    def __init__(self, position, color, powerup_type):
        """Initialize a powerup.

        Args:
            position: pygame.Vector2 spawn position.
            color: RGB tuple for rendering.
            powerup_type: String identifier for the effect.
        """
        super().__init__(position, pygame.Vector2(0, 0), radius=12, color=color)
        self.powerup_type = powerup_type
        self.spawn_time = time.time()
        self.pulse_phase = 0

    def update(self, world_size, **kwargs):
        """Animate the pulse and check lifetime.

        Args:
            world_size: pygame.Vector2 with world dimensions.
        """
        self.pulse_phase += 0.08
        if time.time() - self.spawn_time > self.LIFETIME:
            self.kill()

    def draw(self, surface, camera_offset):
        """Draw the powerup with a pulsing glow effect.

        Args:
            surface: pygame.Surface to draw on.
            camera_offset: pygame.Vector2 camera translation.
        """
        screen = self.screen_pos(camera_offset)
        pulse = 1 + 0.2 * math.sin(self.pulse_phase)
        r = int(self.radius * pulse)

        # Glow ring
        glow_color = tuple(min(255, c + 50) for c in self.color)
        pygame.draw.circle(surface, glow_color, screen, r + 4, 2)
        # Main body
        pygame.draw.circle(surface, self.color, screen, r)

    def get_type(self):
        """Return the powerup type string.

        Returns:
            String identifying the powerup effect.
        """
        return self.powerup_type


class HealthPowerUp(PowerUpBase):
    """Restores 30 HP to the player. Drawn as a green circle with a '+'."""

    def __init__(self, position):
        super().__init__(position, (0, 220, 80), "health")

    def draw(self, surface, camera_offset):
        """Draw with a '+' symbol inside.

        Args:
            surface: pygame.Surface to draw on.
            camera_offset: pygame.Vector2 camera translation.
        """
        super().draw(surface, camera_offset)
        screen = self.screen_pos(camera_offset)
        # Draw plus sign
        white = (255, 255, 255)
        pygame.draw.line(surface, white, (screen.x - 5, screen.y), (screen.x + 5, screen.y), 2)
        pygame.draw.line(surface, white, (screen.x, screen.y - 5), (screen.x, screen.y + 5), 2)


class SpeedPowerUp(PowerUpBase):
    """Grants 6 seconds of increased movement speed. Drawn as a yellow bolt."""

    def __init__(self, position):
        super().__init__(position, (255, 220, 0), "speed")

    def draw(self, surface, camera_offset):
        """Draw with a lightning bolt symbol.

        Args:
            surface: pygame.Surface to draw on.
            camera_offset: pygame.Vector2 camera translation.
        """
        super().draw(surface, camera_offset)
        screen = self.screen_pos(camera_offset)
        # Draw arrow/bolt
        pts = [
            (screen.x - 3, screen.y - 6),
            (screen.x + 2, screen.y - 1),
            (screen.x - 1, screen.y - 1),
            (screen.x + 3, screen.y + 6),
            (screen.x - 2, screen.y + 1),
            (screen.x + 1, screen.y + 1),
        ]
        pygame.draw.polygon(surface, (255, 255, 255), pts)


class MultiShotPowerUp(PowerUpBase):
    """Grants 8 seconds of triple-spread bullets. Drawn as a blue circle with '3'."""

    def __init__(self, position):
        super().__init__(position, (100, 150, 255), "multishot")

    def draw(self, surface, camera_offset):
        """Draw with three dots representing triple shot.

        Args:
            surface: pygame.Surface to draw on.
            camera_offset: pygame.Vector2 camera translation.
        """
        super().draw(surface, camera_offset)
        screen = self.screen_pos(camera_offset)
        white = (255, 255, 255)
        for dx in [-4, 0, 4]:
            pygame.draw.circle(surface, white, (int(screen.x + dx), int(screen.y)), 2)
