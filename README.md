# Wasteland Tactics

A post-apocalyptic RPG that combines two classic styles:

- **Overworld exploration** in the overhead style of the original *Fallout* (1997) —
  walk your party across a wasteland map, find towns to rest at, and stumble into
  danger zones.
- **Grid-based, turn-based combat** in the style of *Final Fantasy Tactics* — when
  you run into trouble, the game switches to a tactical battle grid where each unit
  has a movement range, an attack range, and acts in speed-based turn order.

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)

## Setup & run

```bash
make install   # uv sync
make run       # uv run python main.py
```

See [docs/GAMEPLAY.md](docs/GAMEPLAY.md) for full controls and mechanics,
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for how the code is put
together, and [docs/STATUS.md](docs/STATUS.md) for release history and
what's next.

Quick controls: `WASD`/arrows to move, `Q`/`E` to rotate the camera, mouse
to act in battle. Full details in [docs/GAMEPLAY.md](docs/GAMEPLAY.md).
