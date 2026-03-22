"""Multiplayer client for Void Survivors.

Connects to a server, sends player input each frame,
and renders the game state received from the server.
Shows lobby, countdown, gameplay, and game over screens
based on the server's game state.

Usage:
    python mp_client.py <name> [port] [host]
    python mp_client.py Alice
    python mp_client.py Alice 2345 192.168.1.10
"""

import sys
import zmq
import math
import time
import pygame

from mp_action import Action


class GameRenderer:
    """Renders the game state snapshot received from the server.

    Handles all visual states: lobby, countdown, playing, game over.
    """

    def __init__(self):
        """Initialize fonts for rendering."""
        pygame.font.init()
        self.font_title = pygame.font.SysFont("Arial", 64, bold=True)
        self.font_large = pygame.font.SysFont("Arial", 42, bold=True)
        self.font_countdown = pygame.font.SysFont("Arial", 120, bold=True)
        self.font_medium = pygame.font.SysFont("Arial", 24, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 18)
        self.font_name = pygame.font.SysFont("Arial", 16, bold=True)
        self.font_boss = pygame.font.SysFont("Arial", 14, bold=True)

    def draw(self, surface, snapshot, my_name, camera_offset):
        """Draw the appropriate screen based on game state.

        Args:
            surface: pygame.Surface to draw on.
            snapshot: Dict with game state from server.
            my_name: This client's player name.
            camera_offset: pygame.Vector2 camera translation.
        """
        if not snapshot:
            return

        state = snapshot.get("state", "lobby")

        if state == "lobby":
            self._draw_lobby(surface, snapshot, my_name)
        elif state == "countdown":
            self._draw_countdown(surface, snapshot)
        elif state == "playing":
            self._draw_gameplay(surface, snapshot, my_name, camera_offset)
            self._draw_hud(surface, snapshot, my_name)
        elif state == "game_over":
            self._draw_gameplay(surface, snapshot, my_name, camera_offset)
            self._draw_game_over(surface, snapshot, my_name)

    # ── Lobby Screen ──

    def _draw_lobby(self, surface, snapshot, my_name):
        """Draw the lobby waiting screen showing connected players.

        Args:
            surface: pygame.Surface to draw on.
            snapshot: Game state dict with player_names and ready_players.
            my_name: This client's player name.
        """
        sw = surface.get_width()
        sh = surface.get_height()

        # Title
        pulse = abs(math.sin(time.time() * 2))
        title_color = (int(50 + 205 * pulse), int(200 * pulse), 255)
        title = self.font_title.render("VOID SURVIVORS", True, title_color)
        surface.blit(title, (sw / 2 - title.get_width() / 2, sh * 0.12))

        sub = self.font_medium.render("Multiplayer Lobby", True, (180, 180, 200))
        surface.blit(sub, (sw / 2 - sub.get_width() / 2, sh * 0.12 + 72))

        # Player list
        players = snapshot.get("player_names", [])
        ready = snapshot.get("ready_players", [])

        header = self.font_medium.render("Players:", True, (200, 200, 200))
        surface.blit(header, (sw / 2 - header.get_width() / 2, sh * 0.35))

        y = sh * 0.35 + 40
        for pname in players:
            is_ready = pname in ready
            is_me = pname == my_name
            status = "  READY" if is_ready else "  ..."
            color = (0, 255, 150) if is_ready else (200, 200, 200)
            if is_me:
                label = f"> {pname}{status} (you)"
            else:
                label = f"  {pname}{status}"
            text = self.font_medium.render(label, True, color)
            surface.blit(text, (sw / 2 - text.get_width() / 2, y))
            y += 34

        # Instructions
        my_ready = my_name in ready
        if my_ready:
            wait = self.font_small.render("Waiting for other players...", True, (150, 150, 150))
            surface.blit(wait, (sw / 2 - wait.get_width() / 2, sh * 0.75))
        else:
            if int(time.time() * 2) % 2 == 0:
                prompt = self.font_medium.render("Press SPACE when ready", True, (255, 255, 100))
                surface.blit(prompt, (sw / 2 - prompt.get_width() / 2, sh * 0.75))

        # Controls
        controls = self.font_small.render("WASD: Move  |  Mouse: Aim  |  Click/Space: Shoot", True, (120, 120, 140))
        surface.blit(controls, (sw / 2 - controls.get_width() / 2, sh * 0.85))

    # ── Countdown Screen ──

    def _draw_countdown(self, surface, snapshot):
        """Draw the 3-2-1-GO countdown.

        Args:
            surface: pygame.Surface to draw on.
            snapshot: Game state dict with countdown_remaining.
        """
        sw = surface.get_width()
        sh = surface.get_height()
        remaining = snapshot.get("countdown_remaining", 0)

        if remaining > 2:
            number = "3"
            color = (255, 80, 80)
        elif remaining > 1:
            number = "2"
            color = (255, 200, 50)
        elif remaining > 0:
            number = "1"
            color = (50, 255, 100)
        else:
            number = "GO!"
            color = (0, 200, 255)

        # Scale effect
        phase = remaining % 1.0
        scale = 1.0 + 0.3 * phase
        font_size = int(120 * scale)
        font = pygame.font.SysFont("Arial", font_size, bold=True)

        text = font.render(number, True, color)
        surface.blit(text, (sw / 2 - text.get_width() / 2, sh / 2 - text.get_height() / 2))

        ready_text = self.font_medium.render("Get ready...", True, (180, 180, 180))
        surface.blit(ready_text, (sw / 2 - ready_text.get_width() / 2, sh / 2 - 100))

    # ── Game Over Screen ──

    def _draw_game_over(self, surface, snapshot, my_name):
        """Draw the game over overlay with scores and restart prompt.

        Args:
            surface: pygame.Surface to draw on.
            snapshot: Game state dict with scores.
            my_name: This client's player name.
        """
        sw = surface.get_width()
        sh = surface.get_height()

        # Dimmed overlay
        overlay = pygame.Surface((sw, sh))
        overlay.set_alpha(150)
        overlay.fill((0, 0, 0))
        surface.blit(overlay, (0, 0))

        # Game Over text
        go_text = self.font_large.render("GAME OVER", True, (255, 60, 60))
        surface.blit(go_text, (sw / 2 - go_text.get_width() / 2, sh * 0.2))

        wave = snapshot.get("wave_number", 0)
        wave_text = self.font_medium.render(f"Reached Wave {wave}", True, (200, 200, 200))
        surface.blit(wave_text, (sw / 2 - wave_text.get_width() / 2, sh * 0.2 + 55))

        # Scoreboard
        scores = snapshot.get("scores", {})
        sorted_scores = sorted(scores.items(), key=lambda s: s[1]["score"], reverse=True)

        header = self.font_medium.render("Final Scores:", True, (200, 200, 200))
        surface.blit(header, (sw / 2 - header.get_width() / 2, sh * 0.4))

        y = sh * 0.4 + 40
        for i, (name, data) in enumerate(sorted_scores):
            medal = ["1st", "2nd", "3rd", "4th"][min(i, 3)]
            is_me = name == my_name
            color = (0, 255, 200) if is_me else (220, 220, 220)
            label = f"{medal}  {name}: {data['score']} pts"
            text = self.font_medium.render(label, True, color)
            surface.blit(text, (sw / 2 - text.get_width() / 2, y))
            y += 34

        # Restart prompt
        if int(time.time() * 2) % 2 == 0:
            restart = self.font_medium.render("Press R to restart", True, (255, 255, 100))
            surface.blit(restart, (sw / 2 - restart.get_width() / 2, sh * 0.8))

    # ── Gameplay Rendering ──

    def _draw_gameplay(self, surface, snapshot, my_name, offset):
        """Draw all game units (grid, border, enemies, players, etc).

        Args:
            surface: pygame.Surface to draw on.
            snapshot: Game state dict with units.
            my_name: This client's player name.
            offset: pygame.Vector2 camera offset.
        """
        self._draw_grid(surface, offset)

        ws = snapshot["world_size"]
        rect = pygame.Rect(offset.x, offset.y, ws[0], ws[1])
        pygame.draw.rect(surface, (60, 60, 80), rect, 3)

        # Draw in layer order: powerups, particles, bullets, enemies, players
        for unit in snapshot["units"]:
            if unit["type"].startswith("powerup"):
                self._draw_powerup(surface, unit, offset)
        for unit in snapshot["units"]:
            if unit["type"] == "particle":
                self._draw_particle(surface, unit, offset)
        for unit in snapshot["units"]:
            if unit["type"] in ("player_bullet", "enemy_bullet"):
                self._draw_bullet(surface, unit, offset)
        for unit in snapshot["units"]:
            t = unit["type"]
            if t == "basic_enemy":
                self._draw_basic_enemy(surface, unit, offset)
            elif t == "fast_enemy":
                self._draw_fast_enemy(surface, unit, offset)
            elif t == "tank_enemy":
                self._draw_tank_enemy(surface, unit, offset)
            elif t == "shooter_enemy":
                self._draw_shooter_enemy(surface, unit, offset)
            elif t == "boss_enemy":
                self._draw_boss_enemy(surface, unit, offset)
        for unit in snapshot["units"]:
            if unit["type"] == "player" and unit.get("alive", True):
                self._draw_player(surface, unit, offset, unit["name"] == my_name)

    # ── Unit Drawing Methods ──

    def _screen(self, unit, offset):
        """Convert unit world position to screen position."""
        return pygame.Vector2(unit["x"] + offset.x, unit["y"] + offset.y)

    def _draw_player(self, surface, unit, offset, is_me):
        """Draw a player with trail, aim, health bar, and name tag."""
        screen = self._screen(unit, offset)
        r = unit["radius"]

        for i, (tx, ty) in enumerate(unit.get("trail", [])):
            alpha = (i + 1) / max(1, len(unit["trail"]))
            trail_color = (int(0 * alpha), int(150 * alpha), int(255 * alpha))
            tr = max(2, int(r * 0.4 * alpha))
            pygame.draw.circle(surface, trail_color, (tx + offset.x, ty + offset.y), tr)

        if unit.get("is_invincible") and int(time.time() * 10) % 2 == 0:
            return

        color = (0, 255, 200) if is_me else unit["color"]
        pygame.draw.circle(surface, color, screen, r, 3)
        inner = (0, 160, 220) if is_me else (0, 80, 150)
        pygame.draw.circle(surface, inner, screen, r - 4)

        aim = unit.get("aim_angle", 0)
        aim_end = screen + pygame.Vector2(math.cos(aim) * (r + 14), math.sin(aim) * (r + 14))
        pygame.draw.line(surface, (255, 255, 100), screen, aim_end, 2)

        bar_w, bar_h = 36, 4
        bx = screen.x - bar_w / 2
        by = screen.y - r - 10
        ratio = unit["health"] / unit["max_health"]
        pygame.draw.rect(surface, (80, 0, 0), (bx, by, bar_w, bar_h))
        bar_color = (0, 220, 0) if ratio > 0.5 else (220, 220, 0) if ratio > 0.25 else (220, 0, 0)
        pygame.draw.rect(surface, bar_color, (bx, by, bar_w * ratio, bar_h))

        name_text = self.font_name.render(unit["name"], True, (255, 255, 255))
        surface.blit(name_text, (screen.x - name_text.get_width() / 2, screen.y - r - 24))

    def _draw_basic_enemy(self, surface, unit, offset):
        screen = self._screen(unit, offset)
        pygame.draw.circle(surface, unit["color"], screen, unit["radius"])
        pygame.draw.circle(surface, (180, 30, 30), screen, unit["radius"] - 4)
        self._draw_enemy_hp(surface, screen, unit)

    def _draw_fast_enemy(self, surface, unit, offset):
        screen = self._screen(unit, offset)
        r = unit["radius"]
        pts = [(screen.x, screen.y - r), (screen.x + r, screen.y),
               (screen.x, screen.y + r), (screen.x - r, screen.y)]
        pygame.draw.polygon(surface, unit["color"], pts)
        pygame.draw.polygon(surface, (200, 120, 0), pts, 2)
        self._draw_enemy_hp(surface, screen, unit)

    def _draw_tank_enemy(self, surface, unit, offset):
        screen = self._screen(unit, offset)
        r = unit["radius"]
        pygame.draw.circle(surface, unit["color"], screen, r)
        pygame.draw.circle(surface, (100, 30, 160), screen, r - 6)
        pygame.draw.circle(surface, (200, 100, 255), screen, r, 3)
        self._draw_enemy_hp(surface, screen, unit)

    def _draw_shooter_enemy(self, surface, unit, offset):
        screen = self._screen(unit, offset)
        r = unit["radius"]
        pts = []
        for i in range(6):
            angle = math.pi / 6 + i * math.pi / 3
            pts.append((screen.x + r * math.cos(angle), screen.y + r * math.sin(angle)))
        pygame.draw.polygon(surface, unit["color"], pts)
        pygame.draw.polygon(surface, (0, 180, 100), pts, 2)
        self._draw_enemy_hp(surface, screen, unit)

    def _draw_boss_enemy(self, surface, unit, offset):
        screen = self._screen(unit, offset)
        r = unit["radius"]
        spin = unit.get("spin_angle", 0)
        phase = unit.get("phase", "chase")

        for i in range(8):
            angle = spin + (2 * math.pi * i / 8)
            inner = screen + pygame.Vector2(math.cos(angle) * (r - 8), math.sin(angle) * (r - 8))
            outer = screen + pygame.Vector2(math.cos(angle) * (r + 12), math.sin(angle) * (r + 12))
            color = (255, 100, 100) if phase == "chase" else (255, 200, 50)
            pygame.draw.line(surface, color, inner, outer, 3)

        ring_color = (200, 30, 30) if phase == "chase" else (200, 160, 30)
        pygame.draw.circle(surface, ring_color, screen, r, 4)
        pulse = 0.8 + 0.2 * math.sin(time.time() * 6)
        core_r = int((r - 10) * pulse)
        core_color = (180, 20, 20) if phase == "chase" else (180, 140, 20)
        pygame.draw.circle(surface, core_color, screen, core_r)
        pygame.draw.circle(surface, (255, 255, 200), screen, 8)
        pygame.draw.circle(surface, (60, 0, 0), screen, 4)

        bar_w, bar_h = r * 3, 6
        bx, by = screen.x - bar_w / 2, screen.y + r + 10
        ratio = max(0, unit["health"] / unit["max_health"])
        pygame.draw.rect(surface, (40, 0, 0), (bx - 1, by - 1, bar_w + 2, bar_h + 2))
        pygame.draw.rect(surface, (80, 0, 0), (bx, by, bar_w, bar_h))
        bar_color = (255, 50, 50) if ratio > 0.5 else (255, 150, 0) if ratio > 0.25 else (255, 255, 0)
        pygame.draw.rect(surface, bar_color, (bx, by, bar_w * ratio, bar_h))
        label = self.font_boss.render("BOSS", True, (255, 80, 80))
        surface.blit(label, (screen.x - label.get_width() / 2, screen.y - r - 20))

    def _draw_bullet(self, surface, unit, offset):
        screen = self._screen(unit, offset)
        if unit["type"] == "player_bullet":
            pygame.draw.circle(surface, (255, 200, 50), screen, unit["radius"] + 2)
        else:
            pygame.draw.circle(surface, (180, 30, 30), screen, unit["radius"] + 1)
        pygame.draw.circle(surface, unit["color"], screen, unit["radius"])

    def _draw_powerup(self, surface, unit, offset):
        screen = self._screen(unit, offset)
        pulse = 1 + 0.2 * math.sin(unit.get("pulse_phase", 0))
        r = int(unit["radius"] * pulse)
        glow = tuple(min(255, c + 50) for c in unit["color"])
        pygame.draw.circle(surface, glow, screen, r + 4, 2)
        pygame.draw.circle(surface, unit["color"], screen, r)
        white = (255, 255, 255)
        t = unit["type"]
        if t == "powerup_health":
            pygame.draw.line(surface, white, (screen.x - 5, screen.y), (screen.x + 5, screen.y), 2)
            pygame.draw.line(surface, white, (screen.x, screen.y - 5), (screen.x, screen.y + 5), 2)
        elif t == "powerup_speed":
            pts = [(screen.x - 3, screen.y - 6), (screen.x + 2, screen.y - 1),
                   (screen.x - 1, screen.y - 1), (screen.x + 3, screen.y + 6),
                   (screen.x - 2, screen.y + 1), (screen.x + 1, screen.y + 1)]
            pygame.draw.polygon(surface, white, pts)
        elif t == "powerup_multishot":
            for dx in [-4, 0, 4]:
                pygame.draw.circle(surface, white, (int(screen.x + dx), int(screen.y)), 2)

    def _draw_particle(self, surface, unit, offset):
        screen = self._screen(unit, offset)
        pygame.draw.circle(surface, unit["color"], screen, unit["radius"])

    def _draw_enemy_hp(self, surface, screen, unit):
        r = unit["radius"]
        bar_w, bar_h = r * 2, 3
        bx, by = screen.x - bar_w / 2, screen.y - r - 8
        ratio = max(0, unit["health"] / unit["max_health"])
        pygame.draw.rect(surface, (60, 0, 0), (bx, by, bar_w, bar_h))
        pygame.draw.rect(surface, (220, 50, 50), (bx, by, bar_w * ratio, bar_h))

    # ── HUD ──

    def _draw_hud(self, surface, snapshot, my_name):
        """Draw in-game HUD: health bar, wave, scoreboard."""
        scores = snapshot.get("scores", {})
        wave = snapshot.get("wave_number", 0)

        if my_name in scores:
            my = scores[my_name]
            x, y = 20, 20
            bar_w, bar_h = 200, 20
            ratio = my["health"] / my["max_health"]
            pygame.draw.rect(surface, (40, 40, 40), (x - 2, y - 2, bar_w + 4, bar_h + 4), border_radius=4)
            pygame.draw.rect(surface, (80, 0, 0), (x, y, bar_w, bar_h), border_radius=3)
            bar_color = (0, 200, 50) if ratio > 0.5 else (200, 200, 0) if ratio > 0.25 else (200, 0, 0)
            fill = max(0, int(bar_w * ratio))
            if fill > 0:
                pygame.draw.rect(surface, bar_color, (x, y, fill, bar_h), border_radius=3)
            hp = self.font_small.render(f"{my['health']}/{my['max_health']}", True, (255, 255, 255))
            surface.blit(hp, (x + bar_w / 2 - hp.get_width() / 2, y + 1))

            y_off = 48
            now = time.time()
            if now < my.get("speed_boost_end", 0):
                rem = my["speed_boost_end"] - now
                t = self.font_small.render(f"Speed: {rem:.1f}s", True, (255, 220, 0))
                surface.blit(t, (20, y_off))
                y_off += 22
            if now < my.get("multi_shot_end", 0):
                rem = my["multi_shot_end"] - now
                t = self.font_small.render(f"Multi-Shot: {rem:.1f}s", True, (100, 150, 255))
                surface.blit(t, (20, y_off))

        if wave > 0:
            sw = surface.get_width()
            wt = self.font_medium.render(f"Wave {wave}", True, (200, 200, 200))
            surface.blit(wt, (sw / 2 - wt.get_width() / 2, 20))

        sw = surface.get_width()
        y_pos = 20
        sorted_scores = sorted(scores.items(), key=lambda s: s[1]["score"], reverse=True)
        for name, data in sorted_scores:
            dead = "" if data["alive"] else " [DEAD]"
            color = (0, 255, 200) if name == my_name else (200, 200, 200)
            t = self.font_small.render(f"{name}: {data['score']}{dead}", True, color)
            surface.blit(t, (sw - t.get_width() - 20, y_pos))
            y_pos += 22

    # ── Grid ──

    def _draw_grid(self, surface, offset):
        grid_color = (20, 20, 40)
        grid_size = 80
        sw, sh = surface.get_size()
        sx = int(offset.x % grid_size)
        sy = int(offset.y % grid_size)
        for x in range(sx, sw, grid_size):
            pygame.draw.line(surface, grid_color, (x, 0), (x, sh))
        for y in range(sy, sh, grid_size):
            pygame.draw.line(surface, grid_color, (0, y), (sw, y))


def get_action(name, keys, mouse_pos, screen_center, ready_pressed, restart_pressed):
    """Build an Action from current input state.

    Args:
        name: Player name.
        keys: pygame.key.get_pressed() result.
        mouse_pos: Tuple (x, y) of mouse position.
        screen_center: pygame.Vector2 screen center.
        ready_pressed: True if SPACE was pressed this frame (lobby).
        restart_pressed: True if R was pressed this frame (game over).

    Returns:
        Action instance.
    """
    ax, ay = 0, 0
    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
        ax -= 1
    if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
        ax += 1
    if keys[pygame.K_UP] or keys[pygame.K_w]:
        ay -= 1
    if keys[pygame.K_DOWN] or keys[pygame.K_s]:
        ay += 1

    dx = mouse_pos[0] - screen_center.x
    dy = mouse_pos[1] - screen_center.y
    aim_angle = math.atan2(dy, dx)
    shooting = pygame.mouse.get_pressed()[0] or keys[pygame.K_SPACE]

    return Action(name, ax, ay, shooting, aim_angle, ready_pressed, restart_pressed)


def find_my_position(snapshot, my_name):
    """Find the local player's world position for camera centering.

    Args:
        snapshot: Game state dict from server.
        my_name: This client's player name.

    Returns:
        pygame.Vector2 of the player's position, or world center.
    """
    if snapshot:
        for unit in snapshot["units"]:
            if unit["type"] == "player" and unit.get("name") == my_name:
                return pygame.Vector2(unit["x"], unit["y"])
        ws = snapshot["world_size"]
        return pygame.Vector2(ws[0] / 2, ws[1] / 2)
    return pygame.Vector2(400, 300)


def main(name, port, host):
    """Run the multiplayer client.

    Args:
        name: Player name for this client.
        port: Server port number.
        host: Server host address.
    """
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect(f"tcp://{host}:{port}")
    print(f"Connecting to server at {host}:{port} as '{name}'...")

    pygame.init()
    display = pygame.display.set_mode((800, 600), pygame.RESIZABLE)
    pygame.display.set_caption(f"Void Survivors - {name}")
    clock = pygame.time.Clock()
    renderer = GameRenderer()
    snapshot = None
    screen_size = pygame.Vector2(800, 600)
    camera_offset = pygame.Vector2(0, 0)
    camera_smoothing = 0.1
    bg_color = (10, 10, 25)

    running = True
    while running:
        display.fill(bg_color)
        ready_pressed = False
        restart_pressed = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                screen_size = pygame.Vector2(event.size)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                    ready_pressed = True
                if event.key == pygame.K_r:
                    restart_pressed = True

        keys = pygame.key.get_pressed()
        mouse_pos = pygame.mouse.get_pos()
        action = get_action(name, keys, mouse_pos, screen_size / 2,
                            ready_pressed, restart_pressed)
        socket.send_pyobj(action)

        # Render previous frame while waiting
        if snapshot:
            renderer.draw(display, snapshot, name, camera_offset)

        # Receive new state
        snapshot = socket.recv_pyobj()

        # Smooth camera follow
        my_pos = find_my_position(snapshot, name)
        desired_offset = screen_size / 2 - my_pos
        camera_offset += (desired_offset - camera_offset) * camera_smoothing

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    name = "_"
    port = 2345
    host = "127.0.0.1"
    if len(sys.argv) > 1:
        name = sys.argv[1]
    if len(sys.argv) > 2:
        port = int(sys.argv[2])
    if len(sys.argv) > 3:
        host = sys.argv[3]
    main(name, port, host)