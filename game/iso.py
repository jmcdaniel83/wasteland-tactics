"""2D isometric projection helpers.

Grid coordinates (gx, gy) are the same logical tile coordinates used by the
overworld map and the battle grid; only how they're drawn on screen changes.
This module is the one place that knows how to turn a grid coordinate into a
screen diamond, and back again for mouse picking.

Convention: grid_to_screen(gx, gy) returns the *top vertex* of the diamond
for that cell. The diamond's four corners are then:
    top    = (sx, sy)
    right  = (sx + tile_w/2, sy + tile_h/2)
    bottom = (sx, sy + tile_h)
    left   = (sx - tile_w/2, sy + tile_h/2)
and its center is (sx, sy + tile_h/2).
"""

import math

import pygame


def grid_to_screen(gx, gy, origin=(0, 0), tile_w=64, tile_h=32):
    ox, oy = origin
    sx = ox + (gx - gy) * (tile_w / 2)
    sy = oy + (gx + gy) * (tile_h / 2)
    return sx, sy


def tile_center(gx, gy, origin=(0, 0), tile_w=64, tile_h=32):
    sx, sy = grid_to_screen(gx, gy, origin, tile_w, tile_h)
    return sx, sy + tile_h / 2


def diamond_points(gx, gy, origin=(0, 0), tile_w=64, tile_h=32):
    sx, sy = grid_to_screen(gx, gy, origin, tile_w, tile_h)
    return [
        (sx, sy),
        (sx + tile_w / 2, sy + tile_h / 2),
        (sx, sy + tile_h),
        (sx - tile_w / 2, sy + tile_h / 2),
    ]


def screen_to_grid(sx, sy, origin=(0, 0), tile_w=64, tile_h=32):
    """Inverse of grid_to_screen: which cell's diamond contains this point."""
    ox, oy = origin
    dx = sx - ox
    dy = sy - oy
    a = dx / (tile_w / 2)
    b = dy / (tile_h / 2)
    gx = math.floor((b + a) / 2)
    gy = math.floor((b - a) / 2)
    return gx, gy


def bounds(cols, rows, origin=(0, 0), tile_w=64, tile_h=32):
    """Bounding box (min_x, min_y, max_x, max_y) of a cols x rows iso grid."""
    xs = []
    ys = []
    for gy in (0, rows):
        for gx in (0, cols):
            sx, sy = grid_to_screen(gx, gy, origin, tile_w, tile_h)
            xs.append(sx)
            ys.append(sy)
    # The left/right-most points come from the diamond edges of the corner
    # cells, not just their top vertices, so pad by half a tile width/height.
    return (min(xs) - tile_w / 2, min(ys), max(xs) + tile_w / 2, max(ys) + tile_h)


def fit_origin(cols, rows, target_rect, tile_w=64, tile_h=32):
    """Origin that centers a cols x rows iso grid inside target_rect (x, y, w, h)."""
    tx, ty, tw, th = target_rect
    min_x, min_y, max_x, max_y = bounds(cols, rows, origin=(0, 0), tile_w=tile_w, tile_h=tile_h)
    grid_w = max_x - min_x
    grid_h = max_y - min_y
    origin_x = tx + (tw - grid_w) / 2 - min_x
    origin_y = ty + (th - grid_h) / 2 - min_y
    return origin_x, origin_y


def camera_origin(gx, gy, viewport_center, tile_w=64, tile_h=32):
    """Origin such that the center of tile (gx, gy) lands on viewport_center."""
    vx, vy = viewport_center
    raw_x, raw_y = tile_center(gx, gy, origin=(0, 0), tile_w=tile_w, tile_h=tile_h)
    return vx - raw_x, vy - raw_y


def rotated_dims(cols, rows, facing):
    """Bounding-box dims after rotating a cols x rows grid `facing` quarter turns."""
    return (rows, cols) if facing % 4 in (1, 3) else (cols, rows)


def rotate_coords(gx, gy, cols, rows, facing):
    """Map a logical grid coordinate to its draw coordinate for camera `facing`
    (0-3, quarter turns clockwise). Use with `rotated_dims` for the bounding box."""
    f = facing % 4
    if f == 0:
        return gx, gy
    if f == 1:
        return rows - 1 - gy, gx
    if f == 2:
        return cols - 1 - gx, rows - 1 - gy
    return gy, cols - 1 - gx  # f == 3


def unrotate_coords(rx, ry, cols, rows, facing):
    """Inverse of rotate_coords: draw coordinate -> original logical grid coordinate."""
    f = facing % 4
    if f == 0:
        return rx, ry
    if f == 1:
        return ry, rows - 1 - rx
    if f == 2:
        return cols - 1 - rx, rows - 1 - ry
    return cols - 1 - ry, rx  # f == 3


def shade(color, factor):
    """Lighten (factor > 1) or darken (factor < 1) an RGB color."""
    return tuple(max(0, min(255, int(ch * factor))) for ch in color)


def draw_tile(surface, gx, gy, origin, top_color, tile_w=64, tile_h=32,
              height=0, outline=(0, 0, 0)):
    """Draw one diamond tile, optionally raised as a block (for walls/rubble).

    `height` in pixels raises the top face and adds shaded left/right side
    faces beneath it, giving a simple pseudo-3D look without needing sprites.
    """
    ground = diamond_points(gx, gy, origin, tile_w, tile_h)
    if height <= 0:
        pygame.draw.polygon(surface, top_color, ground)
        if outline:
            pygame.draw.polygon(surface, outline, ground, 1)
        return

    raised_origin = (origin[0], origin[1] - height)
    top = diamond_points(gx, gy, raised_origin, tile_w, tile_h)

    left_face = [top[3], top[2], ground[2], ground[3]]
    right_face = [top[1], top[2], ground[2], ground[1]]
    pygame.draw.polygon(surface, shade(top_color, 0.6), left_face)
    pygame.draw.polygon(surface, shade(top_color, 0.8), right_face)
    if outline:
        pygame.draw.polygon(surface, outline, left_face, 1)
        pygame.draw.polygon(surface, outline, right_face, 1)

    pygame.draw.polygon(surface, top_color, top)
    if outline:
        pygame.draw.polygon(surface, outline, top, 1)
