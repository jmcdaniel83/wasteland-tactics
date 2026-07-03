"""Shared constants for Wasteland Tactics."""

SCREEN_WIDTH = 960
SCREEN_HEIGHT = 640
FPS = 60

# Isometric diamond tile dimensions (2:1 ratio, classic iso look)
ISO_TILE_W = 64
ISO_TILE_H = 32
WALL_HEIGHT = 26  # pixels a '#' block is raised, for the pseudo-3D look

# Overworld tile colors (procedural, no external art needed)
COLOR_SAND = (196, 164, 108)
COLOR_ROAD = (120, 112, 100)
COLOR_RUBBLE = (90, 82, 74)
COLOR_WATER = (46, 78, 92)
COLOR_WALL = (60, 56, 52)
COLOR_GRASS_DEAD = (128, 128, 78)
COLOR_ENCOUNTER = (150, 60, 50)
COLOR_TOWN = (180, 150, 90)

# UI colors
COLOR_BG = (10, 10, 10)
COLOR_TEXT = (0, 255, 102)  # pipboy green
COLOR_TEXT_DIM = (0, 150, 60)
COLOR_PANEL_BG = (12, 20, 14)
COLOR_PANEL_BORDER = (0, 255, 102)
COLOR_HP = (200, 40, 40)
COLOR_AP = (60, 140, 220)
COLOR_HIGHLIGHT_MOVE = (60, 140, 220, 110)
COLOR_HIGHLIGHT_ATTACK = (200, 40, 40, 110)
COLOR_HIGHLIGHT_SELECT = (255, 220, 60, 160)

# Factions
FACTION_PLAYER = "player"
FACTION_ENEMY = "enemy"

# Game states
STATE_OVERWORLD = "overworld"
STATE_BATTLE = "battle"
