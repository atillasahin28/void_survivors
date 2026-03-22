"""Enemy unit types with distinct behaviors.

Four enemy types demonstrate polymorphism: each inherits from Unit
and implements unique movement, attack patterns, and visuals.

- BasicEnemy: Drifts toward the player at moderate speed.
- FastEnemy: Quick but fragile, zigzags toward the player.
- TankEnemy: Slow, large, and high health.
- ShooterEnemy: Keeps distance and fires bullets at the player.
"""

import pygame
import math
import time
import random
from units.unit import Unit


class BasicEnemy(Unit):
    """A standard enemy that homes in on the player.

    Moderate speed and health. The most common enemy type.
    Awards 10 points on kill.
    """

    def __init__(self, position):
        """Initialize a BasicEnemy.

        Args:
            position: pygame.Vector2 spawn position.
        """
        super().__init__(position, pygame.Vector2(0, 0), radius=14, color=(255, 60, 60))
        self.health = 50
        self.max_speed = 2.0
        self.score_value = 10
        self.contact_damage = 15

    def update(self, world_size, **kwargs):
        """Steer toward the player and move.

        Args:
            world_size: pygame.Vector2 with world dimensions.
            **kwargs: Must contain 'player_pos' as pygame.Vector2.
        """
        player_pos = kwargs.get("player_pos")
        if player_pos:
            direction = player_pos - self.position
            if direction.length() > 0:
                direction = direction.normalize() * self.max_speed
                self.speed += (direction - self.speed) * 0.05
        self.step()
        self.stay_on_screen(world_size)

    def take_damage(self, amount):
        """Reduce health by given amount, kill if depleted.

        Args:
            amount: Damage to apply.
        """
        self.health -= amount
        if self.health <= 0:
            self.kill()

    def draw(self, surface, camera_offset):
        """Draw as a red circle with an inner ring.

        Args:
            surface: pygame.Surface to draw on.
            camera_offset: pygame.Vector2 camera translation.
        """
        screen = self.screen_pos(camera_offset)
        pygame.draw.circle(surface, self.color, screen, self.radius)
        pygame.draw.circle(surface, (180, 30, 30), screen, self.radius - 4)
        self._draw_health_bar(surface, screen)

    def _draw_health_bar(self, surface, screen_pos):
        """Draw a small health bar above the enemy.

        Args:
            surface: pygame.Surface to draw on.
            screen_pos: pygame.Vector2 screen position.
        """
        bar_w = self.radius * 2
        bar_h = 3
        x = screen_pos.x - bar_w / 2
        y = screen_pos.y - self.radius - 8
        max_hp = self._get_max_health()
        ratio = max(0, self.health / max_hp)
        pygame.draw.rect(surface, (60, 0, 0), (x, y, bar_w, bar_h))
        pygame.draw.rect(surface, (220, 50, 50), (x, y, bar_w * ratio, bar_h))

    def _get_max_health(self):
        """Return the initial max health for health bar display."""
        return 50


class FastEnemy(Unit):
    """A fast, fragile enemy that zigzags toward the player.

    Low health but high speed. Changes direction periodically
    to create an unpredictable zigzag pattern.
    Awards 15 points on kill.
    """

    def __init__(self, position):
        """Initialize a FastEnemy.

        Args:
            position: pygame.Vector2 spawn position.
        """
        super().__init__(position, pygame.Vector2(0, 0), radius=10, color=(255, 165, 0))
        self.health = 25
        self.max_speed = 4.0
        self.score_value = 15
        self.contact_damage = 10
        self.zigzag_timer = 0
        self.zigzag_offset = 0

    def update(self, world_size, **kwargs):
        """Zigzag toward the player with periodic lateral shifts.

        Args:
            world_size: pygame.Vector2 with world dimensions.
            **kwargs: Must contain 'player_pos' as pygame.Vector2.
        """
        player_pos = kwargs.get("player_pos")
        if player_pos:
            direction = player_pos - self.position
            if direction.length() > 0:
                direction = direction.normalize()
                # Perpendicular zigzag offset
                self.zigzag_timer += 1
                if self.zigzag_timer % 30 == 0:
                    self.zigzag_offset = random.choice([-1, 1])
                perp = pygame.Vector2(-direction.y, direction.x) * self.zigzag_offset * 1.5
                target_speed = (direction * self.max_speed) + perp
                self.speed += (target_speed - self.speed) * 0.1
        self.step()
        self.stay_on_screen(world_size)

    def take_damage(self, amount):
        """Reduce health; kill if depleted.

        Args:
            amount: Damage to apply.
        """
        self.health -= amount
        if self.health <= 0:
            self.kill()

    def draw(self, surface, camera_offset):
        """Draw as an orange diamond shape.

        Args:
            surface: pygame.Surface to draw on.
            camera_offset: pygame.Vector2 camera translation.
        """
        screen = self.screen_pos(camera_offset)
        r = self.radius
        points = [
            (screen.x, screen.y - r),
            (screen.x + r, screen.y),
            (screen.x, screen.y + r),
            (screen.x - r, screen.y),
        ]
        pygame.draw.polygon(surface, self.color, points)
        pygame.draw.polygon(surface, (200, 120, 0), points, 2)

    def _get_max_health(self):
        return 25


class TankEnemy(Unit):
    """A slow, heavily-armored enemy.

    Large radius, high health, low speed. Relentlessly pushes
    toward the player. Awards 25 points on kill.
    """

    def __init__(self, position):
        """Initialize a TankEnemy.

        Args:
            position: pygame.Vector2 spawn position.
        """
        super().__init__(position, pygame.Vector2(0, 0), radius=24, color=(150, 50, 200))
        self.health = 225
        self.max_speed = 1.0
        self.score_value = 25
        self.contact_damage = 25

    def update(self, world_size, **kwargs):
        """Slowly pursue the player.

        Args:
            world_size: pygame.Vector2 with world dimensions.
            **kwargs: Must contain 'player_pos' as pygame.Vector2.
        """
        player_pos = kwargs.get("player_pos")
        if player_pos:
            direction = player_pos - self.position
            if direction.length() > 0:
                direction = direction.normalize() * self.max_speed
                self.speed += (direction - self.speed) * 0.03
        self.step()
        self.stay_on_screen(world_size)

    def take_damage(self, amount):
        """Reduce health; kill if depleted.

        Args:
            amount: Damage to apply.
        """
        self.health -= amount
        if self.health <= 0:
            self.kill()

    def draw(self, surface, camera_offset):
        """Draw as a large purple circle with armor ring.

        Args:
            surface: pygame.Surface to draw on.
            camera_offset: pygame.Vector2 camera translation.
        """
        screen = self.screen_pos(camera_offset)
        pygame.draw.circle(surface, self.color, screen, self.radius)
        pygame.draw.circle(surface, (100, 30, 160), screen, self.radius - 6)
        pygame.draw.circle(surface, (200, 100, 255), screen, self.radius, 3)
        # Health bar
        bar_w = self.radius * 2
        bar_h = 4
        x = screen.x - bar_w / 2
        y = screen.y - self.radius - 10
        ratio = max(0, self.health / 225)
        pygame.draw.rect(surface, (60, 0, 0), (x, y, bar_w, bar_h))
        pygame.draw.rect(surface, (180, 80, 220), (x, y, bar_w * ratio, bar_h))

    def _get_max_health(self):
        return 225


class ShooterEnemy(Unit):
    """An enemy that keeps distance and shoots at the player.

    Maintains a preferred distance and fires EnemyBullet projectiles
    periodically. Awards 20 points on kill.
    """

    PREFERRED_DISTANCE = 250
    SHOOT_COOLDOWN = 1.5

    def __init__(self, position):
        """Initialize a ShooterEnemy.

        Args:
            position: pygame.Vector2 spawn position.
        """
        super().__init__(position, pygame.Vector2(0, 0), radius=16, color=(0, 255, 150))
        self.health = 40
        self.max_speed = 1.5
        self.score_value = 20
        self.contact_damage = 10
        self.last_shoot_time = time.time() + random.uniform(0, 1)
        self.pending_bullets = []

    def update(self, world_size, **kwargs):
        """Maintain distance from the player and shoot periodically.

        Bullets are queued in `pending_bullets` for the game loop to spawn.

        Args:
            world_size: pygame.Vector2 with world dimensions.
            **kwargs: Must contain 'player_pos' as pygame.Vector2.
        """
        player_pos = kwargs.get("player_pos")
        self.pending_bullets = []
        if player_pos:
            direction = player_pos - self.position
            dist = direction.length()
            if dist > 0:
                norm = direction.normalize()
                # Move toward preferred distance
                if dist > self.PREFERRED_DISTANCE + 30:
                    target = norm * self.max_speed
                elif dist < self.PREFERRED_DISTANCE - 30:
                    target = -norm * self.max_speed
                else:
                    # Orbit sideways
                    perp = pygame.Vector2(-norm.y, norm.x)
                    target = perp * self.max_speed * 0.8
                self.speed += (target - self.speed) * 0.05

                # Shoot
                now = time.time()
                if now - self.last_shoot_time > self.SHOOT_COOLDOWN:
                    angle = math.atan2(direction.y, direction.x)
                    bullet_pos = self.position + norm * self.radius
                    self.pending_bullets.append((pygame.Vector2(bullet_pos), angle))
                    self.last_shoot_time = now

        self.step()
        self.stay_on_screen(world_size)

    def take_damage(self, amount):
        """Reduce health; kill if depleted.

        Args:
            amount: Damage to apply.
        """
        self.health -= amount
        if self.health <= 0:
            self.kill()

    def draw(self, surface, camera_offset):
        """Draw as a green hexagon shape.

        Args:
            surface: pygame.Surface to draw on.
            camera_offset: pygame.Vector2 camera translation.
        """
        screen = self.screen_pos(camera_offset)
        r = self.radius
        points = []
        for i in range(6):
            angle = math.pi / 6 + i * math.pi / 3
            points.append((
                screen.x + r * math.cos(angle),
                screen.y + r * math.sin(angle),
            ))
        pygame.draw.polygon(surface, self.color, points)
        pygame.draw.polygon(surface, (0, 180, 100), points, 2)
        # Health bar
        bar_w = self.radius * 2
        bar_h = 3
        x = screen.x - bar_w / 2
        y = screen.y - self.radius - 8
        ratio = max(0, self.health / 40)
        pygame.draw.rect(surface, (60, 0, 0), (x, y, bar_w, bar_h))
        pygame.draw.rect(surface, (0, 200, 120), (x, y, bar_w * ratio, bar_h))

    def _get_max_health(self):
        return 40


class BossEnemy(Unit):
    """A powerful boss that spawns every 5 waves.

    Alternates between two phases:
    - CHASE: Charges directly at the player at increasing speed.
    - SHOOT: Stops and fires a spread of bullets in all directions.

    Large, high health, with a spinning visual and a wide health bar.
    Awards 100 points on kill.
    """

    CHASE_DURATION = 3.0
    SHOOT_DURATION = 2.0
    SPREAD_COOLDOWN = 0.4

    def __init__(self, position, wave_number):
        """Initialize a BossEnemy that scales with the wave number.

        Args:
            position: pygame.Vector2 spawn position.
            wave_number: Current wave number (used to scale health).
        """
        super().__init__(position, pygame.Vector2(0, 0), radius=40, color=(255, 50, 50))
        base_health = 400
        self.health = base_health + (wave_number * 50)
        self.max_health = self.health
        self.max_speed = 2.5
        self.score_value = 100
        self.contact_damage = 35

        # Phase system: alternates between chasing and shooting
        self.phase = "chase"
        self.phase_timer = 0
        self.spin_angle = 0
        self.last_spread_time = 0
        self.pending_bullets = []

    def update(self, world_size, **kwargs):
        """Alternate between chasing the player and shooting spreads.

        During CHASE phase, the boss accelerates toward the player.
        During SHOOT phase, the boss stops and fires bullet rings.

        Args:
            world_size: pygame.Vector2 with world dimensions.
            **kwargs: Must contain 'player_pos' as pygame.Vector2.
        """
        player_pos = kwargs.get("player_pos")
        self.pending_bullets = []
        self.phase_timer += 1 / 60  # assumes 60 FPS
        self.spin_angle += 0.05

        if self.phase == "chase":
            self._do_chase(player_pos)
            if self.phase_timer >= self.CHASE_DURATION:
                self.phase = "shoot"
                self.phase_timer = 0
                self.speed *= 0.1  # brake hard
        elif self.phase == "shoot":
            self._do_shoot(player_pos)
            self.speed *= 0.9  # slow to a stop
            if self.phase_timer >= self.SHOOT_DURATION:
                self.phase = "chase"
                self.phase_timer = 0

        self.step()
        self.stay_on_screen(world_size)

    def _do_chase(self, player_pos):
        """Accelerate toward the player.

        Args:
            player_pos: pygame.Vector2 of the player's position.
        """
        if player_pos:
            direction = player_pos - self.position
            if direction.length() > 0:
                target = direction.normalize() * self.max_speed
                self.speed += (target - self.speed) * 0.06

    def _do_shoot(self, player_pos):
        """Fire a ring of bullets outward at regular intervals.

        Args:
            player_pos: pygame.Vector2 of the player's position (unused,
                        boss shoots in all directions).
        """
        now = time.time()
        if now - self.last_spread_time >= self.SPREAD_COOLDOWN:
            self.last_spread_time = now
            num_bullets = 10
            for i in range(num_bullets):
                angle = self.spin_angle + (2 * math.pi * i / num_bullets)
                bullet_pos = self.position + pygame.Vector2(
                    math.cos(angle) * self.radius,
                    math.sin(angle) * self.radius
                )
                self.pending_bullets.append((pygame.Vector2(bullet_pos), angle))

    def take_damage(self, amount):
        """Reduce health; kill if depleted.

        Args:
            amount: Damage to apply.
        """
        self.health -= amount
        if self.health <= 0:
            self.kill()

    def draw(self, surface, camera_offset):
        """Draw as a large spinning spiky circle with a glowing core.

        The boss has an outer ring of spikes that rotates, an inner
        core that pulses, and a wide health bar underneath.

        Args:
            surface: pygame.Surface to draw on.
            camera_offset: pygame.Vector2 camera translation.
        """
        screen = self.screen_pos(camera_offset)

        # Outer spikes (rotating)
        num_spikes = 8
        for i in range(num_spikes):
            angle = self.spin_angle + (2 * math.pi * i / num_spikes)
            inner_point = screen + pygame.Vector2(
                math.cos(angle) * (self.radius - 8),
                math.sin(angle) * (self.radius - 8)
            )
            outer_point = screen + pygame.Vector2(
                math.cos(angle) * (self.radius + 12),
                math.sin(angle) * (self.radius + 12)
            )
            spike_color = (255, 100, 100) if self.phase == "chase" else (255, 200, 50)
            pygame.draw.line(surface, spike_color, inner_point, outer_point, 3)

        # Outer ring
        ring_color = (200, 30, 30) if self.phase == "chase" else (200, 160, 30)
        pygame.draw.circle(surface, ring_color, screen, self.radius, 4)

        # Inner core (pulses)
        pulse = 0.8 + 0.2 * math.sin(time.time() * 6)
        core_radius = int((self.radius - 10) * pulse)
        core_color = (180, 20, 20) if self.phase == "chase" else (180, 140, 20)
        pygame.draw.circle(surface, core_color, screen, core_radius)

        # Inner eye
        pygame.draw.circle(surface, (255, 255, 200), screen, 8)
        pygame.draw.circle(surface, (60, 0, 0), screen, 4)

        # Wide health bar below the boss
        bar_w = self.radius * 3
        bar_h = 6
        x = screen.x - bar_w / 2
        y = screen.y + self.radius + 10
        ratio = max(0, self.health / self.max_health)
        pygame.draw.rect(surface, (40, 0, 0), (x - 1, y - 1, bar_w + 2, bar_h + 2))
        pygame.draw.rect(surface, (80, 0, 0), (x, y, bar_w, bar_h))
        bar_color = (255, 50, 50) if ratio > 0.5 else (255, 150, 0) if ratio > 0.25 else (255, 255, 0)
        pygame.draw.rect(surface, bar_color, (x, y, bar_w * ratio, bar_h))

        # "BOSS" label above
        font = pygame.font.SysFont("Arial", 14, bold=True)
        label = font.render("BOSS", True, (255, 80, 80))
        surface.blit(label, (screen.x - label.get_width() / 2, screen.y - self.radius - 20))

    def _get_max_health(self):
        return self.max_health