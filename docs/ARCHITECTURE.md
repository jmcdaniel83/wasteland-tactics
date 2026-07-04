# Architecture

Technical breakdown of how Wasteland Tactics is put together. For controls
and gameplay mechanics see [GAMEPLAY.md](GAMEPLAY.md); for current progress
and what's next see [STATUS.md](STATUS.md).

## Module map

```
main.py                     game loop, state machine (overworld <-> battle), input routing
game/constants.py           screen size, iso tile dimensions, colors, faction/state constants
game/entities.py            Unit dataclass, player party + enemy squad generation
game/iso.py                 isometric projection math (the core rendering engine)
game/sprites.py             sprite art: procedural fallback + real PixelLab art loading
game/overworld.py           top-down exploration: movement, camera, encounters
game/battle.py              tactical grid: turn queue, movement/attack ranges, AI
game/data/maps.py           overworld map layout (ASCII tile grid)
game/data/battle_maps.py    battle grid layouts (ASCII tile grid)
assets/characters/          generated sprite art (PixelLab exports)
```

`main.py` owns the top-level `Game` class: it holds the shared `party` (a
list of `Unit`), switches between an `Overworld` instance and a `Battle`
instance based on `self.state`, and routes pygame events (keyboard/mouse) to
whichever one is active. Neither `Overworld` nor `Battle` know about each
other - `Game` is the only thing that transitions between them, via the
`on_encounter` callback passed into `Overworld` and the `battle.finished`/
`battle.victory` flags checked each frame.

## `game/iso.py` - the projection engine

Everything renders on a logical grid of `(x, y)` integer coordinates - the
same coordinates used for movement, collision, and range calculations. This
module is the *only* place that knows how to turn a grid coordinate into an
isometric screen diamond, and back again for mouse picking. Nothing else
does its own trigonometry.

Core functions:

- `grid_to_screen` / `tile_center` / `diamond_points` - grid coordinate ->
  screen pixels (2:1 diamond projection: `sx = (gx-gy) * tile_w/2`,
  `sy = (gx+gy) * tile_h/2`)
- `screen_to_grid` - the exact inverse, used for mouse-click picking
- `bounds` / `fit_origin` - compute the screen-space bounding box of an
  `cols x rows` grid and an origin that centers it in a target rectangle
  (used to fit the battle grid next to the sidebar)
- `camera_origin` - origin that keeps a given grid cell centered in the
  viewport (used for the overworld camera following the player)
- `draw_tile` - draws one diamond, or (if `height > 0`) a raised pseudo-3D
  block with shaded side faces - this is how walls/rubble get their look
  without needing pre-rendered 3D art
- `rotate_coords` / `unrotate_coords` / `rotated_dims` - camera rotation in
  90-degree steps. `rotate_coords` maps a logical grid coordinate to where
  it should be *drawn* for the current facing; `unrotate_coords` is its
  exact inverse (draw coordinate -> logical coordinate), used to map mouse
  clicks back to real grid positions after the camera has been rotated.
  Verified as an exhaustive bijection (every cell round-trips correctly)
  before being wired into rendering.
- `rotate_vector` / `screen_relative_delta` - the *linear* part of the same
  rotation, without the bounding-box/reflection terms a position needs,
  used so movement keys always move the player the same on-screen direction
  regardless of camera facing (see "Camera rotation" below).

## Camera rotation

Both `Overworld` and `Battle` have a `facing` value (0-3, quarter turns
clockwise) and a `rotate_view(step)` method, bound to `Q`/`E` in `main.py`.
Rotating only changes *how the grid is drawn and picked* - the underlying
grid coordinates, movement rules, and combat logic never change.

- **Overworld**: movement keys are deliberately *not* grid-fixed. Pressing
  "up" always moves the player toward the top of the screen, no matter how
  many times the camera has been rotated - `screen_relative_delta` converts
  the on-screen direction the player pressed into the actual grid delta to
  apply, given the current facing.
- **Battle**: `Battle._to_screen(gx, gy)` (via `iso.rotate_coords`) is used
  for all rendering; `Battle.pixel_to_tile(pos)` inverts both the projection
  and the rotation to recover the real grid coordinate a click landed on.
  Rotating the camera mid-battle doesn't break move/attack targeting.

## `game/sprites.py` - sprite art

Two sources of sprite art, selected per-unit:

1. **Procedural** (`_humanoid`, `_rock`, `_skull_marker`, `_town_marker`) -
   small pygame `Surface`s built once out of primitive shapes (rects,
   circles, polygons) and cached, then blitted like normal sprite art
   instead of being redrawn every frame. This is the default/fallback for
   any unit without real art.
2. **Real art** (`_rotation_image`) - loads PNGs from
   `assets/characters/<sprite_id>/rotations/<direction>.png`, generated
   externally (currently via PixelLab) and trimmed to their actual content
   bounding box on load (`_trim_transparent`) so bottom-anchored placement
   lands on the character's feet rather than the padded canvas edge.

`Unit.sprite_id` (in `entities.py`) selects which path a unit uses -
`None` means "use the procedural sprite." `unit_sprite(unit, facing="south")`
is the single entry point both `Overworld` and `Battle` call; it tries real
art first, falls back to procedural.

`blit_grounded(surface, sprite, center)` is the shared placement helper:
every sprite (character or decoration) is anchored by its bottom-center at
the tile's floor point, which is what makes things look like they're
*standing on* the diamond rather than floating over it.

## `game/overworld.py`

- Loads `game/data/maps.py`'s ASCII grid (legend in that file's docstring:
  `.` sand, `,` road, `d` dead grass, `#` rubble/wall, `~` water, `E` danger
  zone, `T` town, `@` player start)
- `update(dt, keys)`: reads held keys, converts to a screen-relative grid
  delta (see above), checks the target tile isn't blocked, moves the
  player, and rolls for a random encounter on danger-zone tiles
  (`encounter_chance`, currently 0.12) or heals the party on town tiles
- `draw(surface)`: paints every tile back-to-front (painter's algorithm, so
  raised wall blocks don't wrongly cover tiles in front of them), then the
  player sprite, then the HUD (party HP, controls hint, transient messages)

## `game/battle.py`

- `BattleGrid`: parses a layout from `game/data/battle_maps.py` (`#` =
  blocked, `P`/`X` = player/enemy deployment slots), and provides
  `reachable_tiles` (BFS flood fill bounded by a unit's `move` stat, used
  for the move-range highlight) and `tiles_in_range` (diamond-shaped range
  check, used for attack range)
- `Battle` is a state machine over `PHASE_SELECT -> PHASE_MOVE ->
  PHASE_ATTACK` (player turns) or `PHASE_ENEMY` (AI turns), ending in
  `PHASE_OVER` once one side is wiped out
- Turn order (`turn_queue`) is sorted by `speed` descending and cycles by
  popping the front unit and re-appending it once its turn ends
  (`_advance_turn`); attacking always spends the rest of a unit's turn (one
  attack per turn, whether or not it moved first)
- `_run_enemy_ai`: picks the nearest living player unit, attacks if already
  in range, otherwise greedily moves to the reachable tile that most closes
  the distance, then attacks if that brought the target into range
- `draw`: same back-to-front tile painting as the overworld, plus a
  translucent overlay surface for move/attack range highlighting, unit
  sprites with HP bars and name labels, and the turn-order sidebar

## Testing approach

There's no formal test suite (no `pytest`, no CI) - verification has been
done via headless pygame runs, using `SDL_VIDEODRIVER=dummy` so the game
loop and rendering can run without a real display. This has been used to:

- Round-trip every grid cell through the iso projection and its inverse
  (including under all 4 camera rotations) to confirm click-picking is
  exact, not approximate
- Simulate full battles end-to-end (a scripted "click the nearest reachable
  tile toward the enemy, then attack if in range" loop) across many random
  seeds to confirm turns always resolve and battles always end
- Render frames to PNG and inspect them visually to catch things pure logic
  checks can't (e.g. a floating sprite, clipped sidebar text)

This caught at least one real bug before it shipped: an enemy that attacked
without first moving would leave its turn "stuck" because `_do_attack`
special-cased ending the turn only when the attacker's AP reached exactly
zero - fixed by always ending the turn on attack.
