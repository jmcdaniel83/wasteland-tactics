"""Unit definitions shared by the overworld and the tactics battle grid."""

import random
from dataclasses import dataclass, field


@dataclass
class Unit:
    name: str
    faction: str  # constants.FACTION_PLAYER / FACTION_ENEMY
    max_hp: int
    attack: int
    defense: int
    move: int          # tiles it can move per turn
    ap_max: int         # action points per turn (1 move action + 1 act action typically)
    attack_range: int
    speed: int          # determines turn order
    color: tuple
    hp: int = None
    x: int = 0
    y: int = 0
    ap: int = None
    alive: bool = True
    has_acted: bool = False
    has_moved: bool = False
    sprite_id: str = None  # assets/characters/<sprite_id>/ - None means use the procedural sprite

    def __post_init__(self):
        if self.hp is None:
            self.hp = self.max_hp
        if self.ap is None:
            self.ap = self.ap_max

    def reset_turn(self):
        self.ap = self.ap_max
        self.has_acted = False
        self.has_moved = False

    def take_damage(self, amount):
        self.hp = max(0, self.hp - amount)
        if self.hp == 0:
            self.alive = False

    def roll_damage(self, target):
        base = max(1, self.attack - target.defense // 2)
        variance = random.randint(-2, 3)
        return max(1, base + variance)

    def distance_to(self, x, y):
        return abs(self.x - x) + abs(self.y - y)


def make_player_party():
    return [
        Unit(name="Lone Wanderer", faction="player", max_hp=32, attack=9, defense=4,
             move=4, ap_max=2, attack_range=1, speed=8, color=(80, 160, 230),
             sprite_id="wasteland_survivor_wearing_a_faded"),
        Unit(name="Dogmeat", faction="player", max_hp=20, attack=6, defense=2,
             move=6, ap_max=2, attack_range=1, speed=10, color=(150, 110, 70)),
        Unit(name="Sharpshooter", faction="player", max_hp=22, attack=8, defense=2,
             move=3, ap_max=2, attack_range=4, speed=6, color=(120, 200, 120)),
    ]


RAIDER_NAMES = ["Raider Thug", "Raider Psycho", "Scavver", "Wastelander Gunner"]


def make_enemy_squad(difficulty=1):
    squad = []
    count = 2 + difficulty
    for i in range(count):
        name = random.choice(RAIDER_NAMES)
        hp = 14 + difficulty * 3
        squad.append(Unit(
            name=f"{name} {i + 1}",
            faction="enemy",
            max_hp=hp,
            attack=6 + difficulty,
            defense=1 + difficulty // 2,
            move=3,
            ap_max=2,
            attack_range=1 if "Gunner" not in name else 3,
            speed=random.randint(4, 9),
            color=(200, 70, 60),
        ))
    return squad
