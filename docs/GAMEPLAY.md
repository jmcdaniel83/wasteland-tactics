# Gameplay

## Setup & running

```bash
make install   # uv sync
make run       # uv run python main.py
```

(or manually: `uv sync` then `uv run python main.py`)

## Controls

### Overworld
- `WASD` / arrow keys - move. Movement is relative to what's on screen, not
  the underlying grid - "up" always moves toward the top of the screen, no
  matter how the camera has been rotated.
- `Q` / `E` - rotate the camera 90 degrees counter-clockwise / clockwise
- Walking onto a red **danger zone** tile has a chance of triggering a
  tactical battle
- Walking onto a **town** tile fully heals your party

### Battle
- **Left click** your unit to select it - reachable tiles highlight blue,
  enemies already in attack range highlight red
- **Left click** a highlighted blue tile to move there (after moving,
  attack range re-highlights from the new position)
- **Left click** a red-highlighted enemy to attack it
- **Space** / **Enter** - end the current unit's turn early
- **Esc** - cancel the current selection (only before you've moved)
- `Q` / `E` - rotate the camera 90 degrees; move/attack targeting keeps
  working correctly after rotating

Turn order (top-right sidebar) is driven by each unit's Speed stat, highest
first. Enemies act automatically using simple "close the distance and
attack" AI.

## The party

| Unit | HP | Attack | Defense | Move | Range | Speed | Role |
|---|---|---|---|---|---|---|---|
| Lone Wanderer | 32 | 9 | 4 | 4 | 1 | 8 | Balanced melee lead |
| Dogmeat | 20 | 6 | 2 | 6 | 1 | 10 | Fast melee scout |
| Sharpshooter | 22 | 8 | 2 | 3 | 4 | 6 | Ranged support |

Enemy squads ("Raider Thug", "Raider Psycho", "Scavver", "Wastelander
Gunner") scale with a difficulty counter that increases by one after every
victory (capped at 6) - more enemies, more HP, more attack/defense per
level, and "Gunner"-named raiders get attack range 3 instead of 1.

## Combat rules

- Each unit gets 2 action points (AP) per turn: enough for one move and one
  attack (in either order), or two moves, or one attack without moving.
- **Attacking always ends your turn**, whether or not you moved first -
  there's no move-attack-move-attack in a single turn.
- Move range is a BFS flood fill bounded by the unit's `move` stat -
  blocked by rubble obstacles and other units, so you can't path through
  a unit or a wall even if the raw tile distance would allow it.
- Attack range is a diamond (Manhattan distance) check around the unit's
  *current* position - melee units need `range 1` (adjacent), the
  Sharpshooter's `range 4` lets it fight from well outside melee reach.
- Damage = `attacker.attack - target.defense // 2`, floored at 1, plus a
  small random variance (-2 to +3), floored at 1 again.
- A battle ends the moment one side has no living units left.

## After a battle

- **Win**: difficulty increases (capped), surviving party members heal 25%
  of their max HP.
- **Loss**: the whole party is revived at 50% HP and returned to the
  overworld (there's no permadeath / game-over screen yet - see
  [STATUS.md](STATUS.md) for known gaps).
