"""File I/O: load events library, save/load leaderboard."""

import json
from constants import EVENTS_PATH, LEADERBOARD_PATH


def load_events(filepath=EVENTS_PATH):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)["events"]


def save_score(days_survived, mode):
    with open(LEADERBOARD_PATH, "w", encoding="utf-8") as f:
        json.dump({"days": days_survived, "mode": mode}, f)


def load_score():
    try:
        with open(LEADERBOARD_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"days": 0, "mode": "None"}
