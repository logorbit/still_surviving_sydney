"""Shared constants: colours, dimensions, fonts, stat defaults, buff table."""

SCREEN_W = 960
SCREEN_H = 720
FPS = 30

BG = (22, 24, 31)
BG_TOP = (32, 37, 49)
BG_BOTTOM = (17, 18, 24)
PANEL = (42, 47, 61)
PANEL_DARK = (30, 34, 45)
PANEL_SOFT = (52, 58, 74)
PANEL_BORDER = (91, 101, 126)
TEXT = (242, 242, 246)
TEXT_DIM = (170, 176, 190)
TEXT_MUTED = (118, 126, 145)
BAR_BG = (67, 72, 87)
ACCENT = (105, 190, 255)
HP_COLOR = (235, 93, 107)
SAN_COLOR = (99, 170, 245)
MONEY_COLOR = (245, 205, 96)
GOOD_COLOR = (104, 210, 145)

FONT_SIZE_LARGE = 36
FONT_SIZE_MEDIUM = 24
FONT_SIZE_SMALL = 18

HP_MAX = 100
SAN_MAX = 100
HP_START = 80
SAN_START = 80
MONEY_START = 500

SEMESTER_DAYS = 15

MODE_HARDCORE = "hardcore"
MODE_TIME = "time"

PERFECT_STAT_THRESHOLD = 60   # Hardcore "Perfect" ending: all stats strictly above this.
NORMAL_LOW_THRESHOLD = 40     # Hardcore "barely" message: any stat below this.

# 2D buff table — [name, description, hp_bonus, san_bonus, money_bonus, cost]
BUFFS = [
    ["Iron Stomach",     "HP losses x0.8",                   10,   0,    0, 0],
    ["Social Butterfly", "Daytime San/Money gains boosted",   0,  10,    0, 0],
    ["Scholarship",      "Money losses x0.8",                 0,   0,  150, 0],
    ["Night Owl",        "Better evening work, weaker days",  5,   0,    0, 0],
    ["Optimist",         "San losses x0.8",                   0,  10,    0, 0],
]

EVENTS_PATH = "events_cleaned.json"
LEADERBOARD_PATH = "leaderboard.json"
