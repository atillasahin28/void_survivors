"""Multiplayer server for Void Survivors.

Runs the game logic server-side with proper state management:
- LOBBY: Players join, everyone sees who's connected, press SPACE to ready up.
         Game starts when all players are ready.
- COUNTDOWN: 3-2-1-GO countdown before gameplay begins.
- PLAYING: Full game with waves, enemies, powerups.
- GAME_OVER: All players dead. Press R to restart.

Usage:
    python mp_server.py [port] [host]
    python mp_server.py 2345
    python mp_server.py 2345 0.0.0.0
"""

import sys
import zmq
import time
import math
import random
import pygame

from mp_action import Action
from units.player import Player
from units.bullet import PlayerBullet, EnemyBullet
from units.enemy import BasicEnemy, FastEnemy, TankEnemy, ShooterEnemy, BossEnemy
from units.powerup import HealthPowerUp, SpeedPowerUp, MultiShotPowerUp
from units.particle import ExplosionEffect
from wave_manager import WaveManager


class ServerGame:
    """Server-side game state managing all units, logic, and game phases.

    Handles lobby, countdown, gameplay, and game over transitions.
    Processes player actions and produces snapshots for clients.
    """

    WORLD_SIZE = pygame.Vector2(1200, 900)
    POWERUP_DROP_CHANCE = 0.3
    COUNTDOWN_DURATION = 3.0

    def __init__(self):
        """Initialize the server game state."""
        self._reset()

    def _reset(self):
        """Reset all game state for a fresh game (or restart)."""
        self.state = "lobby"
        self.players = {}
        self.ready_players = set()
        self.enemies = []
        self.player_bullets = []
        self.enemy_bullets = []
        self.powerups = []
        self.particles = []
        self.wave_manager = WaveManager(self.WORLD_SIZE)
        self.wave_number = 0
        self.countdown_start = 0

    def add_player(self, name):
        """Add a new player to the game.

        Args:
            name: Unique player name string.
        """
        if name not in self.players and name != "_":
            player = Player(self.WORLD_SIZE)
            offset = len(self.players) * 80
            player.position.x += offset - 40 * len(self.players)
            self.players[name] = player
            print(f"Player '{name}' joined. ({len(self.players)} players)")

    def apply_action(self, action):
        """Apply a client's action depending on the current game state.

        Args:
            action: Action object with player input.
        """
        name = action.name
        if name == "_":
            return

        # Always allow joining
        if name not in self.players:
            self.add_player(name)

        if self.state == "lobby":
            if action.ready:
                self.ready_players.add(name)
                print(f"Player '{name}' is ready. ({len(self.ready_players)}/{len(self.players)})")

        elif self.state == "playing":
            player = self.players[name]
            if not player.alive:
                return

            accel = Player.ACCELERATION
            if time.time() < player.speed_boost_end:
                accel *= 1.6
            player.speed.x += action.accel_x * accel
            player.speed.y += action.accel_y * accel
            player.aim_angle = action.aim_angle

            if action.shooting:
                bullet_data = player.try_shoot()
                for pos, angle in bullet_data:
                    self.player_bullets.append(PlayerBullet(pos, angle))

        elif self.state == "game_over":
            if action.restart:
                self._restart_game()

    def _restart_game(self):
        """Restart the game keeping the same players."""
        player_names = list(self.players.keys())
        self._reset()
        for name in player_names:
            self.add_player(name)
            self.ready_players.add(name)
        self.state = "countdown"
        self.countdown_start = time.time()
        print("Game restarting!")

    def update(self):
        """Run one frame of game logic based on current state."""
        if self.state == "lobby":
            # Start countdown when we have players and all are ready
            if len(self.players) > 0 and len(self.ready_players) >= len(self.players):
                self.state = "countdown"
                self.countdown_start = time.time()
                print("All players ready! Starting countdown...")

        elif self.state == "countdown":
            elapsed = time.time() - self.countdown_start
            if elapsed >= self.COUNTDOWN_DURATION:
                self.state = "playing"
                print("Game started!")

        elif self.state == "playing":
            self._update_gameplay()
            # Check if all players are dead
            alive = [p for p in self.players.values() if p.alive]
            if len(alive) == 0 and len(self.players) > 0:
                self.state = "game_over"
                print("All players dead. Game over!")

        elif self.state == "game_over":
            # Still update particles so death explosion plays out
            for particle in self.particles:
                particle.update(self.WORLD_SIZE)
            self.particles = [p for p in self.particles if p.alive]

    def _update_gameplay(self):
        """Run one frame of actual gameplay logic."""
        dt = 1 / 60

        # Update players
        for name, player in self.players.items():
            if player.alive:
                player.update(self.WORLD_SIZE)

        # Wave spawning
        new_enemies = self.wave_manager.update(dt, len(self.enemies))
        if new_enemies:
            self.enemies.extend(new_enemies)
            self.wave_number = self.wave_manager.get_wave_number()

        # Find alive players for enemy targeting
        alive_players = [p for p in self.players.values() if p.alive]

        # Update enemies
        for enemy in self.enemies:
            target = self._nearest_player(enemy.position, alive_players)
            enemy.update(self.WORLD_SIZE, player_pos=target)
            if hasattr(enemy, "pending_bullets") and enemy.pending_bullets:
                for pos, angle in enemy.pending_bullets:
                    self.enemy_bullets.append(EnemyBullet(pos, angle))

        # Update bullets
        for bullet in self.player_bullets:
            bullet.update(self.WORLD_SIZE)
        for bullet in self.enemy_bullets:
            bullet.update(self.WORLD_SIZE)

        # Update powerups and particles
        for powerup in self.powerups:
            powerup.update(self.WORLD_SIZE)
        for particle in self.particles:
            particle.update(self.WORLD_SIZE)

        # Collisions
        self._check_collisions()
        self._cleanup_dead()

    def _nearest_player(self, position, alive_players):
        """Find the closest alive player for enemy targeting.

        Args:
            position: pygame.Vector2 of the enemy.
            alive_players: List of alive Player instances.

        Returns:
            pygame.Vector2 of nearest player, or world center.
        """
        if not alive_players:
            return pygame.Vector2(self.WORLD_SIZE.x / 2, self.WORLD_SIZE.y / 2)
        nearest = min(alive_players, key=lambda p: position.distance_to(p.position))
        return nearest.position

    def _check_collisions(self):
        """Detect and resolve collisions between all units."""
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
                    self.particles.extend(
                        ExplosionEffect.create(bullet.position, enemy.color, count=5, speed_range=(1, 3))
                    )
                    if not enemy.alive:
                        self._on_enemy_killed(enemy)
                    break

        # Enemies vs players
        for enemy in self.enemies:
            if not enemy.alive:
                continue
            for name, player in self.players.items():
                if not player.alive:
                    continue
                if enemy.collides_with(player):
                    player.take_damage(enemy.contact_damage)
                    push_dir = enemy.position - player.position
                    if push_dir.length() > 0:
                        enemy.speed = push_dir.normalize() * 5
                    self.particles.extend(
                        ExplosionEffect.create(player.position, (0, 150, 255), count=8)
                    )
                    if not player.alive:
                        self.particles.extend(
                            ExplosionEffect.create(player.position, (0, 200, 255), count=30, speed_range=(2, 8))
                        )

        # Enemy bullets vs players
        for bullet in self.enemy_bullets:
            if not bullet.alive:
                continue
            for name, player in self.players.items():
                if not player.alive:
                    continue
                if bullet.collides_with(player):
                    player.take_damage(bullet.damage)
                    bullet.kill()
                    self.particles.extend(
                        ExplosionEffect.create(bullet.position, (255, 80, 80), count=4)
                    )

        # Players vs powerups
        for powerup in self.powerups:
            if not powerup.alive:
                continue
            for name, player in self.players.items():
                if not player.alive:
                    continue
                if powerup.collides_with(player):
                    player.apply_powerup(powerup.get_type())
                    self.particles.extend(
                        ExplosionEffect.create(powerup.position, powerup.color, count=8)
                    )
                    powerup.kill()
                    break

    def _on_enemy_killed(self, enemy):
        """Handle enemy death: score, effects, powerup.

        Args:
            enemy: The enemy that was killed.
        """
        for name, player in self.players.items():
            if player.alive:
                player.score += enemy.score_value

        if isinstance(enemy, BossEnemy):
            self.particles.extend(
                ExplosionEffect.create(enemy.position, (255, 100, 50), count=40, speed_range=(3, 10))
            )
            self._spawn_powerup(enemy.position)
        else:
            self.particles.extend(
                ExplosionEffect.create(enemy.position, enemy.color, count=15, speed_range=(2, 6))
            )
            if random.random() < self.POWERUP_DROP_CHANCE:
                self._spawn_powerup(enemy.position)

    def _spawn_powerup(self, position):
        """Spawn a random powerup at the given position.

        Args:
            position: pygame.Vector2 spawn location.
        """
        choices = [HealthPowerUp, SpeedPowerUp, MultiShotPowerUp]
        weights = [0.5, 0.25, 0.25]
        chosen = random.choices(choices, weights=weights, k=1)[0]
        self.powerups.append(chosen(pygame.Vector2(position)))

    def _cleanup_dead(self):
        """Remove dead units from all lists."""
        self.enemies = [e for e in self.enemies if e.alive]
        self.player_bullets = [b for b in self.player_bullets if b.alive]
        self.enemy_bullets = [b for b in self.enemy_bullets if b.alive]
        self.powerups = [p for p in self.powerups if p.alive]
        self.particles = [p for p in self.particles if p.alive]

    def get_snapshot(self):
        """Build a picklable snapshot of the entire game state.

        Returns:
            Dict containing all data needed to render the game.
        """
        units = []

        # Players
        for name, player in self.players.items():
            units.append({
                "type": "player",
                "x": player.position.x,
                "y": player.position.y,
                "radius": player.radius,
                "color": player.color,
                "health": player.health,
                "max_health": player.max_health,
                "name": name,
                "aim_angle": player.aim_angle,
                "trail": [(p.x, p.y) for p in player.trail_positions],
                "is_invincible": player.is_invincible,
                "alive": player.alive,
            })

        # Enemies
        for enemy in self.enemies:
            data = {
                "x": enemy.position.x,
                "y": enemy.position.y,
                "radius": enemy.radius,
                "color": enemy.color,
                "health": enemy.health,
                "max_health": enemy._get_max_health(),
            }
            if isinstance(enemy, BasicEnemy):
                data["type"] = "basic_enemy"
            elif isinstance(enemy, FastEnemy):
                data["type"] = "fast_enemy"
            elif isinstance(enemy, TankEnemy):
                data["type"] = "tank_enemy"
            elif isinstance(enemy, BossEnemy):
                data["type"] = "boss_enemy"
                data["phase"] = enemy.phase
                data["spin_angle"] = enemy.spin_angle
            elif isinstance(enemy, ShooterEnemy):
                data["type"] = "shooter_enemy"
            units.append(data)

        # Bullets
        for bullet in self.player_bullets:
            units.append({
                "type": "player_bullet",
                "x": bullet.position.x, "y": bullet.position.y,
                "radius": bullet.radius, "color": bullet.color,
            })
        for bullet in self.enemy_bullets:
            units.append({
                "type": "enemy_bullet",
                "x": bullet.position.x, "y": bullet.position.y,
                "radius": bullet.radius, "color": bullet.color,
            })

        # Powerups
        for powerup in self.powerups:
            units.append({
                "type": "powerup_" + powerup.get_type(),
                "x": powerup.position.x, "y": powerup.position.y,
                "radius": powerup.radius, "color": powerup.color,
                "pulse_phase": powerup.pulse_phase,
            })

        # Particles
        for particle in self.particles:
            if particle.alive:
                ratio = max(0, particle.lifetime / particle.max_lifetime)
                units.append({
                    "type": "particle",
                    "x": particle.position.x, "y": particle.position.y,
                    "radius": max(1, int(particle.radius * ratio)),
                    "color": (
                        int(particle.color[0] * ratio),
                        int(particle.color[1] * ratio),
                        int(particle.color[2] * ratio),
                    ),
                })

        # Player scores
        scores = {}
        for name, player in self.players.items():
            scores[name] = {
                "score": player.score,
                "health": player.health,
                "max_health": player.max_health,
                "alive": player.alive,
                "speed_boost_end": player.speed_boost_end,
                "multi_shot_end": player.multi_shot_end,
            }

        # Countdown remaining
        countdown_remaining = 0
        if self.state == "countdown":
            countdown_remaining = max(0, self.COUNTDOWN_DURATION - (time.time() - self.countdown_start))

        return {
            "state": self.state,
            "world_size": (self.WORLD_SIZE.x, self.WORLD_SIZE.y),
            "wave_number": self.wave_number,
            "units": units,
            "scores": scores,
            "player_names": list(self.players.keys()),
            "ready_players": list(self.ready_players),
            "countdown_remaining": countdown_remaining,
        }


def main(port, host):
    """Run the multiplayer server.

    Args:
        port: Port number to listen on.
        host: Host address to bind to.
    """
    pygame.init()
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind(f"tcp://{host}:{port}")
    print(f"Void Survivors server running on {host}:{port}")
    print("Waiting for players to connect...")

    game = ServerGame()
    prev_time = time.time()
    game_fps = 60

    while True:
        try:
            action = socket.recv_pyobj(flags=zmq.NOBLOCK)
            game.apply_action(action)
            socket.send_pyobj(game.get_snapshot())
        except zmq.ZMQError:
            time.sleep(0.0005)

        current_time = time.time()
        if current_time - prev_time > 1 / game_fps:
            prev_time = current_time
            game.update()


if __name__ == "__main__":
    port = 2345
    host = "127.0.0.1"
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    if len(sys.argv) > 2:
        host = sys.argv[2]
    main(port, host)