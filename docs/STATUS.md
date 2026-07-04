# Project status

## Where things stand

Wasteland Tactics is a playable vertical slice: walk an overhead wasteland
map, get ambushed into a grid-based tactical battle, fight it out, win or
lose, repeat. Rendering is isometric with a rotatable camera, one character
(the Lone Wanderer) has real generated sprite art, and the rest of the cast
still uses procedural placeholder sprites.

There's also a separate `unity-port` branch holding a migration plan (see
[UNITY_MIGRATION.md](../UNITY_MIGRATION.md) on that branch) for a possible
future Unity/C# rewrite, aimed mainly at easier cross-platform demo
distribution (WebGL builds). Nothing has been built there yet - it's
planning only, and `main` (this pygame version) is the actively developed,
fully working codebase.

## Release history

| Tag | Summary |
|---|---|
| `v0.0.1` | First playable slice: overhead overworld exploration, FFT-style grid tactics, uv + Makefile tooling |
| `v0.0.2` | Switched rendering from flat top-down squares to 2D isometric projection (`game/iso.py`), including raised pseudo-3D blocks for walls/rubble |
| `v0.0.3` | Procedural sprite art (humanoid units, terrain decorations) replacing flat circles/diamonds; 4-way camera rotation (`Q`/`E`) in both overworld and battle |
| `v0.0.4` | Movement keys made camera-relative - "up" always moves toward the top of the screen regardless of camera rotation |
| `v0.0.5` | First real generated sprite art (Lone Wanderer, via PixelLab): 8 directional idle poses, `Unit.sprite_id` opt-in so other units keep the procedural fallback |

## Known limitations / rough edges

- **No walk-cycle animation yet** - the Lone Wanderer has static idle poses
  per direction only; still deciding on the animation-frame system (see
  "Next up" below)
- **Battle always shows the "south" pose** - battle doesn't track
  per-unit directional facing the way the overworld does
- **Clicking a raised wall's visible face** maps to the tile *behind* it,
  not the wall itself - a known limitation of simple iso click-picking
  without multi-layer hit-testing. No gameplay impact since walls aren't
  interactive.
- **Tightly-clustered battle deployment tiles** can cause unit name labels
  to overlap, now that real/procedural sprites are wider than plain circles
- **No permadeath or game-over** - losing a battle revives the whole party
  at 50% HP rather than ending the game
- **Only the Lone Wanderer has real art** - Dogmeat, the Sharpshooter, and
  all enemies still use procedural sprites
- **No automated tests / CI** - verification has been manual, via headless
  pygame runs (see [ARCHITECTURE.md](ARCHITECTURE.md#testing-approach))
- **Tag pushes and GitHub Release creation aren't available from this
  session's tooling** - releases are cut by handing the repo owner the exact
  `git tag`/`gh release` commands and notes to run themselves

## Next up

Roughly in the order they've come up in conversation, not a firm commitment:

1. Walk-cycle animation frames for the Lone Wanderer (PixelLab's Custom
   Animation tool - action description, frame count, starting direction
   already scoped)
2. Real sprite art for Dogmeat, the Sharpshooter, and enemy raiders
3. A small animation-frame-timer system in `sprites.py`/`overworld.py` to
   actually play back walk cycles instead of a single static pose
4. Terrain tile art (PixelLab's tileset tool, or a CC0 pack) to replace the
   flat procedural colors - the raised-block shading trick in `iso.draw_tile`
   should keep working with real top-face textures
5. Longer-term/exploratory: a Unity rewrite for easier cross-platform demo
   builds (see the `unity-port` branch) - not started, no timeline
