"""Base Unit class for all game entities.

All objects in the game (player, enemies, bullets, powerups, particles)
inherit from Unit, providing shared position/speed physics and drawing.
This is the core of the polymorphism used throughout the game.
"""

import pygame
from abc import ABC, abstractmethod


class Unit(ABC):
    """Abstract base class for all game entities.

    Provides shared position, speed, radius, and basic physics
    (movement and boundary handling). Subclasses must implement
    `draw()` and `update()`.
    """

    def __init__(self, position, speed, radius=20, color=(255, 255, 255)):
        """Initialize a Unit with position, speed, size, and color.

        Args:
            position: pygame.Vector2 world position.
            speed: pygame.Vector2 velocity per frame.
            radius: Collision/draw radius in pixels.
            color: RGB tuple for rendering.
        """
        self.position = pygame.Vector2(position)
        self.speed = pygame.Vector2(speed)
        self.radius = radius
        self.color = color
        self.alive = True

    def step(self):
        """Move the unit by its current speed vector."""
        self.position += self.speed

    def stay_on_screen(self, world_size):
        """Bounce the unit off the world boundaries.

        Args:
            world_size: pygame.Vector2 with world width and height.
        """
        width, height = world_size.x, world_size.y
        if self.position.x < self.radius:
            self.position.x = self.radius
            self.speed.x = abs(self.speed.x)
        if self.position.y < self.radius:
            self.position.y = self.radius
            self.speed.y = abs(self.speed.y)
        if self.position.x > width - self.radius:
            self.position.x = width - self.radius
            self.speed.x = -abs(self.speed.x)
        if self.position.y > height - self.radius:
            self.position.y = height - self.radius
            self.speed.y = -abs(self.speed.y)

    def is_off_screen(self, world_size, margin=50):
        """Check if the unit is far outside the world boundaries.

        Args:
            world_size: pygame.Vector2 with world dimensions.
            margin: Extra pixels beyond the boundary before removal.

        Returns:
            True if the unit is outside world + margin.
        """
        return (self.position.x < -margin or self.position.x > world_size.x + margin or
                self.position.y < -margin or self.position.y > world_size.y + margin)

    def collides_with(self, other):
        """Check circular collision with another Unit.

        Args:
            other: Another Unit instance.

        Returns:
            True if the units' circles overlap.
        """
        distance = self.position.distance_to(other.position)
        return distance < self.radius + other.radius

    def kill(self):
        """Mark this unit as dead for removal."""
        self.alive = False

    @abstractmethod
    def draw(self, surface, camera_offset):
        """Draw the unit on the surface with camera offset.

        Args:
            surface: pygame.Surface to draw on.
            camera_offset: pygame.Vector2 to translate world to screen coords.
        """
        ...

    @abstractmethod
    def update(self, world_size, **kwargs):
        """Update the unit each frame.

        Args:
            world_size: pygame.Vector2 with world dimensions.
            **kwargs: Additional context (e.g., player position for enemies).
        """
        ...

    def screen_pos(self, camera_offset):
        """Convert world position to screen position.

        Args:
            camera_offset: pygame.Vector2 camera translation.

        Returns:
            pygame.Vector2 screen position.
        """
        return self.position + camera_offset
