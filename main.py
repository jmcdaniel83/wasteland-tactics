"""Wasteland Tactics
An overhead post-apocalyptic RPG (Fallout 1/2 style exploration) with
Final Fantasy Tactics style grid-based, turn-based combat.

Controls
  Overworld:  WASD / Arrow keys to move
  Battle:     Left click to select a unit, move, and attack
              Space = end unit's turn early
              Esc   = cancel current selection (before moving)
"""

import sys

import pygame

from game import constants as c
from game.entities import make_player_party, make_enemy_squad
from game.overworld import Overworld
from game.battle import Battle, PHASE_OVER


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Wasteland Tactics")
        self.screen = pygame.display.set_mode((c.SCREEN_WIDTH, c.SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True

        self.log = []
        self.party = make_player_party()
        self.state = c.STATE_OVERWORLD
        self.overworld = Overworld(self.party, on_encounter=self.start_battle)
        self.battle = None
        self.difficulty = 1
        self.post_battle_timer = 0.0

    def start_battle(self):
        squad = make_enemy_squad(self.difficulty)
        self.battle = Battle(self.party, squad, log=self.log)
        self.state = c.STATE_BATTLE

    def end_battle(self):
        if self.battle.victory:
            self.difficulty = min(6, self.difficulty + 1)
            for u in self.party:
                if u.alive:
                    u.hp = min(u.max_hp, u.hp + u.max_hp // 4)
        else:
            for u in self.party:
                u.alive = True
                u.hp = u.max_hp // 2
        self.battle = None
        self.state = c.STATE_OVERWORLD

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state == c.STATE_BATTLE and self.battle:
                        self.battle.cancel_selection()
                elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    if self.state == c.STATE_BATTLE and self.battle:
                        self.battle.end_unit_turn()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.state == c.STATE_BATTLE and self.battle:
                    tile = self._pixel_to_tile(event.pos)
                    if tile:
                        self.battle.handle_click(tile)

    def _pixel_to_tile(self, pos, origin=(40, 40), tile=48):
        ox, oy = origin
        x, y = pos
        gx = (x - ox) // tile
        gy = (y - oy) // tile
        if 0 <= gx < self.battle.grid.cols and 0 <= gy < self.battle.grid.rows:
            return int(gx), int(gy)
        return None

    def update(self, dt):
        if self.state == c.STATE_OVERWORLD:
            keys = pygame.key.get_pressed()
            self.overworld.update(dt, keys)
        elif self.state == c.STATE_BATTLE and self.battle:
            self.battle.update(dt)
            if self.battle.phase == PHASE_OVER:
                self.post_battle_timer += dt
                if self.post_battle_timer > 1.8:
                    self.post_battle_timer = 0.0
                    self.end_battle()

    def draw(self):
        if self.state == c.STATE_OVERWORLD:
            self.overworld.draw(self.screen)
        elif self.state == c.STATE_BATTLE and self.battle:
            self.screen.fill(c.COLOR_BG)
            self.battle.draw(self.screen)
            self._draw_battle_banner()
        pygame.display.flip()

    def _draw_battle_banner(self):
        font = pygame.font.SysFont("consolas", 18)
        banner = pygame.Rect(0, c.SCREEN_HEIGHT - 40, c.SCREEN_WIDTH, 40)
        pygame.draw.rect(self.screen, c.COLOR_PANEL_BG, banner)
        pygame.draw.rect(self.screen, c.COLOR_PANEL_BORDER, banner, 2)
        label = font.render(self.battle.message, True, c.COLOR_TEXT)
        self.screen.blit(label, (16, c.SCREEN_HEIGHT - 32))

    def run(self):
        while self.running:
            dt = self.clock.tick(c.FPS) / 1000.0
            self.handle_events()
            self.update(dt)
            self.draw()
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    Game().run()
