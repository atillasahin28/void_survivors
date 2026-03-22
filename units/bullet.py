"""Bullet units for player and enemy projectiles.

PlayerBullet and EnemyBullet share the same base behavior
(fly in a straight line, die when off-screen) but differ in
speed, color, damage, and what they can hit.
"""

import pygame
import math
from units.unit import Unit


class PlayerBullet(Unit):
    """A bullet fired by the player.

    Flies in a straight line at the aimed angle.
    Deals damage to enemies on collision.
    """

    SPEED = 10
    DAMAGE = 25

    def __init__(self, position, angle):
        """Initialize a player bullet.

        Args:
            position: pygame.Vector2 spawn position.
            angle: Direction in radians.
        """
        speed = pygame.Vector2(
            math.cos(angle) * self.SPEED,
            math.sin(angle) * self.SPEED
        )
        super().__init__(position, speed, radius=4, color=(255, 255, 100))
        self.damage = self.DAMAGE

    def update(self, world_size, **kwargs):
        """Move forward; die if off-screen.

        Args:
            world_size: pygame.Vector2 with world dimensions.
        """
        self.step()
        if self.is_off_screen(world_size):
            self.kill()

    def draw(self, surface, camera_offset):
        """Draw the bullet as a bright circle with a glow.

        Args:
            surface: pygame.Surface to draw on.
            camera_offset: pygame.Vector2 camera translation.
        """
        screen = self.screen_pos(camera_offset)
        pygame.draw.circle(surface, (255, 200, 50), screen, self.radius + 2)
        pygame.draw.circle(surface, self.color, screen, self.radius)


class EnemyBullet(Unit):
    """A bullet fired by enemy ShooterEnemy units.

    Slower and differently colored than player bullets.
    Deals damage to the player on collision.
    """

    SPEED = 5
    DAMAGE = 10

    def __init__(self, position, angle):
        """Initialize an enemy bullet.

        Args:
            position: pygame.Vector2 spawn position.
            angle: Direction in radians.
        """
        speed = pygame.Vector2(
            math.cos(angle) * self.SPEED,
            math.sin(angle) * self.SPEED
        )
        super().__init__(position, speed, radius=5, color=(255, 80, 80))
        self.damage = self.DAMAGE

    def update(self, world_size, **kwargs):
        """Move forward; die if off-screen.

        Args:
            world_size: pygame.Vector2 with world dimensions.
        """
        self.step()
        if self.is_off_screen(world_size):
            self.kill()

    def draw(self, surface, camera_offset):
        """Draw the enemy bullet as a red circle.

        Args:
            surface: pygame.Surface to draw on.
            camera_offset: pygame.Vector2 camera translation.
        """
        screen = self.screen_pos(camera_offset)
        pygame.draw.circle(surface, (180, 30, 30), screen, self.radius + 1)
        pygame.draw.circle(surface, self.color, screen, self.radius)
