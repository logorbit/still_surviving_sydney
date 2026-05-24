# Still Surviving Sydney

## About Game:

A text-based life simulator about surviving everyday Aussie problems as an international student doing a Master's in Au. Every in-game day throws 3 or more random events at you; every choice moves three stats (HP, San, Money). Survivea 15 day semester or last as long as you can in endless Time Mode.

## How it run:

1.Install Python 3 and Pygame

2.From the project folder:

```
python3 main.py
```

##Notes: Tested based on macOS(26.5) with Python 3.9 and Pygame 2.6.

## Control

| Screen          | Keys                                              |
| --------------- | ------------------------------------------------- |
| Title           | `SPACE` start                                     |
| Mode select     | `1` One-Life (Hardcore) · `2` Time Mode           |
| Buff select     | `↑` / `↓` move · `SPACE` toggle · `ENTER` confirm |
| Event / Evening | `1` / `2` / `3` choose                            |
| Result screens  | `SPACE` continue                                  |
| Ending          | `ENTER` restart · `ESC` quit anyw                 |

## Game Modes

1.One-Life Mode— 15 fixed days. One chance. Ending depends on final stats:

- Perfect— all three stats above 60
- Normal — you made it through
- Failure— any stat hit 0 before Day 15

2.Time Mode— endless. Game ends when any stat hits 0. Days survived are
  (saved to `leaderboard.json`; your best run shows on the title screen.)

## Pressure Mechanics

1.Low stats now create extra pressure after choices:

- Low HP: can drain San and Money because exhaustion leads to stress,
  medication, missed shifts, or messy decisions.
- Low San: can drain HP and Money because stress affects sleep, food, focus, and work.

2.The penalties are light at first and get stronger under 30 and 15, so the game warns the player before a full spiral.

## Buffs

Pick 2 of 5 before the run:

| Buff             | Effect                                                       |
| ---------------- | ------------------------------------------------------------ |
| Iron Stomach     | +10 HP at start, all HP losses × 0.8                         |
| Social Butterfly | +10 San at start, daytime San gains × 1.2, daytime Money gains × 1.1 |
| Scholarship      | +150 Money at start, all Money losses × 0.8                  |
| Night Owl        | +5 HP at start, daytime HP/San gains × 0.8, better Work shift in the evening (Money +120, HP −0 |
| Optimist         | +10 San at start, all San losses × 0.8                       |

## Score

The ending screen gives a score and grade based on days survived, final HP, final San, remaining Money, and ending quality.

## File Structure

```
survive_sydney/
├── main.py                # Game loop & state machine (title → ending)
├── player.py              # Player class — stats, buff application, Night Owl
├── event.py               # Event + EventPool — load, apply choice, day pool
├── buff.py                # BuffSelector + selection screen
├── ending.py               # Perfect / Normal / Failure logic & screen
├── save.py                 # JSON I/O for events + leaderboard
├── constants.py           # Colours, sizes, fonts, stat defaults, BUFFS table
├── events_cleaned.json    # 40 events (6 categories)
├── events.json           # older 20-event version kept as backup
└── README_FINALPROJECT.md
```





