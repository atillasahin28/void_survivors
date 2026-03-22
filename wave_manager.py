"""Wave manager for spawning enemy waves.

Enemies spawn in waves at the edges of the world. Each wave
gets progressively harder by increasing the count and introducing
tougher enemy types.
"""

import pygame
import random
import math
from units.enemy import BasicEnemy, FastEnemy, TankEnemy, ShooterEnemy, BossEnemy


class WaveManager:
    """Manages enemy wave spawning and difficulty progression.

    Waves start with basic enemies and introduce new types
    as the wave number increases. A brief pause separates waves.
    """

    PAUSE_BETWEEN_WAVES = 3.0  # seconds

    def __init__(self, world_size):
        """Initialize the wave manager.

        Args:
            world_size: pygame.Vector2 with world dimensions.
        """
        self.world_size = world_size
        self.wave_number = 0
        self.enemies_remaining = 0
        self.wave_timer = 0
        self.waiting = True
        self.wave_active = False

    def update(self, dt, enemy_count):
        """Check if a new wave should start.

        Args:
            dt: Time elapsed since last frame in seconds.
            enemy_count: Current number of alive enemies.

        Returns:
            List of new enemy instances to add, or empty list.
        """
        if self.waiting:
            self.wave_timer += dt
            if self.wave_timer >= self.PAUSE_BETWEEN_WAVES:
                self.waiting = False
                self.wave_timer = 0
                self.wave_number += 1
                return self._spawn_wave()
            return []

        # If all enemies from the wave are dead, start waiting for next
        if enemy_count == 0:
            self.waiting = True
            self.wave_timer = 0

        return []

    def _spawn_wave(self):
        """Create enemies for the current wave number.

        Returns:
            List of enemy instances for this wave.
        """
        enemies = []
        n = self.wave_number

        # Basic enemies every wave
        basic_count = 3 + n
        for _ in range(basic_count):
            enemies.append(BasicEnemy(self._random_edge_position()))

        # Fast enemies from wave 2+
        if n >= 2:
            fast_count = max(1, n - 1)
            for _ in range(fast_count):
                enemies.append(FastEnemy(self._random_edge_position()))

        # Shooter enemies from wave 3+
        if n >= 3:
            shooter_count = max(1, (n - 2))
            for _ in range(shooter_count):
                enemies.append(ShooterEnemy(self._random_edge_position()))

        # Tank enemies from wave 4+
        if n >= 4:
            tank_count = max(1, (n - 3))
            for _ in range(tank_count):
                enemies.append(TankEnemy(self._random_edge_position()))

        # Boss every 5 waves
        if n % 5 == 0:
            enemies.append(BossEnemy(self._random_edge_position(), n))

        return enemies

    def _random_edge_position(self):
        """Generate a random position along the world edges.

        Returns:
            pygame.Vector2 at a random edge point.
        """
        side = random.randint(0, 3)
        margin = 30
        w, h = self.world_size.x, self.world_size.y

        if side == 0:  # top
            return pygame.Vector2(random.uniform(margin, w - margin), margin)
        elif side == 1:  # bottom
            return pygame.Vector2(random.uniform(margin, w - margin), h - margin)
        elif side == 2:  # left
            return pygame.Vector2(margin, random.uniform(margin, h - margin))
        else:  # right
            return pygame.Vector2(w - margin, random.uniform(margin, h - margin))

    def get_wave_number(self):
        """Return the current wave number.

        Returns:
            Integer wave count.
        """
        return self.wave_number

    def is_between_waves(self):
        """Check if the game is in the pause between waves.

        Returns:
            True during the inter-wave pause.
        """
        return self.waiting