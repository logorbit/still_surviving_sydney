"""Event handling: wraps event dicts, applies player choices, manages the daily pool."""

from __future__ import annotations

import random


class Event:
    def __init__(self, data: dict):
        self.id = data["id"]
        self.category = data["category"]
        self.title = data["title"]
        self.repeatable = data.get("repeatable", True)
        self.description = data["description"]
        self.choices = data["choices"]

    def choice_count(self):
        return len(self.choices)

    def apply_choice(self, choice_index: int, player, daytime: bool = True) -> dict:
        c = self.choices[choice_index]
        hp = c.get("hp_change", 0)
        san = c.get("san_change", 0)
        money = c.get("money_change", 0)
        if daytime:
            pressure = player.apply_daytime_event(hp_change=hp, san_change=san, money_change=money)
        else:
            pressure = player.apply_stat_change(hp_change=hp, san_change=san, money_change=money)
        return {
            "result_text": c["result_text"],
            "hp_change": hp,
            "san_change": san,
            "money_change": money,
            "trigger_event": c.get("trigger_event"),
            "pressure": pressure,
        }


class EventPool:
    """Owns the event library. Tracks which non-repeatables have fired and queues triggered follow-ups."""

    def __init__(self, events_data, rng: random.Random | None = None):
        self.events_by_id = {e["id"]: Event(e) for e in events_data}
        self.available_ids = [e["id"] for e in events_data]
        self.rng = rng or random.Random()
        self._pending_trigger_id = None

    def draw_today(self) -> list[Event]:
        # 2 or 3 events per day, weighted toward 2 (plan section 8).
        n = self.rng.choice([2, 2, 3])
        pool = list(self.available_ids)
        self.rng.shuffle(pool)
        return [self.events_by_id[eid] for eid in pool[:n]]

    def consume(self, event: Event) -> None:
        if not event.repeatable and event.id in self.available_ids:
            self.available_ids.remove(event.id)

    def queue_trigger(self, event_id: str | None) -> None:
        if event_id and event_id in self.events_by_id:
            self._pending_trigger_id = event_id

    def pop_trigger(self) -> Event | None:
        if self._pending_trigger_id is None:
            return None
        ev = self.events_by_id[self._pending_trigger_id]
        self._pending_trigger_id = None
        return ev
