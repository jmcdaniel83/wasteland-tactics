"""Grid-based, turn-based tactical battle (Final Fantasy Tactics style)."""

import random
import copy
from collections import deque

import pygame

from game import constants as c
from game import iso
from game import sprites
from game.data.battle_maps import BATTLE_MAPS

SIDEBAR_WIDTH = 260
BATTLE_MARGIN = 30
BANNER_HEIGHT = 40

PHASE_SELECT = "select"        # waiting for the player to pick a unit
PHASE_MOVE = "move"            # a unit is selected, showing move range
PHASE_ATTACK = "attack"        # a unit has moved (or not), showing attack range
PHASE_ENEMY = "enemy"          # AI is resolving its turn
PHASE_OVER = "over"            # battle finished


class BattleGrid:
    def __init__(self, layout):
        self.rows = len(layout)
        self.cols = len(layout[0])
        self.blocked = set()
        self.player_slots = []
        self.enemy_slots = []
        for y, row in enumerate(layout):
            for x, ch in enumerate(row):
                if ch == "#":
                    self.blocked.add((x, y))
                elif ch == "P":
                    self.player_slots.append((x, y))
                elif ch == "X":
                    self.enemy_slots.append((x, y))

    def in_bounds(self, x, y):
        return 0 <= x < self.cols and 0 <= y < self.rows

    def is_free(self, x, y, units, ignore=None):
        if not self.in_bounds(x, y) or (x, y) in self.blocked:
            return False
        for u in units:
            if u is ignore or not u.alive:
                continue
            if u.x == x and u.y == y:
                return False
        return True

    def reachable_tiles(self, unit, units):
        """BFS flood fill of tiles reachable within unit.move, avoiding occupied/blocked tiles."""
        start = (unit.x, unit.y)
        visited = {start: 0}
        frontier = deque([start])
        while frontier:
            cx, cy = frontier.popleft()
            dist = visited[(cx, cy)]
            if dist >= unit.move:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = cx + dx, cy + dy
                if (nx, ny) in visited:
                    continue
                if not self.is_free(nx, ny, units, ignore=unit):
                    continue
                visited[(nx, ny)] = dist + 1
                frontier.append((nx, ny))
        visited.pop(start, None)
        return set(visited.keys())

    def tiles_in_range(self, x, y, rng):
        result = set()
        for dx in range(-rng, rng + 1):
            remaining = rng - abs(dx)
            for dy in range(-remaining, remaining + 1):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if self.in_bounds(nx, ny):
                    result.add((nx, ny))
        return result


class Battle:
    """Encapsulates one tactical encounter. Call update()/handle_click() from the
    main loop, and draw() to render. Check `finished` and `victory` for the outcome."""

    def __init__(self, player_party, enemy_squad, log=None):
        layout = random.choice(BATTLE_MAPS)
        self.grid = BattleGrid(layout)
        self.log = log if log is not None else []

        self.player_units = [copy.deepcopy(u) for u in player_party if u.alive]
        self.enemy_units = enemy_squad
        for u in self.player_units + self.enemy_units:
            u.reset_turn()

        slots = list(self.grid.player_slots)
        random.shuffle(slots)
        for u, (x, y) in zip(self.player_units, slots):
            u.x, u.y = x, y

        slots = list(self.grid.enemy_slots)
        random.shuffle(slots)
        for u, (x, y) in zip(self.enemy_units, slots):
            u.x, u.y = x, y

        self.units = self.player_units + self.enemy_units
        self.turn_queue = []
        self._build_turn_queue()

        self.phase = PHASE_SELECT
        self.selected = None
        self.move_tiles = set()
        self.attack_tiles = set()
        self.finished = False
        self.victory = False
        self.enemy_think_timer = 0.0
        self.message = "Your turn. Click a unit to act."

        self.tile_w, self.tile_h = c.ISO_TILE_W, c.ISO_TILE_H
        self.target_rect = (
            BATTLE_MARGIN, BATTLE_MARGIN,
            c.SCREEN_WIDTH - SIDEBAR_WIDTH - 2 * BATTLE_MARGIN,
            c.SCREEN_HEIGHT - 2 * BATTLE_MARGIN - BANNER_HEIGHT,
        )
        self.facing = 0  # camera rotation, in 90-degree steps clockwise
        self.origin = None
        self._recompute_origin()

    def _recompute_origin(self):
        rcols, rrows = iso.rotated_dims(self.grid.cols, self.grid.rows, self.facing)
        self.origin = iso.fit_origin(rcols, rrows, self.target_rect, self.tile_w, self.tile_h)

    def rotate_view(self, step):
        self.facing = (self.facing + step) % 4
        self._recompute_origin()

    def _to_screen(self, gx, gy):
        return iso.rotate_coords(gx, gy, self.grid.cols, self.grid.rows, self.facing)

    def pixel_to_tile(self, pos):
        """Screen position -> (grid_x, grid_y) in logical grid space, or None if outside."""
        rx, ry = iso.screen_to_grid(pos[0], pos[1], self.origin, self.tile_w, self.tile_h)
        rcols, rrows = iso.rotated_dims(self.grid.cols, self.grid.rows, self.facing)
        if not (0 <= rx < rcols and 0 <= ry < rrows):
            return None
        return iso.unrotate_coords(rx, ry, self.grid.cols, self.grid.rows, self.facing)

    # -- turn order -----------------------------------------------------
    def _build_turn_queue(self):
        alive = [u for u in self.units if u.alive]
        alive.sort(key=lambda u: (-u.speed, u.faction))
        self.turn_queue = alive

    @property
    def current_unit(self):
        return self.turn_queue[0] if self.turn_queue else None

    def _advance_turn(self):
        if not self.turn_queue:
            return
        finished_unit = self.turn_queue.pop(0)
        if finished_unit.alive:
            self.turn_queue.append(finished_unit)
        self.turn_queue = [u for u in self.turn_queue if u.alive]
        self.selected = None
        self.move_tiles = set()
        self.attack_tiles = set()

        self._check_victory()
        if self.finished:
            return

        nxt = self.current_unit
        if nxt is None:
            return
        if nxt.ap <= 0:
            nxt.reset_turn()
        if nxt.faction == c.FACTION_ENEMY:
            self.phase = PHASE_ENEMY
            self.enemy_think_timer = 0.5
            self.message = f"{nxt.name} is acting..."
        else:
            self.phase = PHASE_SELECT
            self.message = f"{nxt.name}'s turn. Click to move/attack."

    def _check_victory(self):
        if not any(u.alive for u in self.enemy_units):
            self.finished = True
            self.victory = True
            self.phase = PHASE_OVER
            self.message = "Victory! The wasteland is a little safer."
        elif not any(u.alive for u in self.player_units):
            self.finished = True
            self.victory = False
            self.phase = PHASE_OVER
            self.message = "Your party has fallen..."

    # -- player input -----------------------------------------------------
    def handle_click(self, tile):
        if self.phase == PHASE_OVER or self.phase == PHASE_ENEMY:
            return
        unit = self.current_unit
        if unit is None or unit.faction != c.FACTION_PLAYER:
            return
        tx, ty = tile

        if self.phase == PHASE_SELECT:
            if unit.x == tx and unit.y == ty:
                self.selected = unit
                self.move_tiles = self.grid.reachable_tiles(unit, self.units) if unit.ap > 0 else set()
                self.attack_tiles = self._attack_tiles_from(unit.x, unit.y, unit)
                self.phase = PHASE_MOVE
                self.message = f"{unit.name} selected. Choose a tile to move, or an enemy in red to attack."

        elif self.phase == PHASE_MOVE:
            target = self._unit_at(tx, ty)
            if target and target.faction == c.FACTION_ENEMY and (tx, ty) in self.attack_tiles:
                self._do_attack(unit, target)
                return
            if (tx, ty) in self.move_tiles and unit.ap > 0:
                unit.x, unit.y = tx, ty
                unit.ap -= 1
                unit.has_moved = True
                self.move_tiles = set()
                self.attack_tiles = self._attack_tiles_from(unit.x, unit.y, unit)
                self.phase = PHASE_ATTACK
                self.message = f"{unit.name} moved. Attack an enemy in red, or end turn (Space)."
            elif unit.x == tx and unit.y == ty:
                pass  # re-clicked self, no-op
            else:
                self.message = "Out of move range."

        elif self.phase == PHASE_ATTACK:
            target = self._unit_at(tx, ty)
            if target and target.faction == c.FACTION_ENEMY and (tx, ty) in self.attack_tiles:
                self._do_attack(unit, target)

    def end_unit_turn(self):
        """Skip remaining actions for the current unit (Space / right-click)."""
        unit = self.current_unit
        if unit is None or unit.faction != c.FACTION_PLAYER or self.phase == PHASE_ENEMY:
            return
        unit.ap = 0
        self._advance_turn()

    def cancel_selection(self):
        if self.phase in (PHASE_MOVE, PHASE_ATTACK) and self.selected and not self.selected.has_moved:
            self.phase = PHASE_SELECT
            self.selected = None
            self.move_tiles = set()
            self.attack_tiles = set()

    def _unit_at(self, x, y):
        for u in self.units:
            if u.alive and u.x == x and u.y == y:
                return u
        return None

    def _attack_tiles_from(self, x, y, unit):
        candidates = self.grid.tiles_in_range(x, y, unit.attack_range)
        result = set()
        for (tx, ty) in candidates:
            target = self._unit_at(tx, ty)
            if target and target.faction != unit.faction:
                result.add((tx, ty))
        return result

    def _do_attack(self, attacker, target):
        dmg = attacker.roll_damage(target)
        target.take_damage(dmg)
        self.log.append(f"{attacker.name} hits {target.name} for {dmg}.")
        self.message = f"{attacker.name} hits {target.name} for {dmg} damage!"
        # Attacking always spends the rest of the unit's turn (move + attack, one attack per turn).
        attacker.ap = 0
        attacker.has_acted = True
        if not target.alive:
            self.log.append(f"{target.name} is destroyed!")
        self.move_tiles = set()
        self.attack_tiles = set()
        self._check_victory()
        if not self.finished:
            self._advance_turn()

    # -- update / AI -----------------------------------------------------
    def update(self, dt):
        if self.phase != PHASE_ENEMY or self.finished:
            return
        self.enemy_think_timer -= dt
        if self.enemy_think_timer > 0:
            return
        unit = self.current_unit
        if unit is None or unit.faction != c.FACTION_ENEMY:
            return
        self._run_enemy_ai(unit)
        self.enemy_think_timer = 0.4

    def _run_enemy_ai(self, unit):
        targets = [u for u in self.player_units if u.alive]
        if not targets:
            self._check_victory()
            return
        target = min(targets, key=lambda t: unit.distance_to(t.x, t.y))

        attack_tiles = self._attack_tiles_from(unit.x, unit.y, unit)
        if (target.x, target.y) in attack_tiles and unit.ap > 0:
            self._do_attack(unit, target)
            return

        if unit.ap > 0 and not unit.has_moved:
            reachable = self.grid.reachable_tiles(unit, self.units)
            best_tile = None
            best_dist = unit.distance_to(target.x, target.y)
            for (tx, ty) in reachable:
                d = abs(tx - target.x) + abs(ty - target.y)
                if d < best_dist:
                    best_dist = d
                    best_tile = (tx, ty)
            if best_tile:
                unit.x, unit.y = best_tile
                unit.ap -= 1
                unit.has_moved = True
                attack_tiles = self._attack_tiles_from(unit.x, unit.y, unit)
                if (target.x, target.y) in attack_tiles and unit.ap > 0:
                    self._do_attack(unit, target)
                    return

        unit.ap = 0
        self._advance_turn()

    # -- rendering -----------------------------------------------------
    def draw(self, surface):
        origin = self.origin
        tile_w, tile_h = self.tile_w, self.tile_h
        font = pygame.font.SysFont("consolas", 14)

        cells = sorted(
            ((x, y) for y in range(self.grid.rows) for x in range(self.grid.cols)),
            key=lambda p: sum(self._to_screen(*p)),
        )
        for (x, y) in cells:
            rx, ry = self._to_screen(x, y)
            blocked = (x, y) in self.grid.blocked
            color = (70, 60, 55) if blocked else ((44, 50, 42) if (x + y) % 2 == 0 else (38, 44, 36))
            height = c.WALL_HEIGHT if blocked else 0
            iso.draw_tile(surface, rx, ry, origin, color, tile_w, tile_h, height=height)
            if blocked:
                center = iso.tile_center(rx, ry, origin, tile_w, tile_h)
                sprites.blit_grounded(surface, sprites.decoration("rock"),
                                       (center[0], center[1] - c.WALL_HEIGHT))

        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        if self.phase == PHASE_MOVE:
            for (x, y) in self.move_tiles:
                rx, ry = self._to_screen(x, y)
                pygame.draw.polygon(overlay, c.COLOR_HIGHLIGHT_MOVE,
                                     iso.diamond_points(rx, ry, origin, tile_w, tile_h))
        if self.phase in (PHASE_MOVE, PHASE_ATTACK):
            for (x, y) in self.attack_tiles:
                rx, ry = self._to_screen(x, y)
                pygame.draw.polygon(overlay, c.COLOR_HIGHLIGHT_ATTACK,
                                     iso.diamond_points(rx, ry, origin, tile_w, tile_h))
        surface.blit(overlay, (0, 0))

        living = sorted((u for u in self.units if u.alive),
                         key=lambda u: sum(self._to_screen(u.x, u.y)))
        for u in living:
            rx, ry = self._to_screen(u.x, u.y)
            cx, cy = iso.tile_center(rx, ry, origin, tile_w, tile_h)
            cx, cy = int(cx), int(cy)

            if u is self.selected:
                ring_rect = pygame.Rect(0, 0, tile_w - 8, tile_h - 4)
                ring_rect.center = (cx, cy)
                pygame.draw.ellipse(surface, c.COLOR_HIGHLIGHT_SELECT[:3], ring_rect, 2)

            sprite = sprites.unit_sprite(u)
            sprites.blit_grounded(surface, sprite, (cx, cy))

            hp_ratio = u.hp / u.max_hp if u.max_hp else 0
            bar_w = tile_w - 20
            bar_rect_bg = pygame.Rect(cx - bar_w // 2, cy - sprite.get_height() - 8, bar_w, 5)
            pygame.draw.rect(surface, (40, 10, 10), bar_rect_bg)
            pygame.draw.rect(surface, c.COLOR_HP, (bar_rect_bg.x, bar_rect_bg.y, int(bar_w * hp_ratio), 5))

            label = font.render(u.name.split(" ")[0], True, (230, 230, 230))
            surface.blit(label, (cx - label.get_width() // 2, cy + 4))

        self._draw_sidebar(surface, c.SCREEN_WIDTH - SIDEBAR_WIDTH + 10, BATTLE_MARGIN)

    def _draw_sidebar(self, surface, x, y):
        title_font = pygame.font.SysFont("consolas", 16)
        line_font = pygame.font.SysFont("consolas", 13)
        title = title_font.render("TURN ORDER", True, c.COLOR_TEXT)
        surface.blit(title, (x, y))
        for i, u in enumerate(self.turn_queue[:8]):
            tag = "> " if i == 0 else "  "
            color = c.COLOR_TEXT if u.faction == c.FACTION_PLAYER else (230, 120, 120)
            short_name = u.name.split(" ")[0]
            line = line_font.render(f"{tag}{short_name} {u.hp}/{u.max_hp}", True, color)
            surface.blit(line, (x, y + 26 + i * 20))
