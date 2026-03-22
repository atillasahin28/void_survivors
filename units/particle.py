"""Particle effects for explosions and visual feedback.

Particles are short-lived units that spread outward from a point
and fade over their lifetime. ExplosionEffect is a factory that
creates a burst of particles at a given position.
"""

import pygame
import random
import math
from units.unit import Unit


class Particle(Unit):
    """A single particle that flies outward and fades.

    Used for explosion effects when enemies die or the player
    takes damage. Each particle has a limited lifetime and
    shrinks as it ages.
    """

    def __init__(self, position, speed, color, lifetime=0.5):
        """Initialize a particle.

        Args:
            position: pygame.Vector2 spawn position.
            speed: pygame.Vector2 initial velocity.
            color: RGB tuple for rendering.
            lifetime: Seconds before the particle disappears.
        """
        super().__init__(position, speed, radius=3, color=color)
        self.lifetime = lifetime
        self.max_lifetime = lifetime

    def update(self, world_size, **kwargs):
        """Move the particle and reduce its lifetime.

        The particle slows down and shrinks over time.

        Args:
            world_size: pygame.Vector2 (unused, particles ignore boundaries).
        """
        self.step()
        self.speed *= 0.95
        self.lifetime -= 1 / 60  # assumes 60 FPS
        if self.lifetime <= 0:
            self.kill()

    def draw(self, surface, camera_offset):
        """Draw the particle with fading opacity effect.

        As the particle ages, it shrinks and its color fades.

        Args:
            surface: pygame.Surface to draw on.
            camera_offset: pygame.Vector2 camera translation.
        """
        screen = self.screen_pos(camera_offset)
        ratio = max(0, self.lifetime / self.max_lifetime)
        r = max(1, int(self.radius * ratio))
        faded_color = (
            int(self.color[0] * ratio),
            int(self.color[1] * ratio),
            int(self.color[2] * ratio),
        )
        pygame.draw.circle(surface, faded_color, screen, r)


class ExplosionEffect:
    """Factory that creates a burst of particles at a position.

    Call `create()` to get a list of Particle objects that can
    be added to the game's unit list.
    """

    @staticmethod
    def create(position, color=(255, 100, 50), count=12, speed_range=(1, 5)):
        """Generate an explosion burst of particles.

        Args:
            position: pygame.Vector2 center of the explosion.
            color: Base RGB color for the particles (varied slightly).
            count: Number of particles to create.
            speed_range: Tuple (min_speed, max_speed) for particle velocity.

        Returns:
            List of Particle instances.
        """
        particles = []
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed_mag = random.uniform(*speed_range)
            speed = pygame.Vector2(
                math.cos(angle) * speed_mag,
                math.sin(angle) * speed_mag
            )
            # Vary the color slightly for visual interest
            varied_color = (
                min(255, max(0, color[0] + random.randint(-30, 30))),
                min(255, max(0, color[1] + random.randint(-30, 30))),
                min(255, max(0, color[2] + random.randint(-30, 30))),
            )
            lifetime = random.uniform(0.3, 0.7)
            particles.append(Particle(
                pygame.Vector2(position), speed, varied_color, lifetime
            ))
        return particles
