"""Poker Dice: hand-ranking roll-off. Each player privately rolls 5 dice, up
to 3 rolls total, choosing which dice to hold between rolls. No bluffing —
everyone plays simultaneously, then hands are revealed and ranked.
"""
from __future__ import annotations

import random
from collections import Counter

MAX_ROLLS = 3
CATEGORY_NAMES = {
    6: "Five of a Kind", 5: "Four of a Kind", 4: "Full House", 3: "Three of a Kind",
    2: "Two Pair", 1: "One Pair", 0: "High Die",
}


def evaluate_dice(dice: list[int]) -> tuple:
    counts = Counter(dice)
    groups = sorted(counts.items(), key=lambda kv: (kv[1], kv[0]), reverse=True)
    group_counts = [c for _, c in groups]
    group_ranks = [r for r, _ in groups]
    if group_counts[0] == 5:
        cat = 6
    elif group_counts[0] == 4:
        cat = 5
    elif group_counts[0] == 3 and len(group_counts) > 1 and group_counts[1] == 2:
        cat = 4
    elif group_counts[0] == 3:
        cat = 3
    elif group_counts[0] == 2 and len(group_counts) > 1 and group_counts[1] == 2:
        cat = 2
    elif group_counts[0] == 2:
        cat = 1
    else:
        cat = 0
    return (cat, *group_ranks)


class PokerDiceGame:
    game_type = "poker_dice"

    def __init__(self, player_ids: list[str]):
        self.order = list(player_ids)
        self.dice: dict[str, list[int]] = {pid: [0] * 5 for pid in self.order}
        self.rolls_used = {pid: 0 for pid in self.order}
        self.done = {pid: False for pid in self.order}
        self.phase = "rolling"  # "rolling" | "revealed"
        self.last_result: dict | None = None

    def apply_action(self, player_id: str, action: dict) -> None:
        if player_id not in self.order:
            raise ValueError("Not a player in this game.")
        if self.phase != "rolling":
            raise ValueError("Round already finished.")
        if self.done[player_id]:
            raise ValueError("You've already finished your rolls.")

        action_type = action.get("type")
        if action_type == "roll":
            self._apply_roll(player_id, action)
        elif action_type == "stand":
            self.done[player_id] = True
        else:
            raise ValueError(f"Unknown action: {action_type}")

        if all(self.done.values()):
            self._reveal()

    def _apply_roll(self, player_id: str, action: dict) -> None:
        used = self.rolls_used[player_id]
        if used >= MAX_ROLLS:
            raise ValueError("No rolls remaining.")

        keep = action.get("keep")
        if used == 0:
            self.dice[player_id] = [random.randint(1, 6) for _ in range(5)]
        else:
            if not isinstance(keep, list) or len(keep) != 5:
                raise ValueError("keep must be a 5-item boolean list.")
            self.dice[player_id] = [
                d if keep[i] else random.randint(1, 6) for i, d in enumerate(self.dice[player_id])
            ]
        self.rolls_used[player_id] = used + 1
        if self.rolls_used[player_id] >= MAX_ROLLS:
            self.done[player_id] = True

    def _reveal(self) -> None:
        scores = {pid: evaluate_dice(self.dice[pid]) for pid in self.order}
        best = max(scores.values())
        worst = min(scores.values())
        self.last_result = {
            "dice": {pid: list(vals) for pid, vals in self.dice.items()},
            "scores": {pid: {"category": CATEGORY_NAMES[s[0]], "rank": s} for pid, s in scores.items()},
            "winners": [pid for pid, s in scores.items() if s == best],
            "losers": [pid for pid, s in scores.items() if s == worst],
        }
        self.phase = "revealed"

    def start_next_round(self) -> None:
        if self.phase != "revealed":
            raise ValueError("Can't start a new round right now.")
        self.dice = {pid: [0] * 5 for pid in self.order}
        self.rolls_used = {pid: 0 for pid in self.order}
        self.done = {pid: False for pid in self.order}
        self.phase = "rolling"
        self.last_result = None

    def to_public_state(self, viewer_id: str) -> dict:
        return {
            "game": self.game_type,
            "phase": self.phase,
            "players": [
                {
                    "id": pid,
                    "rolls_used": self.rolls_used[pid],
                    "done": self.done[pid],
                }
                for pid in self.order
            ],
            "your_dice": self.dice.get(viewer_id, [0] * 5),
            "your_rolls_used": self.rolls_used.get(viewer_id, 0),
            "last_result": self.last_result,
        }
