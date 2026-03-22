"""Main Game class orchestrating the game loop.

The Game class manages:
- The game loop (input, update, render)
- All unit lists (player, enemies, bullets, powerups, particles)
- Collision detection between units
- Spawning powerups from killed enemies
- Game state transitions (playing, game over, restart)
"""

import pygame
import random
import time

from units.player import Player
from units.bullet import PlayerBullet, EnemyBullet
from units.enemy import BasicEnemy, FastEnemy, TankEnemy, ShooterEnemy
from units.powerup import HealthPowerUp, SpeedPowerUp, MultiShotPowerUp, PowerUpBase
from units.particle import Particle, ExplosionEffect
from camera import Camera
from wave_manager import WaveManager
from hud import HUD


class Game:
    """Main game controller managing the complete game lifecycle.

    Handles initialization, the main loop, input processing,
    physics updates, collision resolution, and rendering.
    All units are stored in categorized lists for efficient
    collision checking.
    """

    WORLD_SIZE = pygame.Vector2(1200, 900)
    BG_COLOR = (10, 10, 25)
    POWERUP_DROP_CHANCE = 0.3

    def __init__(self):
        """Initialize pygame, the display, and all game systems."""
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600), pygame.RESIZABLE)
        pygame.display.set_caption("Void Survivors")
        self.clock = pygame.time.Clock()
        self.running = True
        self._init_game_state()

    def _init_game_state(self):
        """Reset all game state for a new game."""
        self.player = Player(self.WORLD_SIZE)
        self.camera = Camera(self.screen.get_size())
        self.wave_manager = WaveManager(self.WORLD_SIZE)
        self.hud = HUD()

        # Unit lists separated by type for efficient collision checks
        self.enemies = []
        self.player_bullets = []
        self.enemy_bullets = []
        self.powerups = []
        self.particles = []

        # Game states: "title", "countdown", "playing", "game_over"
        self.state = "title"
        self.countdown_start = 0
        self.last_wave = 0

    def run(self):
        """Execute the main game loop until the player quits."""
        while self.running:
            dt = self.clock.tick(60) / 1000.0  # delta time in seconds
            self._handle_events()

            if self.state == "playing":
                self._handle_input()
                self._update(dt)
                self._check_collisions()
                self._cleanup_dead()
            elif self.state == "countdown":
                self._update_countdown()

            self._render()

        pygame.quit()

    def _handle_events(self):
        """Process pygame events (quit, resize, state transitions)."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.VIDEORESIZE:
                self.camera.resize(event.size)
            elif event.type == pygame.KEYDOWN:
                if self.state == "title":
                    if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                        self.state = "countdown"
                        self.countdown_start = time.time()
                elif self.state == "game_over":
                    if event.key == pygame.K_r:
                        self._init_game_state()
                        self.state = "countdown"
                        self.countdown_start = time.time()
                    elif event.key == pygame.K_q:
                        self.running = False

    def _update_countdown(self):
        """Check if the countdown has finished and transition to playing."""
        elapsed = time.time() - self.countdown_start
        if elapsed >= 3.0:
            self.state = "playing"

    def _handle_input(self):
        """Process keyboard and mouse input for the player."""
        keys = pygame.key.get_pressed()
        mouse_pos = pygame.mouse.get_pos()
        mouse_buttons = pygame.mouse.get_pressed()

        self.player.handle_input(keys, mouse_pos, self.camera.get_offset())

        # Shoot on left click or spacebar (held)
        if mouse_buttons[0] or keys[pygame.K_SPACE]:
            bullet_data = self.player.try_shoot()
            for pos, angle in bullet_data:
                self.player_bullets.append(PlayerBullet(pos, angle))

    def _update(self, dt):
        """Update all game systems and units.

        Args:
            dt: Time elapsed since last frame in seconds.
        """
        # Player
        self.player.update(self.WORLD_SIZE)
        self.camera.update(self.player.position)

        # Wave spawning
        new_enemies = self.wave_manager.update(dt, len(self.enemies))
        if new_enemies:
            self.enemies.extend(new_enemies)
            wave_num = self.wave_manager.get_wave_number()
            if wave_num != self.last_wave:
                self.hud.announce_wave(wave_num)
                self.last_wave = wave_num

        # Enemies
        for enemy in self.enemies:
            enemy.update(self.WORLD_SIZE, player_pos=self.player.position)
            # Collect enemy bullets from ShooterEnemy
            if isinstance(enemy, ShooterEnemy) and enemy.pending_bullets:
                for pos, angle in enemy.pending_bullets:
                    self.enemy_bullets.append(EnemyBullet(pos, angle))

        # Bullets
        for bullet in self.player_bullets:
            bullet.update(self.WORLD_SIZE)
        for bullet in self.enemy_bullets:
            bullet.update(self.WORLD_SIZE)

        # PowerUps
        for powerup in self.powerups:
            powerup.update(self.WORLD_SIZE)

        # Particles
        for particle in self.particles:
            particle.update(self.WORLD_SIZE)

    def _check_collisions(self):
        """Detect and resolve all collisions between units."""
        # Player bullets vs enemies
        for bullet in self.player_bullets:
            if not bullet.alive:
                continue
            for enemy in self.enemies:
                if not enemy.alive:
                    continue
                if bullet.collides_with(enemy):
                    enemy.take_damage(bullet.damage)
                    bullet.kill()
                    # Hit particles
                    self.particles.extend(
                        ExplosionEffect.create(bullet.position, enemy.color, count=5, speed_range=(1, 3))
                    )
                    if not enemy.alive:
                        self._on_enemy_killed(enemy)
                    break

        # Enemies vs player
        for enemy in self.enemies:
            if not enemy.alive:
                continue
            if enemy.collides_with(self.player):
                if self.player.take_damage(enemy.contact_damage):
                    self.camera.trigger_shake(10)
                    self.particles.extend(
                        ExplosionEffect.create(self.player.position, (0, 150, 255), count=8)
                    )
                    # Push enemy back
                    push_dir = enemy.position - self.player.position
                    if push_dir.length() > 0:
                        enemy.speed = push_dir.normalize() * 5
                    if not self.player.alive:
                        self._on_game_over()

        # Enemy bullets vs player
        for bullet in self.enemy_bullets:
            if not bullet.alive:
                continue
            if bullet.collides_with(self.player):
                if self.player.take_damage(bullet.damage):
                    self.camera.trigger_shake(5)
                    self.particles.extend(
                        ExplosionEffect.create(bullet.position, (255, 80, 80), count=4)
                    )
                    bullet.kill()
                    if not self.player.alive:
                        self._on_game_over()

        # Player vs powerups
        for powerup in self.powerups:
            if not powerup.alive:
                continue
            if powerup.collides_with(self.player):
                self.player.apply_powerup(powerup.get_type())
                self.particles.extend(
                    ExplosionEffect.create(powerup.position, powerup.color, count=8, speed_range=(1, 4))
                )
                powerup.kill()

    def _on_enemy_killed(self, enemy):
        """Handle enemy death: score, explosion, powerup drop.

        Args:
            enemy: The enemy that was killed.
        """
        self.player.score += enemy.score_value
        self.camera.trigger_shake(4)
        self.particles.extend(
            ExplosionEffect.create(enemy.position, enemy.color, count=15, speed_range=(2, 6))
        )
        # Random powerup drop
        if random.random() < self.POWERUP_DROP_CHANCE:
            self._spawn_powerup(enemy.position)

    def _spawn_powerup(self, position):
        """Spawn a random powerup at the given position.

        Args:
            position: pygame.Vector2 where the powerup appears.
        """
        powerup_classes = [HealthPowerUp, SpeedPowerUp, MultiShotPowerUp]
        weights = [0.5, 0.25, 0.25]
        chosen = random.choices(powerup_classes, weights=weights, k=1)[0]
        self.powerups.append(chosen(pygame.Vector2(position)))

    def _on_game_over(self):
        """Trigger the game over state with a big explosion."""
        self.state = "game_over"
        self.particles.extend(
            ExplosionEffect.create(self.player.position, (0, 200, 255), count=30, speed_range=(2, 8))
        )
        self.camera.trigger_shake(15)

    def _cleanup_dead(self):
        """Remove all dead units from their lists."""
        self.enemies = [e for e in self.enemies if e.alive]
        self.player_bullets = [b for b in self.player_bullets if b.alive]
        self.enemy_bullets = [b for b in self.enemy_bullets if b.alive]
        self.powerups = [p for p in self.powerups if p.alive]
        self.particles = [p for p in self.particles if p.alive]

    def _render(self):
        """Draw everything to the screen."""
        self.screen.fill(self.BG_COLOR)
        offset = self.camera.get_offset()

        # Draw world border
        self._draw_world_border(offset)

        # Draw background grid for visual movement feedback
        self._draw_grid(offset)

        # Draw all units in correct layer order
        for powerup in self.powerups:
            powerup.draw(self.screen, offset)
        for particle in self.particles:
            particle.draw(self.screen, offset)
        for bullet in self.player_bullets:
            bullet.draw(self.screen, offset)
        for bullet in self.enemy_bullets:
            bullet.draw(self.screen, offset)
        for enemy in self.enemies:
            enemy.draw(self.screen, offset)
        if self.player.alive:
            self.player.draw(self.screen, offset)

        # HUD (screen-space, no camera offset)
        if self.state == "title":
            self.hud.draw_title_screen(self.screen)
        elif self.state == "countdown":
            elapsed = time.time() - self.countdown_start
            self.hud.draw_countdown(self.screen, elapsed)
        elif self.state == "game_over":
            self.hud.draw_game_over(self.screen, self.player.score,
                                     self.wave_manager.get_wave_number())
        else:
            self.hud.draw(self.screen, self.player, self.wave_manager.get_wave_number())

        pygame.display.flip()

    def _draw_world_border(self, offset):
        """Draw a visible border around the world edges.

        Args:
            offset: pygame.Vector2 camera offset.
        """
        rect = pygame.Rect(offset.x, offset.y, self.WORLD_SIZE.x, self.WORLD_SIZE.y)
        pygame.draw.rect(self.screen, (60, 60, 80), rect, 3)

    def _draw_grid(self, offset):
        """Draw a subtle background grid for spatial awareness.

        Args:
            offset: pygame.Vector2 camera offset.
        """
        grid_color = (20, 20, 40)
        grid_size = 80
        screen_w, screen_h = self.screen.get_size()

        start_x = int(offset.x % grid_size)
        start_y = int(offset.y % grid_size)

        for x in range(start_x, screen_w, grid_size):
            pygame.draw.line(self.screen, grid_color, (x, 0), (x, screen_h))
        for y in range(start_y, screen_h, grid_size):
            pygame.draw.line(self.screen, grid_color, (0, y), (screen_w, y))