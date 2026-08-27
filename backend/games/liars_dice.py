"""Liar's Dice: standard rules, 5 dice per player, 1s wild (except when the
current bid is itself on 1s), loser of a challenge drops a die, eliminated at
zero, last player standing wins.
"""
from __future__ import annotations

import random

STARTING_DICE = 5


def _bid_key(qty: int, face: int) -> tuple[int, int]:
    # 1s are the strongest face at any given quantity (wild-die bidding).
    return (qty, 7 if face == 1 else face)


class LiarsDiceGame:
    game_type = "liars_dice"

    def __init__(self, player_ids: list[str]):
        self.order = list(player_ids)
        self.dice_count = {pid: STARTING_DICE for pid in self.order}
        self.dice_values: dict[str, list[int]] = {}
        self.current_bid: dict | None = None
        self.bidder: str | None = None
        self.turn_index = 0
        self.phase = "bidding"  # "bidding" | "revealed" | "game_over"
        self.last_result: dict | None = None
        self.winner: str | None = None
        self._roll_all()

    def _active_players(self) -> list[str]:
        return [pid for pid in self.order if self.dice_count[pid] > 0]

    def _roll_all(self) -> None:
        for pid in self._active_players():
            self.dice_values[pid] = [random.randint(1, 6) for _ in range(self.dice_count[pid])]
        self.current_bid = None
        self.bidder = None
        self.phase = "bidding"
        self.last_result = None

    def current_turn(self) -> str | None:
        active = self._active_players()
        if not active:
            return None
        return active[self.turn_index % len(active)]

    def _advance_turn_from(self, pid: str) -> None:
        active = self._active_players()
        if pid in active:
            self.turn_index = active.index(pid)
        else:
            self.turn_index = 0

    def apply_action(self, player_id: str, action: dict) -> None:
        if self.phase != "bidding":
            raise ValueError("Round is over — wait for the next round.")
        if player_id != self.current_turn():
            raise ValueError("It's not your turn.")

        action_type = action.get("type")
        if action_type == "bid":
            self._apply_bid(player_id, action)
        elif action_type == "call_liar":
            self._apply_call_liar(player_id)
        else:
            raise ValueError(f"Unknown action: {action_type}")

    def _apply_bid(self, player_id: str, action: dict) -> None:
        qty = action.get("qty")
        face = action.get("face")
        if not isinstance(qty, int) or not isinstance(face, int) or not (1 <= face <= 6) or qty < 1:
            raise ValueError("Invalid bid.")
        total_dice = sum(self.dice_count[pid] for pid in self._active_players())
        if qty > total_dice:
            raise ValueError(f"Bid quantity can't exceed {total_dice} dice in play.")
        if self.current_bid is not None and _bid_key(qty, face) <= _bid_key(
            self.current_bid["qty"], self.current_bid["face"]
        ):
            raise ValueError("Bid must be higher than the current bid.")

        self.current_bid = {"qty": qty, "face": face}
        self.bidder = player_id
        active = self._active_players()
        self.turn_index = (active.index(player_id) + 1) % len(active)

    def _apply_call_liar(self, player_id: str) -> None:
        if self.current_bid is None:
            raise ValueError("No bid to call.")

        all_dice = [v for pid in self._active_players() for v in self.dice_values[pid]]
        face = self.current_bid["face"]
        if face == 1:
            actual = sum(1 for v in all_dice if v == 1)
        else:
            actual = sum(1 for v in all_dice if v == face or v == 1)

        bid_was_true = actual >= self.current_bid["qty"]
        # Bid held up -> the caller doubted a true bid and loses a die.
        # Bid didn't hold up -> the bidder lied and loses a die.
        loser = player_id if bid_was_true else self.bidder

        self.dice_count[loser] -= 1
        eliminated = self.dice_count[loser] == 0

        self.last_result = {
            "caller": player_id,
            "bidder": self.bidder,
            "bid": dict(self.current_bid),
            "actual_count": actual,
            "bid_was_true": bid_was_true,
            "loser": loser,
            "eliminated": eliminated,
            "reveal": {pid: list(vals) for pid, vals in self.dice_values.items()},
        }
        self.phase = "revealed"

        active = self._active_players()
        if len(active) == 1:
            self.winner = active[0]
            self.phase = "game_over"
            return

        self._advance_turn_from(loser if not eliminated else active[0])

    def start_next_round(self) -> None:
        if self.phase != "revealed":
            raise ValueError("Can't start a new round right now.")
        loser = self.last_result["loser"]
        self._roll_all()
        self._advance_turn_from(loser)

    def to_public_state(self, viewer_id: str) -> dict:
        return {
            "game": self.game_type,
            "phase": self.phase,
            "players": [
                {"id": pid, "dice_count": self.dice_count[pid]} for pid in self.order
            ],
            "current_turn": self.current_turn(),
            "current_bid": self.current_bid,
            "bidder": self.bidder,
            "your_dice": self.dice_values.get(viewer_id, []),
            "last_result": self.last_result,
            "winner": self.winner,
        }
