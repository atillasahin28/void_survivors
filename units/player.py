"""Player unit controlled by the user.

The player moves with WASD/arrow keys, aims with the mouse,
and shoots with left-click or spacebar. The player has health,
and can pick up powerups for temporary boosts.
"""

import pygame
import math
import time
from units.unit import Unit


class Player(Unit):
    """The player-controlled unit.

    Attributes:
        health: Current hit points (0 = dead).
        max_health: Maximum hit points.
        score: Points earned from killing enemies.
        speed_boost_end: Timestamp when speed boost expires.
        multi_shot_end: Timestamp when multi-shot expires.
    """

    MAX_HEALTH = 100
    ACCELERATION = 0.6
    FRICTION = 0.92
    SHOOT_COOLDOWN = 0.15
    INVINCIBILITY_TIME = 1.0  # seconds of invincibility after taking damage

    def __init__(self, world_size):
        """Initialize the player at the center of the world.

        Args:
            world_size: pygame.Vector2 with world dimensions.
        """
        position = pygame.Vector2(world_size.x / 2, world_size.y / 2)
        super().__init__(position, pygame.Vector2(0, 0), radius=18, color=(0, 200, 255))
        self.health = self.MAX_HEALTH
        self.max_health = self.MAX_HEALTH
        self.score = 0
        self.last_shoot_time = 0
        self.last_hit_time = 0
        self.aim_angle = 0
        self.speed_boost_end = 0
        self.multi_shot_end = 0
        self.trail_positions = []

    def update(self, world_size, **kwargs):
        """Update player movement and trail.

        Args:
            world_size: pygame.Vector2 with world dimensions.
        """
        self.step()
        self.speed *= self.FRICTION
        self.stay_on_screen(world_size)
        self.trail_positions.append(pygame.Vector2(self.position))
        if len(self.trail_positions) > 12:
            self.trail_positions.pop(0)

    def handle_input(self, keys, mouse_pos, camera_offset):
        """Process keyboard input for movement and update aim angle.

        Args:
            keys: pygame.key.get_pressed() result.
            mouse_pos: Tuple (x, y) of mouse screen position.
            camera_offset: pygame.Vector2 camera translation.
        """
        accel = self.ACCELERATION
        if time.time() < self.speed_boost_end:
            accel *= 1.6

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.speed.x -= accel
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.speed.x += accel
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.speed.y -= accel
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.speed.y += accel

        screen_pos = self.screen_pos(camera_offset)
        dx = mouse_pos[0] - screen_pos.x
        dy = mouse_pos[1] - screen_pos.y
        self.aim_angle = math.atan2(dy, dx)

    def try_shoot(self):
        """Attempt to fire bullets if cooldown has elapsed.

        Returns:
            List of (position, angle) tuples for new bullets, or empty list.
        """
        now = time.time()
        if now - self.last_shoot_time < self.SHOOT_COOLDOWN:
            return []
        self.last_shoot_time = now

        offset = pygame.Vector2(
            math.cos(self.aim_angle) * self.radius,
            math.sin(self.aim_angle) * self.radius
        )
        origin = self.position + offset

        if time.time() < self.multi_shot_end:
            spread = 0.15  # radians
            return [
                (pygame.Vector2(origin), self.aim_angle - spread),
                (pygame.Vector2(origin), self.aim_angle),
                (pygame.Vector2(origin), self.aim_angle + spread),
            ]
        return [(pygame.Vector2(origin), self.aim_angle)]

    def take_damage(self, amount):
        """Reduce health if not invincible.

        Args:
            amount: Damage points to subtract.

        Returns:
            True if damage was applied, False if invincible.
        """
        now = time.time()
        if now - self.last_hit_time < self.INVINCIBILITY_TIME:
            return False
        self.health -= amount
        self.last_hit_time = now
        if self.health <= 0:
            self.health = 0
            self.kill()
        return True

    @property
    def is_invincible(self):
        """Check if player is currently invincible after a hit."""
        return time.time() - self.last_hit_time < self.INVINCIBILITY_TIME

    def draw(self, surface, camera_offset):
        """Draw the player with trail, aim indicator, and health bar.

        The player blinks when invincible. A colored trail follows movement.
        An aim line shows the current mouse direction.

        Args:
            surface: pygame.Surface to draw on.
            camera_offset: pygame.Vector2 camera translation.
        """
        # Draw trail
        for i, pos in enumerate(self.trail_positions):
            alpha = (i + 1) / len(self.trail_positions) if self.trail_positions else 1
            trail_color = (
                int(0 * alpha),
                int(150 * alpha),
                int(255 * alpha)
            )
            trail_radius = max(2, int(self.radius * 0.4 * alpha))
            screen = pos + camera_offset
            pygame.draw.circle(surface, trail_color, screen, trail_radius)

        screen = self.screen_pos(camera_offset)

        # Blink effect when invincible
        if self.is_invincible and int(time.time() * 10) % 2 == 0:
            return

        # Player body
        pygame.draw.circle(surface, self.color, screen, self.radius, 3)
        inner_color = (0, 120, 200)
        pygame.draw.circle(surface, inner_color, screen, self.radius - 4)

        # Aim indicator line
        aim_end = screen + pygame.Vector2(
            math.cos(self.aim_angle) * (self.radius + 14),
            math.sin(self.aim_angle) * (self.radius + 14)
        )
        pygame.draw.line(surface, (255, 255, 100), screen, aim_end, 2)

        # Health bar above player
        bar_width = 36
        bar_height = 4
        bar_x = screen.x - bar_width / 2
        bar_y = screen.y - self.radius - 10
        health_ratio = self.health / self.max_health
        pygame.draw.rect(surface, (80, 0, 0), (bar_x, bar_y, bar_width, bar_height))
        bar_color = (0, 220, 0) if health_ratio > 0.5 else (220, 220, 0) if health_ratio > 0.25 else (220, 0, 0)
        pygame.draw.rect(surface, bar_color, (bar_x, bar_y, bar_width * health_ratio, bar_height))

    def apply_powerup(self, powerup_type):
        """Apply a powerup effect to the player.

        Args:
            powerup_type: String identifier ('health', 'speed', 'multishot').
        """
        now = time.time()
        if powerup_type == "health":
            self.health = min(self.max_health, self.health + 30)
        elif powerup_type == "speed":
            self.speed_boost_end = now + 6.0
        elif powerup_type == "multishot":
            self.multi_shot_end = now + 8.0
