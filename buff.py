"""Buff selection screen: pick 2 of 5 from the BUFFS table."""

from __future__ import annotations

import pygame

from constants import (
    BUFFS, SCREEN_W, SCREEN_H,
    PANEL, PANEL_DARK, PANEL_SOFT, PANEL_BORDER,
    TEXT, TEXT_DIM, TEXT_MUTED, ACCENT,
    MONEY_COLOR, HP_COLOR, SAN_COLOR, GOOD_COLOR,
)


BUFF_FLAVOUR = {
    "Iron Stomach":     "Start with +10 HP. All HP losses are reduced to 80%.",
    "Social Butterfly": "Start with +10 San. Daytime San gains x1.2 and Money gains x1.1.",
    "Scholarship":      "Start with +150 Money. All Money losses are reduced to 80%.",
    "Night Owl":        "Start with +5 HP. Better evening work, but daytime HP/San gains x0.8.",
    "Optimist":         "Start with +10 San. All San losses are reduced to 80%.",
}

REQUIRED_SELECTION = 2


class BuffSelector:
    def __init__(self):
        self.cursor = 0
        self.selected: set[int] = set()

    def move(self, delta: int) -> None:
        self.cursor = (self.cursor + delta) % len(BUFFS)

    def toggle(self) -> None:
        if self.cursor in self.selected:
            self.selected.remove(self.cursor)
        elif len(self.selected) < REQUIRED_SELECTION:
            self.selected.add(self.cursor)

    def is_ready(self) -> bool:
        return len(self.selected) == REQUIRED_SELECTION

    def get_selected_rows(self) -> list:
        return [BUFFS[i] for i in sorted(self.selected)]


def _bonus_str(hp: int, san: int, money: int) -> str:
    parts = []
    if hp:    parts.append(f"HP {hp:+d}")
    if san:   parts.append(f"San {san:+d}")
    if money: parts.append(f"Money {money:+d}")
    return ", ".join(parts) if parts else "special"


def _draw_keycap(screen, font, text, x, y, active=False):
    rect = pygame.Rect(x, y, 34, 28)
    pygame.draw.rect(screen, ACCENT if active else PANEL_SOFT, rect, border_radius=8)
    surf = font.render(text, True, (22, 24, 31) if active else TEXT)
    screen.blit(surf, (rect.centerx - surf.get_width() // 2,
                       rect.centery - surf.get_height() // 2))


def draw_buff_select(screen, fonts, selector: BuffSelector) -> None:
    f_large, f_med, f_small = fonts

    title = f_large.render("Choose 2 Buffs", True, TEXT)
    screen.blit(title, ((SCREEN_W - title.get_width()) // 2, 30))

    subtitle = f_small.render(
        "W/S or Up/Down move    SPACE toggle    ENTER confirm (need 2)",
        True, TEXT_DIM,
    )
    screen.blit(subtitle, ((SCREEN_W - subtitle.get_width()) // 2, 80))

    panel = pygame.Rect(40, 120, SCREEN_W - 80, SCREEN_H - 200)
    shadow = pygame.Rect(panel.x + 5, panel.y + 7, panel.w, panel.h)
    pygame.draw.rect(screen, (13, 15, 20), shadow, border_radius=14)
    pygame.draw.rect(screen, PANEL, panel, border_radius=14)
    pygame.draw.rect(screen, PANEL_BORDER, panel, width=1, border_radius=14)

    row_h = 86
    for i, row in enumerate(BUFFS):
        name, desc, hp, san, money, _cost = row
        y = panel.y + 16 + i * row_h

        is_cursor = (i == selector.cursor)
        is_selected = (i in selector.selected)
        row_rect = pygame.Rect(panel.x + 18, y - 6, panel.w - 36, 72)
        fill = PANEL_SOFT if is_cursor else PANEL_DARK
        border = MONEY_COLOR if is_selected else (ACCENT if is_cursor else PANEL_BORDER)
        pygame.draw.rect(screen, fill, row_rect, border_radius=10)
        pygame.draw.rect(screen, border, row_rect, width=2 if is_selected else 1, border_radius=10)

        _draw_keycap(screen, f_small, str(i + 1), row_rect.x + 14, row_rect.y + 13, active=is_cursor)
        check_rect = pygame.Rect(row_rect.right - 52, row_rect.y + 19, 24, 24)
        pygame.draw.rect(screen, GOOD_COLOR if is_selected else PANEL, check_rect, border_radius=6)
        pygame.draw.rect(screen, border, check_rect, width=1, border_radius=6)

        bonus = _bonus_str(hp, san, money)
        color = MONEY_COLOR if is_selected else TEXT
        screen.blit(f_med.render(name, True, color), (row_rect.x + 62, row_rect.y + 10))
        bonus_surf = f_small.render(bonus, True, TEXT_DIM)
        screen.blit(bonus_surf, (row_rect.right - bonus_surf.get_width() - 92, row_rect.y + 15))

        flavour = BUFF_FLAVOUR.get(name, desc)
        screen.blit(f_small.render(flavour, True, TEXT_MUTED), (row_rect.x + 62, row_rect.y + 42))

    status = f"Selected: {len(selector.selected)} / {REQUIRED_SELECTION}"
    status_color = MONEY_COLOR if selector.is_ready() else TEXT_DIM
    surf = f_small.render(status, True, status_color)
    screen.blit(surf, ((SCREEN_W - surf.get_width()) // 2, SCREEN_H - 60))
