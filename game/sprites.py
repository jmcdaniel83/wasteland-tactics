"""Procedurally-built sprite art.

No external art assets: every sprite here is a small pygame Surface drawn
once out of primitive shapes and cached, then blitted like normal sprite
art instead of being redrawn as a raw circle/diamond every frame.
"""

import pygame

from game import iso

_CACHE = {}

UNIT_SIZE = (28, 42)
SKIN = (198, 158, 128)
OUTLINE = (18, 16, 14)


def _humanoid(body_color, faction):
    w, h = UNIT_SIZE
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    leg_color = iso.shade(body_color, 0.55)
    arm_color = iso.shade(body_color, 0.8)

    pygame.draw.rect(surf, leg_color, (w // 2 - 7, h - 14, 5, 13))
    pygame.draw.rect(surf, leg_color, (w // 2 + 2, h - 14, 5, 13))

    torso = [
        (w // 2 - 9, h - 14),
        (w // 2 + 9, h - 14),
        (w // 2 + 7, h - 29),
        (w // 2 - 7, h - 29),
    ]
    pygame.draw.polygon(surf, body_color, torso)
    pygame.draw.polygon(surf, OUTLINE, torso, 1)

    pygame.draw.rect(surf, arm_color, (w // 2 - 12, h - 28, 4, 13))
    pygame.draw.rect(surf, arm_color, (w // 2 + 8, h - 28, 4, 13))

    head_center = (w // 2, h - 33)
    pygame.draw.circle(surf, SKIN, head_center, 7)
    pygame.draw.circle(surf, OUTLINE, head_center, 7, 1)

    if faction == "enemy":
        for i in range(-2, 3):
            x = head_center[0] + i * 3
            pygame.draw.line(surf, (70, 65, 60), (x, head_center[1] - 6), (x, head_center[1] - 12), 2)
    else:
        pygame.draw.line(surf, (255, 220, 130), (w // 2 - 4, h - 27), (w // 2 + 4, h - 27), 2)

    return surf


def unit_sprite(unit):
    key = ("unit", unit.faction, unit.color)
    if key not in _CACHE:
        _CACHE[key] = _humanoid(unit.color, unit.faction)
    return _CACHE[key]


def _rock():
    surf = pygame.Surface((32, 22), pygame.SRCALPHA)
    pygame.draw.ellipse(surf, (92, 84, 76), (2, 8, 28, 14))
    pygame.draw.ellipse(surf, (118, 108, 98), (7, 3, 20, 13))
    pygame.draw.ellipse(surf, (60, 54, 48), (2, 8, 28, 14), 1)
    pygame.draw.ellipse(surf, (60, 54, 48), (7, 3, 20, 13), 1)
    return surf


def _skull_marker():
    surf = pygame.Surface((18, 18), pygame.SRCALPHA)
    pygame.draw.circle(surf, (230, 224, 208), (9, 7), 6)
    pygame.draw.rect(surf, (230, 224, 208), (5, 11, 8, 4))
    pygame.draw.circle(surf, (35, 25, 22), (6, 7), 2)
    pygame.draw.circle(surf, (35, 25, 22), (12, 7), 2)
    pygame.draw.line(surf, (35, 25, 22), (7, 13), (9, 11), 1)
    pygame.draw.line(surf, (35, 25, 22), (11, 13), (9, 11), 1)
    return surf


def _town_marker():
    surf = pygame.Surface((26, 24), pygame.SRCALPHA)
    pygame.draw.polygon(surf, (132, 84, 56), [(13, 0), (25, 11), (1, 11)])
    pygame.draw.polygon(surf, OUTLINE, [(13, 0), (25, 11), (1, 11)], 1)
    pygame.draw.rect(surf, (184, 154, 112), (4, 11, 18, 12))
    pygame.draw.rect(surf, OUTLINE, (4, 11, 18, 12), 1)
    pygame.draw.rect(surf, (94, 70, 46), (11, 15, 4, 8))
    return surf


_DECORATIONS = {"rock": _rock, "skull": _skull_marker, "town": _town_marker}


def decoration(name):
    if name not in _CACHE:
        _CACHE[name] = _DECORATIONS[name]()
    return _CACHE[name]


def blit_grounded(surface, sprite, center, anchor_y_offset=0):
    """Blit a sprite so its bottom-center sits at `center` (the tile's floor point)."""
    rect = sprite.get_rect(midbottom=(int(center[0]), int(center[1]) + anchor_y_offset))
    surface.blit(sprite, rect)
