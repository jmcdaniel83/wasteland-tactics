# Wasteland Tactics

A post-apocalyptic RPG that combines two classic styles:

- **Overworld exploration** in the overhead style of the original *Fallout* (1997) —
  walk your party across a wasteland map, find towns to rest at, and stumble into
  danger zones.
- **Grid-based, turn-based combat** in the style of *Final Fantasy Tactics* — when
  you run into trouble, the game switches to a tactical battle grid where each unit
  has a movement range, an attack range, and acts in speed-based turn order.

## Requirements

- Python 3.9+
- [pygame](https://www.pygame.org/) 2.5+

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate   # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

## Controls

### Overworld
- `WASD` / arrow keys — move your party
- Walking into a red **danger zone** tile has a chance of triggering a tactical battle
- Walking onto a **town** tile fully heals your party

### Battle
- **Left click** your unit to select it (highlighted tiles show where it can move)
- **Left click** a highlighted tile to move there
- **Left click** an enemy highlighted in red to attack it (in range)
- **Space** / **Enter** — end the current unit's turn early
- **Esc** — cancel the current selection (before you've moved)

Turn order (top-right sidebar) is driven by each unit's Speed stat. Enemies act
automatically using simple "close the distance and attack" AI.

## Project layout

```
main.py                 game loop / state machine (overworld <-> battle)
game/constants.py       shared colors, sizes, faction/state constants
game/entities.py        Unit stats, player party and enemy squad generation
game/overworld.py       tile-based overworld map, movement, encounters
game/battle.py          tactical grid, turn queue, movement/attack range, AI
game/data/maps.py       overworld map layout
game/data/battle_maps.py battle grid layouts
```

## Roadmap ideas

- Height/elevation on the battle grid and line-of-sight blocking
- Skills/abilities beyond basic attacks (grenades, aimed shots, stimpaks)
- Persistent party leveling and loot between battles
- Multiple overworld regions and hand-authored town/dialogue scenes
