"""Player state: HP, San, Money, buff application, day-based flags."""

from constants import HP_MAX, SAN_MAX, HP_START, SAN_START, MONEY_START


class Player:
    def __init__(self, buffs=None):
        self.hp = HP_START
        self.san = SAN_START
        self.money = MONEY_START
        self.buffs = []
        self.sleep_used_today = False
        if buffs:
            self.apply_buffs(buffs)

    def apply_buffs(self, buff_rows):
        for row in buff_rows:
            name, _desc, hp_bonus, san_bonus, money_bonus, _cost = row
            self.buffs.append(name)
            self.hp = min(HP_MAX, self.hp + hp_bonus)
            self.san = min(SAN_MAX, self.san + san_bonus)
            self.money += money_bonus

    def _clamp_stats(self, hp_change=0, san_change=0, money_change=0):
        old_hp, old_san, old_money = self.hp, self.san, self.money
        self.hp = max(0, min(HP_MAX, self.hp + hp_change))
        self.san = max(0, min(SAN_MAX, self.san + san_change))
        self.money = max(0, self.money + money_change)
        return {
            "hp_change": self.hp - old_hp,
            "san_change": self.san - old_san,
            "money_change": self.money - old_money,
        }

    def _adjust_san_loss(self, san_change):
        if "Optimist" in self.buffs and san_change < 0:
            return int(san_change * 0.8)
        return san_change

    def _adjust_hp_change(self, hp_change):
        if "Iron Stomach" in self.buffs and hp_change < 0:
            return int(hp_change * 0.8)
        return hp_change

    def _adjust_money_change(self, money_change):
        if "Scholarship" in self.buffs and money_change < 0:
            return int(money_change * 0.8)
        return money_change

    def _apply_passives(self, hp_change=0, san_change=0, money_change=0):
        return (
            self._adjust_hp_change(hp_change),
            self._adjust_san_loss(san_change),
            self._adjust_money_change(money_change),
        )

    def _apply_pressure_effects(self):
        hp_penalty = 0
        san_penalty = 0
        money_penalty = 0
        reasons = []

        if self.hp < 15:
            hp_penalty -= 2
            san_penalty -= 6
            money_penalty -= 35
            reasons.append("critical health")
        elif self.hp < 30:
            san_penalty -= 4
            money_penalty -= 20
            reasons.append("low health")
        elif self.hp < 50:
            san_penalty -= 2
            reasons.append("tired body")

        if self.san < 15:
            hp_penalty -= 6
            san_penalty -= 2
            money_penalty -= 30
            reasons.append("mental crash")
        elif self.san < 30:
            hp_penalty -= 4
            money_penalty -= 15
            reasons.append("high stress")
        elif self.san < 50:
            hp_penalty -= 2
            reasons.append("stress fatigue")

        hp_penalty, san_penalty, money_penalty = self._apply_passives(
            hp_penalty, san_penalty, money_penalty
        )
        actual = self._clamp_stats(hp_penalty, san_penalty, money_penalty)
        if not reasons or not any(actual.values()):
            return None
        actual["reasons"] = reasons
        return actual

    def apply_stat_change(self, hp_change=0, san_change=0, money_change=0):
        hp_change, san_change, money_change = self._apply_passives(
            hp_change, san_change, money_change
        )
        self._clamp_stats(hp_change, san_change, money_change)
        return self._apply_pressure_effects()


    # Social Butterfly: social confidence turns good daytime outcomes into
    # stronger morale and small money opportunities.
    def apply_daytime_event(self, hp_change=0, san_change=0, money_change=0):
        if "Social Butterfly" in self.buffs:
            if san_change > 0:
                san_change = int(san_change * 1.2)
            if money_change > 0:
                money_change = int(money_change * 1.1)

        # Night Owl: daytime gains reduced (tired from staying up).
        if "Night Owl" in self.buffs:
            if hp_change > 0:
                hp_change = int(hp_change * 0.8)
            if san_change > 0:
                san_change = int(san_change * 0.8)
        return self.apply_stat_change(hp_change, san_change, money_change)

    def new_day(self):
        self.sleep_used_today = False

    def can_sleep(self):
        return "Night Owl" in self.buffs and not self.sleep_used_today

    def use_sleep_skip(self):
        self.hp = min(HP_MAX, self.hp + 15)
        self.san = max(0, self.san - 5)
        self.sleep_used_today = True

    def check_status(self):
        if self.hp <= 0:
            return "hp_zero"
        if self.san <= 0:
            return "san_zero"
        if self.money <= 0:
            return "broke"
        return "alive"

    def is_alive(self):
        return self.check_status() == "alive"

    def get_stats(self):
        return {"hp": self.hp, "san": self.san, "money": self.money}
