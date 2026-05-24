"""Ending determination + screen rendering for both game modes."""

from __future__ import annotations

import pygame

from constants import (
    SCREEN_W, SCREEN_H,
    PANEL, PANEL_DARK, PANEL_BORDER,
    TEXT, TEXT_DIM, TEXT_MUTED, ACCENT, HP_COLOR, SAN_COLOR, MONEY_COLOR,
    MODE_HARDCORE, MODE_TIME,
    PERFECT_STAT_THRESHOLD, NORMAL_LOW_THRESHOLD,
    SEMESTER_DAYS,
)

# Ending keys
PERFECT = "perfect"
NORMAL = "normal"
FAILURE = "failure"
GAME_OVER = "game_over"


_TITLES = {
    PERFECT:   ("Perfect Ending",      MONEY_COLOR),
    NORMAL:    ("You Made It",         TEXT),
    FAILURE:   ("Game Over",           HP_COLOR),
    GAME_OVER: ("Game Over",           HP_COLOR),
}

_DEATH_FLAVOUR = {
    "hp_zero":  "Your body gave out.",
    "san_zero": "You couldn't take any more.",
    "broke":    "You ran out of money.",
}


def determine_ending(mode: str, player, alive: bool) -> str:
    """Return one of: perfect / normal / failure / game_over."""
    if not alive:
        return FAILURE if mode == MODE_HARDCORE else GAME_OVER
    # Survived the run (only meaningful for hardcore; time mode only ends on death)
    stats = (player.hp, player.san, player.money)
    if all(v > PERFECT_STAT_THRESHOLD for v in stats):
        return PERFECT
    return NORMAL


def calculate_score(mode: str, ending_key: str, player, days_survived: int) -> int:
    score = days_survived * 100
    score += player.hp * 2
    score += player.san * 2
    score += player.money // 10
    if mode == MODE_HARDCORE:
        if ending_key == PERFECT:
            score += 500
        elif ending_key == NORMAL:
            score += 200
    return max(0, score)


def score_grade(score: int) -> tuple[str, str]:
    if score >= 2600:
        return "S", "Excellent Survivor"
    if score >= 2150:
        return "A", "Strong Survivor"
    if score >= 1600:
        return "B", "Made It Through"
    if score >= 900:
        return "C", "Barely Survived"
    return "D", "Sydney Hit Hard"


def _ending_message(ending_key: str, mode: str, player, days_survived: int,
                    death_reason: str | None) -> str:
    if ending_key == PERFECT:
        return "You didn't just survive — you thrived. Master's secured."
    if ending_key == NORMAL:
        if min(player.hp, player.san) < NORMAL_LOW_THRESHOLD:
            return "You survived 15 days. Barely. But you survived."
        return "You made it through the semester, scars and all."
    if ending_key == FAILURE:
        flavour = _DEATH_FLAVOUR.get(death_reason or "", "Sydney wins this round.")
        return f"{flavour} You didn't make it."
    # GAME_OVER (time mode)
    return _DEATH_FLAVOUR.get(death_reason or "", "Your run ends here.")


def draw_ending(screen, fonts, *, ending_key: str, mode: str, player,
                days_survived: int, death_reason: str | None,
                is_new_record: bool, previous_best: int) -> None:
    f_large, f_med, f_small = fonts

    panel = pygame.Rect(120, 126, SCREEN_W - 240, 420)
    shadow = pygame.Rect(panel.x + 5, panel.y + 7, panel.w, panel.h)
    pygame.draw.rect(screen, (13, 15, 20), shadow, border_radius=16)
    pygame.draw.rect(screen, PANEL, panel, border_radius=16)
    pygame.draw.rect(screen, PANEL_BORDER, panel, width=1, border_radius=16)

    title_text, title_color = _TITLES[ending_key]
    title = f_large.render(title_text, True, title_color)
    screen.blit(title, ((SCREEN_W - title.get_width()) // 2, panel.y + 54))

    msg = _ending_message(ending_key, mode, player, days_survived, death_reason)
    msg_surf = f_med.render(msg, True, TEXT)
    screen.blit(msg_surf, ((SCREEN_W - msg_surf.get_width()) // 2, panel.y + 126))

    stat_y = panel.y + 188
    stats = [
        ("HP", str(player.hp), HP_COLOR),
        ("San", str(player.san), SAN_COLOR),
        ("Money", f"${player.money}", MONEY_COLOR),
    ]
    for i, (label, value, color) in enumerate(stats):
        card = pygame.Rect(panel.x + 72 + i * 170, stat_y, 132, 68)
        pygame.draw.rect(screen, PANEL_DARK, card, border_radius=10)
        pygame.draw.rect(screen, color, card, width=1, border_radius=10)
        screen.blit(f_small.render(label, True, TEXT_MUTED), (card.x + 16, card.y + 12))
        value_surf = f_med.render(value, True, TEXT)
        screen.blit(value_surf, (card.x + 16, card.y + 34))

    score = calculate_score(mode, ending_key, player, days_survived)
    grade, grade_label = score_grade(score)
    score_line = f"Score {score}   Grade {grade} - {grade_label}"
    score_surf = f_med.render(score_line, True, ACCENT)
    y = stat_y + 96
    screen.blit(score_surf, ((SCREEN_W - score_surf.get_width()) // 2, y))
    y += 48

    if mode == MODE_TIME:
        line = f"Days survived: {days_survived}"
        surf = f_med.render(line, True, TEXT)
        screen.blit(surf, ((SCREEN_W - surf.get_width()) // 2, y))
        y += 40
        if is_new_record:
            rec = f_med.render("★ New record! Saved to leaderboard. ★", True, MONEY_COLOR)
            screen.blit(rec, ((SCREEN_W - rec.get_width()) // 2, y))
        else:
            best = f_small.render(f"Best so far: {previous_best} day(s)", True, TEXT_DIM)
            screen.blit(best, ((SCREEN_W - best.get_width()) // 2, y))
        y += 40
    else:
        line = f"Days completed: {days_survived} / {SEMESTER_DAYS}"
        surf = f_small.render(line, True, TEXT_DIM)
        screen.blit(surf, ((SCREEN_W - surf.get_width()) // 2, y))
        y += 30

    hint = f_small.render("ENTER restart   ·   ESC quit", True, ACCENT)
    screen.blit(hint, ((SCREEN_W - hint.get_width()) // 2, SCREEN_H - 60))
