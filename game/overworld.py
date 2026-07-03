"""Top-down overhead exploration, in the style of the original Fallout world map."""

import random

import pygame

from game import constants as c
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

        dx = dy = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = -1
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = 1
        elif keys[pygame.K_UP] or keys[pygame.K_w]:
            dy = -1
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy = 1

        if dx == 0 and dy == 0:
            return

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
        tile = c.TILE_SIZE
        view_cols = c.SCREEN_WIDTH // tile
        view_rows = (c.SCREEN_HEIGHT - 90) // tile

        cam_x = max(0, min(self.px - view_cols // 2, self.width - view_cols))
        cam_y = max(0, min(self.py - view_rows // 2, self.height - view_rows))

        for sy in range(view_rows + 1):
            for sx in range(view_cols + 1):
                wx, wy = cam_x + sx, cam_y + sy
                ch = self._tile(wx, wy)
                color = TILE_COLORS.get(ch, c.COLOR_SAND)
                rect = pygame.Rect(sx * tile, sy * tile, tile, tile)
                pygame.draw.rect(surface, color, rect)
                if ch == "E":
                    pygame.draw.circle(surface, (60, 20, 20), rect.center, 3)

        # player
        prect = pygame.Rect((self.px - cam_x) * tile, (self.py - cam_y) * tile, tile, tile)
        pygame.draw.circle(surface, (60, 130, 220), prect.center, tile // 2 - 4)
        pygame.draw.circle(surface, (255, 255, 255), prect.center, tile // 2 - 4, 2)

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
            "WASD/Arrows: move   Red zones (E): danger   T: town (safe, heals)",
            True, c.COLOR_TEXT_DIM,
        )
        surface.blit(help_label, (16, c.SCREEN_HEIGHT - 40))

        if self.message:
            msg_label = font.render(self.message, True, (255, 230, 120))
            surface.blit(msg_label, (16, c.SCREEN_HEIGHT - 18))
