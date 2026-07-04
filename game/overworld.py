"""Top-down overhead exploration, in the style of the original Fallout world map."""

import random

import pygame

from game import constants as c
from game import iso
from game import sprites
from game.data.maps import OVERWORLD_MAP

TILE_COLORS = {
    ".": c.COLOR_SAND,
    ",": c.COLOR_ROAD,
    "d": c.COLOR_GRASS_DEAD,
    "#": c.COLOR_WALL,
    "~": c.COLOR_WATER,
    "E": c.COLOR_ENCOUNTER,
    "T": c.COLOR_TOWN,
    "@": c.COLOR_SAND,
}
BLOCKED_TILES = {"#", "~"}
WALL_TILES = {"#"}  # raised as pseudo-3D blocks; water stays flat
ENCOUNTER_TILES = {"E"}
TOWN_TILES = {"T"}

MOVE_DELAY = 0.13  # seconds between steps, for classic tile-by-tile feel


class Overworld:
    def __init__(self, party, on_encounter, on_town=None):
        self.rows = [list(row) for row in OVERWORLD_MAP]
        self.height = len(self.rows)
        self.width = len(self.rows[0])
        self.party = party
        self.on_encounter = on_encounter
        self.on_town = on_town

        self.px, self.py = self._find_start()
        self.move_timer = 0.0
        self.message = ""
        self.message_timer = 0.0
        self.encounter_chance = 0.12
        self.facing = 0  # camera rotation, in 90-degree steps clockwise
        self.facing_dir = "south"  # on-screen direction the player sprite faces

    def rotate_view(self, step):
        self.facing = (self.facing + step) % 4

    def _find_start(self):
        for y, row in enumerate(self.rows):
            for x, ch in enumerate(row):
                if ch == "@":
                    return x, y
        return 1, 1

    def _tile(self, x, y):
        if 0 <= y < self.height and 0 <= x < self.width:
            return self.rows[y][x]
        return "#"

    def update(self, dt, keys):
        self.move_timer -= dt
        if self.message_timer > 0:
            self.message_timer -= dt
            if self.message_timer <= 0:
                self.message = ""

        if self.move_timer > 0:
            return

        screen_dx = screen_dy = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            screen_dx = -1
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            screen_dx = 1
        elif keys[pygame.K_UP] or keys[pygame.K_w]:
            screen_dy = -1
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            screen_dy = 1

        if screen_dx == 0 and screen_dy == 0:
            return

        if screen_dy == -1:
            self.facing_dir = "north"
        elif screen_dy == 1:
            self.facing_dir = "south"
        elif screen_dx == -1:
            self.facing_dir = "west"
        elif screen_dx == 1:
            self.facing_dir = "east"

        # Keys are relative to what's on screen, not the underlying grid, so
        # "up" always moves toward the top of the screen no matter how the
        # camera has been rotated.
        dx, dy = iso.screen_relative_delta(screen_dx, screen_dy, self.facing)

        nx, ny = self.px + dx, self.py + dy
        tile = self._tile(nx, ny)
        if tile in BLOCKED_TILES:
            return

        self.px, self.py = nx, ny
        self.move_timer = MOVE_DELAY

        if tile in ENCOUNTER_TILES and random.random() < self.encounter_chance:
            self.on_encounter()
        elif tile in TOWN_TILES:
            self.message = "You find a settlement. Your party rests and heals."
            self.message_timer = 2.5
            for u in self.party:
                if u.alive:
                    u.hp = u.max_hp
            if self.on_town:
                self.on_town()

    def draw(self, surface):
        surface.fill(c.COLOR_BG)
        tile_w, tile_h = c.ISO_TILE_W, c.ISO_TILE_H
        view_h = c.SCREEN_HEIGHT - 90
        viewport_center = (c.SCREEN_WIDTH / 2, view_h / 2)

        rpx, rpy = iso.rotate_coords(self.px, self.py, self.width, self.height, self.facing)
        origin = iso.camera_origin(rpx, rpy, viewport_center, tile_w, tile_h)

        # Painter's algorithm: draw back-to-front so raised walls don't
        # cover tiles that are actually in front of them.
        cells = sorted(
            ((x, y) for y in range(self.height) for x in range(self.width)),
            key=lambda p: sum(iso.rotate_coords(p[0], p[1], self.width, self.height, self.facing)),
        )

        for (x, y) in cells:
            ch = self.rows[y][x]
            rx, ry = iso.rotate_coords(x, y, self.width, self.height, self.facing)
            color = TILE_COLORS.get(ch, c.COLOR_SAND)
            height = c.WALL_HEIGHT if ch in WALL_TILES else 0
            iso.draw_tile(surface, rx, ry, origin, color, tile_w, tile_h, height=height)
            if ch in WALL_TILES:
                center = iso.tile_center(rx, ry, origin, tile_w, tile_h)
                sprites.blit_grounded(surface, sprites.decoration("rock"),
                                       (center[0], center[1] - c.WALL_HEIGHT))
            elif ch in ENCOUNTER_TILES:
                center = iso.tile_center(rx, ry, origin, tile_w, tile_h)
                sprites.blit_grounded(surface, sprites.decoration("skull"), center)
            elif ch in TOWN_TILES:
                center = iso.tile_center(rx, ry, origin, tile_w, tile_h)
                sprites.blit_grounded(surface, sprites.decoration("town"), center)

        rpx, rpy = iso.rotate_coords(self.px, self.py, self.width, self.height, self.facing)
        center = iso.tile_center(rpx, rpy, origin, tile_w, tile_h)
        sprites.blit_grounded(surface, sprites.unit_sprite(self.party[0], facing=self.facing_dir), center)

        self._draw_hud(surface)

    def _draw_hud(self, surface):
        font = pygame.font.SysFont("consolas", 16)
        hud_rect = pygame.Rect(0, c.SCREEN_HEIGHT - 90, c.SCREEN_WIDTH, 90)
        pygame.draw.rect(surface, c.COLOR_PANEL_BG, hud_rect)
        pygame.draw.rect(surface, c.COLOR_PANEL_BORDER, hud_rect, 2)

        x = 16
        for u in self.party:
            status = f"{u.name}: {'DEAD' if not u.alive else f'HP {u.hp}/{u.max_hp}'}"
            color = c.COLOR_TEXT if u.alive else (120, 60, 60)
            label = font.render(status, True, color)
            surface.blit(label, (x, c.SCREEN_HEIGHT - 78))
            x += label.get_width() + 30

        help_label = font.render(
            "WASD/Arrows: move   Q/E: rotate view   Red zones: danger   Houses: town (heals)",
            True, c.COLOR_TEXT_DIM,
        )
        surface.blit(help_label, (16, c.SCREEN_HEIGHT - 40))

        if self.message:
            msg_label = font.render(self.message, True, (255, 230, 120))
            surface.blit(msg_label, (16, c.SCREEN_HEIGHT - 18))
