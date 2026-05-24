"""
Controls:
  Title / Day intro / Result / Evening result : SPACE to advance
  Mode select        : 1 = Hardcore, 2 = Time
  Buff select        : ↑/↓ (or W/S) move, SPACE toggle, ENTER confirm (need 2)
  Event / Evening    : 1 / 2 / 3 choice
  Ending             : ENTER restart, ESC quit
"""

from __future__ import annotations

import os
import re
import sys
import random

os.environ.setdefault("SDL_VIDEO_ALLOW_HIGHDPI", "1")

import pygame
import pygame.freetype

from constants import (
    SCREEN_W, SCREEN_H, FPS,
    BG, BG_TOP, BG_BOTTOM, PANEL, PANEL_DARK, PANEL_SOFT, PANEL_BORDER,
    TEXT, TEXT_DIM, TEXT_MUTED, BAR_BG, ACCENT,
    HP_COLOR, SAN_COLOR, MONEY_COLOR, GOOD_COLOR,
    HP_MAX, SAN_MAX, SEMESTER_DAYS,
    FONT_SIZE_LARGE, FONT_SIZE_MEDIUM, FONT_SIZE_SMALL,
    MODE_HARDCORE, MODE_TIME,
)
from player import Player
from save import load_events, load_score, save_score
from event import EventPool
from buff import BuffSelector, draw_buff_select
from ending import determine_ending, draw_ending, FAILURE, GAME_OVER


# State constants
STATE_TITLE = "title"
STATE_MODE_SELECT = "mode_select"
STATE_BUFF_SELECT = "buff_select"
STATE_DAY_INTRO = "day_intro"
STATE_EVENT = "event"
STATE_RESULT = "result"
STATE_EVENING = "evening"
STATE_EVENING_RESULT = "evening_result"
STATE_ENDING = "ending"

EVENING_CHOICES = [
    ("[1] Sleep early",  12,   0,   0),
    ("[2] Play games",    0,  12,   0),
    ("[3] Work a shift", -8,   0,  90),
]

CHOICE_KEYS = {
    pygame.K_1: 0, pygame.K_KP1: 0,
    pygame.K_2: 1, pygame.K_KP2: 1,
    pygame.K_3: 2, pygame.K_KP3: 2,
}
MODE_KEY_HARDCORE = (pygame.K_1, pygame.K_KP1)
MODE_KEY_TIME     = (pygame.K_2, pygame.K_KP2)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOCAL_FONT_REGULAR = os.path.join(BASE_DIR, "assets", "fonts", "Inter-Regular.ttf")
LOCAL_FONT_BOLD = os.path.join(BASE_DIR, "assets", "fonts", "Inter-Bold.ttf")
SYSTEM_FONT_REGULAR = "/System/Library/Fonts/SFNS.ttf"
SYSTEM_FONT_BOLD = "/System/Library/Fonts/SFNS.ttf"


#Rendering helpers

class UIFont:
    """Small adapter so pygame.freetype works with the existing render calls."""

    def __init__(self, size: int, bold: bool = False):
        candidates = [
            LOCAL_FONT_BOLD if bold else LOCAL_FONT_REGULAR,
            SYSTEM_FONT_BOLD if bold else SYSTEM_FONT_REGULAR,
            "/System/Library/Fonts/Helvetica.ttc",
        ]
        self.font = None
        for path in candidates:
            if os.path.exists(path):
                try:
                    self.font = pygame.freetype.Font(path, size)
                    break
                except (OSError, RuntimeError):
                    continue
        if self.font is None:
            self.font = pygame.freetype.SysFont("Helvetica", size)
        self.font.pad = True
        self.font.strong = bold

    def render(self, text, antialias=True, color=TEXT):
        surf, _rect = self.font.render(str(text), fgcolor=color)
        return surf

    def size(self, text):
        rect = self.font.get_rect(str(text))
        return rect.width, rect.height

def clean_text(s: str) -> str:
    """Normalize generated event text before rendering."""
    return re.sub(r"\s{2,}", " ", s).strip()


TAG_COLORS = {
    "[STUDY]": SAN_COLOR,
    "[RISK]": HP_COLOR,
    "[HELP]": ACCENT,
    "[REST]": GOOD_COLOR,
    "[WORK]": MONEY_COLOR,
    "[MONEY]": MONEY_COLOR,
    "[SOCIAL]": (210, 145, 245),
    "[FOOD]": (245, 160, 96),
    "[ADMIN]": TEXT_DIM,
    "[HOME]": (140, 210, 170),
    "[AUS]": (90, 210, 210),
    "[LUCK]": (255, 220, 110),
    "[SAFE]": GOOD_COLOR,
}


def split_choice_tag(text):
    if text.startswith("["):
        end = text.find("]")
        if end != -1:
            return text[:end + 1], text[end + 1:].strip()
    return None, text


def render_choice_line(screen, font, text, x, y):
    tag, body = split_choice_tag(text)
    if tag:
        tag_surf = font.render(tag, True, TAG_COLORS.get(tag, ACCENT))
        body_surf = font.render(body, True, TEXT)
        screen.blit(tag_surf, (x, y))
        screen.blit(body_surf, (x + tag_surf.get_width() + 8, y))
        return max(tag_surf.get_height(), body_surf.get_height())

    surf = font.render(text, True, TEXT)
    screen.blit(surf, (x, y))
    return surf.get_height()


def wrap_text(text, font, max_width):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if font.size(trial)[0] <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def render_lines(screen, lines, font, x, y, color, line_gap=4):
    for ln in lines:
        surf = font.render(ln, True, color)
        screen.blit(surf, (x, y))
        y += surf.get_height() + line_gap
    return y


def draw_background(screen):
    for y in range(SCREEN_H):
        t = y / (SCREEN_H - 1)
        color = tuple(
            int(BG_TOP[i] * (1 - t) + BG_BOTTOM[i] * t)
            for i in range(3)
        )
        pygame.draw.line(screen, color, (0, y), (SCREEN_W, y))
    pygame.draw.rect(screen, (25, 34, 47), (0, 0, SCREEN_W, 150))
    pygame.draw.line(screen, (55, 78, 102), (0, 150), (SCREEN_W, 150), 1)


def draw_title_skyline(screen):
    base_y = SCREEN_H - 86
    color = (18, 25, 34)
    accent = (39, 61, 78)
    buildings = [
        (48, 68), (86, 112), (126, 82), (170, 132), (218, 92), (264, 118),
        (322, 76), (372, 146), (430, 96), (486, 122), (548, 84), (604, 138),
        (672, 104), (728, 126), (784, 74), (832, 116), (884, 86),
    ]
    for x, h in buildings:
        w = 34 if h < 100 else 42
        pygame.draw.rect(screen, color, (x, base_y - h, w, h))
        if h > 115:
            pygame.draw.rect(screen, accent, (x + 8, base_y - h - 14, w - 16, 14))
    pygame.draw.rect(screen, color, (0, base_y, SCREEN_W, 86))
    pygame.draw.line(screen, (55, 78, 102), (0, base_y), (SCREEN_W, base_y), 1)


def draw_panel(screen, rect, fill=PANEL, border=PANEL_BORDER, radius=12):
    shadow = pygame.Rect(rect.x + 5, rect.y + 7, rect.w, rect.h)
    pygame.draw.rect(screen, (13, 15, 20), shadow, border_radius=radius)
    pygame.draw.rect(screen, fill, rect, border_radius=radius)
    pygame.draw.rect(screen, border, rect, width=1, border_radius=radius)


def draw_keycap(screen, font, text, x, y, active=False):
    color = ACCENT if active else PANEL_SOFT
    text_w = font.size(text)[0]
    rect = pygame.Rect(x, y, max(38, text_w + 20), 30)
    pygame.draw.rect(screen, color, rect, border_radius=8)
    label = font.render(text, True, BG if active else TEXT)
    screen.blit(label, (rect.centerx - label.get_width() // 2,
                        rect.centery - label.get_height() // 2))
    return rect.right + 12


def draw_title_stat_card(screen, fonts, rect, label, description, color):
    _f_large, f_med, f_small = fonts
    pygame.draw.rect(screen, PANEL_DARK, rect, border_radius=12)
    pygame.draw.rect(screen, PANEL_BORDER, rect, width=1, border_radius=12)
    pygame.draw.circle(screen, color, (rect.x + 24, rect.y + 26), 7)
    screen.blit(f_med.render(label, True, TEXT), (rect.x + 44, rect.y + 14))
    screen.blit(f_small.render(description, True, TEXT_MUTED), (rect.x + 20, rect.y + 48))


def draw_primary_button(screen, fonts, rect):
    _f_large, f_med, f_small = fonts
    pygame.draw.rect(screen, ACCENT, rect, border_radius=14)
    pygame.draw.rect(screen, (151, 216, 255), rect, width=1, border_radius=14)
    key_rect = pygame.Rect(rect.x + 22, rect.y + 15, 84, 34)
    pygame.draw.rect(screen, (22, 24, 31), key_rect, border_radius=9)
    key = f_small.render("SPACE", True, ACCENT)
    screen.blit(key, (key_rect.centerx - key.get_width() // 2,
                      key_rect.centery - key.get_height() // 2))
    label = f_med.render("Start Survival", True, (16, 23, 31))
    screen.blit(label, (key_rect.right + 22, rect.y + 16))


def draw_bar(screen, x, y, w, h, value, max_value, color):
    pygame.draw.rect(screen, BAR_BG, (x, y, w, h), border_radius=6)
    fill_w = int(w * max(0.0, min(1.0, value / max_value)))
    if fill_w > 0:
        pygame.draw.rect(screen, color, (x, y, fill_w, h), border_radius=6)


def draw_top_hud(screen, fonts, player, day, mode):
    f_large, f_med, f_small = fonts
    screen.blit(f_large.render("Still Surviving Sydney", True, TEXT), (30, 22))

    if mode == MODE_HARDCORE:
        day_str = f"Day {day} / {SEMESTER_DAYS}"
    else:
        day_str = f"Day {day}  ·  Time Mode"
    day_surf = f_med.render(day_str, True, TEXT)
    day_rect = pygame.Rect(SCREEN_W - day_surf.get_width() - 54, 28,
                           day_surf.get_width() + 28, 36)
    pygame.draw.rect(screen, PANEL_DARK, day_rect, border_radius=10)
    pygame.draw.rect(screen, PANEL_BORDER, day_rect, width=1, border_radius=10)
    screen.blit(day_surf, (day_rect.x + 14, day_rect.y + 5))

    stats = [
        ("HP", player.hp, HP_MAX, HP_COLOR, True),
        ("San", player.san, SAN_MAX, SAN_COLOR, True),
        ("Money", player.money, None, MONEY_COLOR, False),
    ]
    for i, (name, value, maximum, color, has_bar) in enumerate(stats):
        card = pygame.Rect(30 + i * 220, 82, 194, 48)
        pygame.draw.rect(screen, PANEL_DARK, card, border_radius=10)
        pygame.draw.rect(screen, PANEL_BORDER, card, width=1, border_radius=10)
        value_text = f"${value}" if name == "Money" else f"{value}/{maximum}"
        screen.blit(f_small.render(name, True, TEXT_MUTED), (card.x + 14, card.y + 7))
        value_surf = f_small.render(value_text, True, color if name == "Money" else TEXT)
        value_y = card.y + 18 if name == "Money" else card.y + 7
        screen.blit(value_surf, (card.right - value_surf.get_width() - 14, value_y))
        if has_bar:
            draw_bar(screen, card.x + 14, card.y + 30, card.w - 28, 8, value, maximum, color)


# Screen renderers

def screen_title(screen, fonts, best_score):
    f_large, f_med, f_small = fonts
    draw_title_skyline(screen)

    eyebrow = f_small.render("COMP9001 FINAL PROJECT", True, ACCENT)
    screen.blit(eyebrow, ((SCREEN_W - eyebrow.get_width()) // 2, 110))

    title = f_large.render("Still Surviving Sydney", True, TEXT)
    screen.blit(title, ((SCREEN_W - title.get_width()) // 2, 150))

    sub = f_med.render("Survive everyday Aussie problems as an international student.", True, TEXT_DIM)
    screen.blit(sub, ((SCREEN_W - sub.get_width()) // 2, 210))

    hook = f_small.render("Assignments, rent, culture shock, and one more day to survive.", True, TEXT_MUTED)
    screen.blit(hook, ((SCREEN_W - hook.get_width()) // 2, 252))

    card_y = 320
    card_w = 236
    gap = 22
    start_x = (SCREEN_W - card_w * 3 - gap * 2) // 2
    cards = [
        ("HP", "Body condition", HP_COLOR),
        ("San", "Mental state", SAN_COLOR),
        ("Money", "Rent, food, transport", MONEY_COLOR),
    ]
    for i, (label, desc, color) in enumerate(cards):
        draw_title_stat_card(
            screen, fonts,
            pygame.Rect(start_x + i * (card_w + gap), card_y, card_w, 86),
            label, desc, color,
        )

    draw_primary_button(screen, fonts, pygame.Rect((SCREEN_W - 300) // 2, 448, 300, 64))

    days = best_score.get("days", 0)
    if days > 0:
        badge = pygame.Rect((SCREEN_W - 236) // 2, 542, 236, 76)
        pygame.draw.rect(screen, PANEL_DARK, badge, border_radius=12)
        pygame.draw.rect(screen, MONEY_COLOR, badge, width=1, border_radius=12)
        label = f_small.render("BEST RUN", True, TEXT_MUTED)
        value = f_med.render(f"{days} day(s)", True, MONEY_COLOR)
        mode = f_small.render("Time Mode", True, TEXT_DIM)
        screen.blit(label, (badge.centerx - label.get_width() // 2, badge.y + 10))
        screen.blit(value, (badge.centerx - value.get_width() // 2, badge.y + 30))
        screen.blit(mode, (badge.centerx - mode.get_width() // 2, badge.y + 54))


def screen_mode_select(screen, fonts, best_score):
    f_large, f_med, f_small = fonts
    title = f_large.render("Choose Your Mode", True, TEXT)
    screen.blit(title, ((SCREEN_W - title.get_width()) // 2, 60))

    panel = pygame.Rect(80, 160, SCREEN_W - 160, 380)
    draw_panel(screen, panel, radius=14)

    # Hardcore
    y = panel.y + 30
    draw_keycap(screen, f_small, "1", panel.x + 40, y - 3, active=True)
    screen.blit(f_med.render("One-Life Mode (Hardcore)", True, HP_COLOR), (panel.x + 92, y))
    for ln in [
        "Survive exactly 15 days. One chance only.",
        "Ending depends on final stats:",
        "    Perfect — all stats above 60",
        "    Normal  — you made it through",
        "    Failure — any stat hits 0",
    ]:
        y += 26
        screen.blit(f_small.render(ln, True, TEXT_DIM), (panel.x + 60, y))

    # Time
    y = panel.y + 210
    draw_keycap(screen, f_small, "2", panel.x + 40, y - 3, active=True)
    screen.blit(f_med.render("Time Mode (Endless)", True, MONEY_COLOR), (panel.x + 92, y))
    for ln in [
        "No day limit — survive as long as you can.",
        "Game ends when any stat hits 0.",
        "Your best run is saved to the leaderboard.",
    ]:
        y += 26
        screen.blit(f_small.render(ln, True, TEXT_DIM), (panel.x + 60, y))

    if best_score.get("days", 0) > 0:
        rec = f_small.render(f"Current record: {best_score['days']} day(s)", True, MONEY_COLOR)
        screen.blit(rec, (panel.x + 60, y + 32))


def screen_day_intro(screen, fonts, day, mode):
    f_large, f_med, f_small = fonts
    if mode == MODE_HARDCORE:
        msg = f"Day {day} of {SEMESTER_DAYS}"
    else:
        msg = f"Day {day}"
    intro = f_small.render("A new day in Sydney", True, ACCENT)
    screen.blit(intro, ((SCREEN_W - intro.get_width()) // 2, SCREEN_H // 2 - 110))
    title = f_large.render(msg, True, TEXT)
    screen.blit(title, ((SCREEN_W - title.get_width()) // 2, SCREEN_H // 2 - 60))
    hint = f_small.render("Press SPACE to begin the day", True, TEXT_DIM)
    screen.blit(hint, ((SCREEN_W - hint.get_width()) // 2, SCREEN_H // 2 + 22))


def screen_event(screen, fonts, event, player, day, mode):
    f_large, f_med, f_small = fonts
    draw_top_hud(screen, fonts, player, day, mode)

    panel = pygame.Rect(20, 140, SCREEN_W - 40, SCREEN_H - 160)
    draw_panel(screen, panel, radius=14)

    cat = f_small.render(event.category.upper(), True, ACCENT)
    screen.blit(cat, (44, 160))
    screen.blit(f_med.render(clean_text(event.title), True, TEXT), (40, 182))

    desc_lines = wrap_text(clean_text(event.description), f_small, SCREEN_W - 100)
    y = render_lines(screen, desc_lines, f_small, 40, 230, TEXT, line_gap=10)
    y += 20

    for i, c in enumerate(event.choices):
        key = "123"[i]
        text = clean_text(c['text'])
        lines = wrap_text(text, f_small, SCREEN_W - 170)
        option_h = max(48, 22 + len(lines) * 23)
        option_rect = pygame.Rect(48, y, SCREEN_W - 96, option_h)
        pygame.draw.rect(screen, PANEL_DARK, option_rect, border_radius=10)
        pygame.draw.rect(screen, PANEL_BORDER, option_rect, width=1, border_radius=10)
        draw_keycap(screen, f_small, key, option_rect.x + 14, option_rect.y + 9, active=True)
        line_y = option_rect.y + 13
        for j, ln in enumerate(lines):
            if j == 0:
                line_h = render_choice_line(screen, f_small, ln, option_rect.x + 68, line_y)
            else:
                surf = f_small.render(ln, True, TEXT)
                screen.blit(surf, (option_rect.x + 68, line_y))
                line_h = surf.get_height()
            line_y += line_h + 4
        y += option_h + 12


def screen_result(screen, fonts, result, player, day, mode, header="Result"):
    f_large, f_med, f_small = fonts
    draw_top_hud(screen, fonts, player, day, mode)

    panel = pygame.Rect(20, 140, SCREEN_W - 40, SCREEN_H - 160)
    draw_panel(screen, panel, radius=14)

    screen.blit(f_med.render(header, True, ACCENT), (40, 162))

    lines = wrap_text(clean_text(result["result_text"]), f_small, SCREEN_W - 100)
    y = render_lines(screen, lines, f_small, 40, 210, TEXT, line_gap=9)
    y += 26

    parts = []
    if result["hp_change"]:    parts.append(f"HP {result['hp_change']:+d}")
    if result["san_change"]:   parts.append(f"San {result['san_change']:+d}")
    if result["money_change"]: parts.append(f"Money {result['money_change']:+d}")
    if parts:
        change_box = pygame.Rect(40, y, SCREEN_W - 100, 48)
        pygame.draw.rect(screen, PANEL_DARK, change_box, border_radius=10)
        screen.blit(f_med.render("   ".join(parts), True, TEXT), (change_box.x + 18, change_box.y + 10))
        y += 64

    pressure = result.get("pressure")
    if pressure:
        extra = []
        if pressure["hp_change"]:    extra.append(f"HP {pressure['hp_change']:+d}")
        if pressure["san_change"]:   extra.append(f"San {pressure['san_change']:+d}")
        if pressure["money_change"]: extra.append(f"Money {pressure['money_change']:+d}")
        reason = ", ".join(pressure["reasons"])
        text = f"Pressure penalty ({reason}): {'   '.join(extra)}"
        pressure_box = pygame.Rect(40, y, SCREEN_W - 100, 48)
        pygame.draw.rect(screen, (54, 37, 44), pressure_box, border_radius=10)
        pygame.draw.rect(screen, HP_COLOR, pressure_box, width=1, border_radius=10)
        screen.blit(f_small.render(text, True, TEXT), (pressure_box.x + 18, pressure_box.y + 14))

    hint = f_small.render("Press SPACE to continue", True, TEXT_DIM)
    screen.blit(hint, (40, SCREEN_H - 50))


def screen_evening(screen, fonts, player, day, mode):
    f_large, f_med, f_small = fonts
    draw_top_hud(screen, fonts, player, day, mode)

    panel = pygame.Rect(20, 140, SCREEN_W - 40, SCREEN_H - 160)
    draw_panel(screen, panel, radius=14)

    screen.blit(f_med.render("Evening — how do you spend it?", True, TEXT), (40, 170))

    y = 240
    night_owl = "Night Owl" in player.buffs
    for i, (label, hp, san, money) in enumerate(EVENING_CHOICES):
        suffix = ""
        if i == 2 and night_owl:
            hp, money = 0, 120
            suffix = "  (Night Owl bonus)"
        deltas = []
        if hp:    deltas.append(f"HP {hp:+d}")
        if san:   deltas.append(f"San {san:+d}")
        if money: deltas.append(f"Money {money:+d}")
        option = pygame.Rect(48, y - 10, SCREEN_W - 96, 48)
        pygame.draw.rect(screen, PANEL_DARK, option, border_radius=10)
        pygame.draw.rect(screen, PANEL_BORDER, option, width=1, border_radius=10)
        draw_keycap(screen, f_small, str(i + 1), option.x + 14, option.y + 9, active=True)
        full = f"{label[4:]}    ({', '.join(deltas)}){suffix}"
        screen.blit(f_small.render(full, True, TEXT), (option.x + 68, option.y + 14))
        y += 62


#Game state machine

class Game:
    def __init__(self, seed=None):
        self.rng = random.Random(seed)
        self.events_data = load_events()
        self.best_score = load_score()

        self.mode: str | None = None
        self.buff_selector = BuffSelector()
        self.player: Player | None = None
        self.pool: EventPool | None = None

        self.day = 1
        self.days_survived = 0
        self.state = STATE_TITLE

        self.todays_queue: list = []
        self.current_event = None
        self.last_result = None
        self.death_reason: str | None = None
        self.ending_key: str | None = None
        self.is_new_record = False
        self.previous_best = self.best_score.get("days", 0)

    def reset(self):
        self.__init__()

    def begin_game(self):
        self.player = Player(buffs=self.buff_selector.get_selected_rows())
        self.pool = EventPool(self.events_data, rng=self.rng)
        self.day = 1
        self.state = STATE_DAY_INTRO

    def begin_day(self):
        self.player.new_day()
        self.todays_queue = self.pool.draw_today()
        self._advance_to_next_event_or_evening()

    def _advance_to_next_event_or_evening(self):
        triggered = self.pool.pop_trigger()
        if triggered is not None:
            self.current_event = triggered
            self.state = STATE_EVENT
        elif self.todays_queue:
            self.current_event = self.todays_queue.pop(0)
            self.state = STATE_EVENT
        else:
            self.current_event = None
            self.state = STATE_EVENING

    def _check_death_then_continue(self, on_alive):
        if not self.player.is_alive():
            self.death_reason = self.player.check_status()
            self._finalize_ending(alive=False)
        else:
            on_alive()

    def _finalize_ending(self, alive: bool):
        if alive:
            self.days_survived = SEMESTER_DAYS  # only hardcore reaches "alive end"
        else:
            self.days_survived = self.day - 1  # full days completed before death-day

        self.ending_key = determine_ending(self.mode, self.player, alive)

        if self.mode == MODE_TIME and not alive:
            if self.days_survived > self.previous_best:
                self.is_new_record = True
                save_score(self.days_survived, "time")

        self.state = STATE_ENDING

    def handle_key(self, key):
        s = self.state

        if s == STATE_TITLE:
            if key == pygame.K_SPACE:
                self.state = STATE_MODE_SELECT

        elif s == STATE_MODE_SELECT:
            if key in MODE_KEY_HARDCORE:
                self.mode = MODE_HARDCORE
                self.state = STATE_BUFF_SELECT
            elif key in MODE_KEY_TIME:
                self.mode = MODE_TIME
                self.state = STATE_BUFF_SELECT

        elif s == STATE_BUFF_SELECT:
            if key in (pygame.K_UP, pygame.K_w):
                self.buff_selector.move(-1)
            elif key in (pygame.K_DOWN, pygame.K_s):
                self.buff_selector.move(1)
            elif key == pygame.K_SPACE:
                self.buff_selector.toggle()
            elif key == pygame.K_RETURN and self.buff_selector.is_ready():
                self.begin_game()

        elif s == STATE_DAY_INTRO:
            if key == pygame.K_SPACE:
                self.begin_day()

        elif s == STATE_EVENT:
            if key in CHOICE_KEYS:
                idx = CHOICE_KEYS[key]
                if idx < self.current_event.choice_count():
                    self.last_result = self.current_event.apply_choice(idx, self.player, daytime=True)
                    self.pool.consume(self.current_event)
                    self.pool.queue_trigger(self.last_result["trigger_event"])
                    self.state = STATE_RESULT

        elif s == STATE_RESULT:
            if key == pygame.K_SPACE:
                self._check_death_then_continue(self._advance_to_next_event_or_evening)

        elif s == STATE_EVENING:
            if key in CHOICE_KEYS:
                idx = CHOICE_KEYS[key]
                label, hp, san, money = EVENING_CHOICES[idx]
                if idx == 2 and "Night Owl" in self.player.buffs:
                    hp, money = 0, 120
                pressure = self.player.apply_stat_change(hp_change=hp, san_change=san, money_change=money)
                self.last_result = {
                    "result_text": f"You chose: {label}.",
                    "hp_change": hp, "san_change": san, "money_change": money,
                    "trigger_event": None,
                    "pressure": pressure,
                }
                self.state = STATE_EVENING_RESULT

        elif s == STATE_EVENING_RESULT:
            if key == pygame.K_SPACE:
                self._check_death_then_continue(self._next_day)

        elif s == STATE_ENDING:
            if key == pygame.K_RETURN:
                self.reset()

    def _next_day(self):
        self.day += 1
        if self.mode == MODE_HARDCORE and self.day > SEMESTER_DAYS:
            self._finalize_ending(alive=True)
        else:
            self.state = STATE_DAY_INTRO

    def render(self, screen, fonts):
        draw_background(screen)
        s = self.state
        if s == STATE_TITLE:
            screen_title(screen, fonts, self.best_score)
        elif s == STATE_MODE_SELECT:
            screen_mode_select(screen, fonts, self.best_score)
        elif s == STATE_BUFF_SELECT:
            draw_buff_select(screen, fonts, self.buff_selector)
        elif s == STATE_DAY_INTRO:
            screen_day_intro(screen, fonts, self.day, self.mode)
        elif s == STATE_EVENT:
            screen_event(screen, fonts, self.current_event, self.player, self.day, self.mode)
        elif s == STATE_RESULT:
            screen_result(screen, fonts, self.last_result, self.player, self.day, self.mode)
        elif s == STATE_EVENING:
            screen_evening(screen, fonts, self.player, self.day, self.mode)
        elif s == STATE_EVENING_RESULT:
            screen_result(screen, fonts, self.last_result, self.player, self.day, self.mode, header="Evening")
        elif s == STATE_ENDING:
            draw_ending(
                screen, fonts,
                ending_key=self.ending_key,
                mode=self.mode,
                player=self.player,
                days_survived=self.days_survived,
                death_reason=self.death_reason,
                is_new_record=self.is_new_record,
                previous_best=self.previous_best,
            )


def main():
    pygame.init()
    pygame.freetype.init()
    pygame.display.set_caption("Still Surviving Sydney")
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    clock = pygame.time.Clock()

    fonts = (
        UIFont(FONT_SIZE_LARGE, bold=True),
        UIFont(FONT_SIZE_MEDIUM),
        UIFont(FONT_SIZE_SMALL),
    )

    game = Game()

    running = True
    while running:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    running = False
                else:
                    game.handle_key(ev.key)

        game.render(screen, fonts)
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
