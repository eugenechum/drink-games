"""Texas Hold'em: full betting rounds (pre-flop/flop/turn/river), side pots
for all-in situations, 7-card hand evaluation at showdown, and buy-backs for
busted players (until the host closes buy-ins).

Simplification note: an all-in raise for less than a full legal raise still
reopens the action to other players (real casinos sometimes restrict this) —
an acceptable simplification for a casual party game.
"""
from __future__ import annotations

from .base import best_hand, card_label, hand_description, new_deck

STARTING_STACK = 1000
SMALL_BLIND = 10
BIG_BLIND = 20


class HoldemGame:
    game_type = "holdem"

    def __init__(self, player_ids: list[str]):
        self.seats = list(player_ids)  # fixed seating order, stable across busts/rebuys
        self.stacks = {pid: STARTING_STACK for pid in self.seats}
        self.buyins_open = True
        self.button_pid: str | None = None
        self.hand_number = 0
        self.phase = "hand_complete"  # trigger start_next_hand() to deal hand #1
        self.order: list[str] = []
        self.in_hand: set[str] = set()
        self.folded: set[str] = set()
        self.all_in: set[str] = set()
        self.hole_cards: dict[str, list[dict]] = {}
        self.community: list[dict] = []
        self.deck: list[dict] = []
        self.committed_street: dict[str, int] = {}
        self.total_committed: dict[str, int] = {}
        self.current_bet = 0
        self.min_raise = BIG_BLIND
        self.queue: list[str] = []
        self.sb_pid: str | None = None
        self.bb_pid: str | None = None
        self.last_result: dict | None = None
        self.winner: str | None = None

    # -- table / hand setup -------------------------------------------------

    def _players_with_chips(self) -> list[str]:
        return [pid for pid in self.seats if self.stacks[pid] > 0]

    def start_next_hand(self) -> None:
        if self.phase not in ("hand_complete",):
            raise ValueError("Current hand isn't finished yet.")
        eligible = self._players_with_chips()
        if len(eligible) < 2:
            self.phase = "game_over"
            self.winner = eligible[0] if eligible else None
            return

        if self.button_pid is None or self.button_pid not in eligible:
            self.button_pid = eligible[0]
        else:
            idx = self.seats.index(self.button_pid)
            n = len(self.seats)
            for i in range(1, n + 1):
                candidate = self.seats[(idx + i) % n]
                if candidate in eligible:
                    self.button_pid = candidate
                    break

        b_idx = eligible.index(self.button_pid)
        self.order = eligible[b_idx + 1:] + eligible[: b_idx + 1]  # ends with button
        n = len(self.order)
        if n == 2:
            self.sb_pid, self.bb_pid = self.order[1], self.order[0]
        else:
            self.sb_pid, self.bb_pid = self.order[0], self.order[1]

        self.hand_number += 1
        self.in_hand = set(eligible)
        self.folded = set()
        self.all_in = set()
        self.deck = new_deck()
        self.hole_cards = {pid: [self.deck.pop(), self.deck.pop()] for pid in self.order}
        self.community = []
        self.total_committed = {pid: 0 for pid in self.in_hand}
        self.committed_street = {pid: 0 for pid in self.in_hand}
        self.current_bet = 0
        self.min_raise = BIG_BLIND
        self.last_result = None

        self._post_blind(self.sb_pid, SMALL_BLIND)
        self._post_blind(self.bb_pid, BIG_BLIND)
        self.current_bet = BIG_BLIND

        self.phase = "preflop"
        self.queue = self._filtered(self._preflop_order())
        if not self.queue:
            self._runout_to_showdown()

    def _post_blind(self, pid: str, amount: int) -> None:
        pay = min(amount, self.stacks[pid])
        self.stacks[pid] -= pay
        self.committed_street[pid] = pay
        self.total_committed[pid] = pay
        if self.stacks[pid] == 0:
            self.all_in.add(pid)

    def _preflop_order(self) -> list[str]:
        n = len(self.order)
        bb_idx = self.order.index(self.bb_pid)
        return [self.order[(bb_idx + 1 + i) % n] for i in range(n)]

    def _postflop_order(self) -> list[str]:
        n = len(self.order)
        button_idx = self.order.index(self.button_pid)
        return [self.order[(button_idx + 1 + i) % n] for i in range(n)]

    def _filtered(self, seq: list[str]) -> list[str]:
        return [p for p in seq if p not in self.folded and p not in self.all_in]

    def _players_after(self, pid: str) -> list[str]:
        n = len(self.order)
        idx = self.order.index(pid)
        seq = [self.order[(idx + 1 + i) % n] for i in range(n - 1)]
        return self._filtered(seq)

    def current_turn(self) -> str | None:
        return self.queue[0] if self.queue else None

    # -- betting actions ------------------------------------------------------

    def apply_action(self, player_id: str, action: dict) -> None:
        if self.phase not in ("preflop", "flop", "turn", "river"):
            raise ValueError("No betting in progress.")
        if player_id != self.current_turn():
            raise ValueError("It's not your turn.")

        action_type = action.get("type")
        if action_type == "fold":
            self.folded.add(player_id)
            self.queue.pop(0)
        elif action_type == "check":
            if self.committed_street[player_id] != self.current_bet:
                raise ValueError("You can't check — there's a bet to call.")
            self.queue.pop(0)
        elif action_type == "call":
            self._call(player_id)
            self.queue.pop(0)
        elif action_type in ("raise", "bet"):
            self._raise(player_id, action)
        else:
            raise ValueError(f"Unknown action: {action_type}")

        self._after_action()

    def _call(self, pid: str) -> None:
        needed = self.current_bet - self.committed_street[pid]
        pay = min(needed, self.stacks[pid])
        self.stacks[pid] -= pay
        self.committed_street[pid] += pay
        self.total_committed[pid] += pay
        if self.stacks[pid] == 0:
            self.all_in.add(pid)

    def _raise(self, pid: str, action: dict) -> None:
        to_amount = action.get("to")
        if not isinstance(to_amount, int) or to_amount <= self.current_bet:
            raise ValueError("Raise must be higher than the current bet.")
        max_possible = self.committed_street[pid] + self.stacks[pid]
        if to_amount > max_possible:
            raise ValueError("You don't have enough chips for that raise.")
        raise_size = to_amount - self.current_bet
        is_all_in = to_amount == max_possible
        if raise_size < self.min_raise and not is_all_in:
            raise ValueError(f"Raise must be at least {self.min_raise} more than the current bet.")

        pay = to_amount - self.committed_street[pid]
        self.stacks[pid] -= pay
        self.committed_street[pid] = to_amount
        self.total_committed[pid] += pay
        if self.stacks[pid] == 0:
            self.all_in.add(pid)

        if raise_size > self.min_raise:
            self.min_raise = raise_size
        self.current_bet = to_amount
        self.queue = self._players_after(pid)

    def _after_action(self) -> None:
        still_in = [p for p in self.in_hand if p not in self.folded]
        if len(still_in) == 1:
            self._award_uncontested(still_in[0])
            return
        if not self.queue:
            self._advance_street()

    def _award_uncontested(self, winner: str) -> None:
        pot = sum(self.total_committed.values())
        self.stacks[winner] += pot
        self.last_result = {
            "pots": [{"amount": pot, "winners": [winner], "eligible": [winner]}],
            "reason": "everyone else folded",
            "hole_cards": {pid: [card_label(c) for c in cards] for pid, cards in self.hole_cards.items()},
        }
        self._finish_hand()

    def _advance_street(self) -> None:
        if self.phase == "preflop":
            self.community += [self.deck.pop() for _ in range(3)]
            self.phase = "flop"
        elif self.phase == "flop":
            self.community.append(self.deck.pop())
            self.phase = "turn"
        elif self.phase == "turn":
            self.community.append(self.deck.pop())
            self.phase = "river"
        else:
            self._showdown()
            return

        for pid in self.in_hand:
            self.committed_street[pid] = 0
        self.current_bet = 0
        self.min_raise = BIG_BLIND
        self.queue = self._filtered(self._postflop_order())
        if not self.queue:
            self._runout_to_showdown()

    def _runout_to_showdown(self) -> None:
        # Everyone left is all-in (or only one player can still act) — deal
        # the remaining streets with no further betting, then showdown.
        while self.phase != "river":
            if self.phase == "preflop":
                self.community += [self.deck.pop() for _ in range(3)]
                self.phase = "flop"
            elif self.phase == "flop":
                self.community.append(self.deck.pop())
                self.phase = "turn"
            elif self.phase == "turn":
                self.community.append(self.deck.pop())
                self.phase = "river"
        self._showdown()

    def _showdown(self) -> None:
        layers = sorted(set(v for v in self.total_committed.values() if v > 0))
        pots = []
        prev_level = 0
        for level in layers:
            contributors = [p for p in self.in_hand if self.total_committed[p] > prev_level]
            layer_size = level - prev_level
            amount = layer_size * len(contributors)
            eligible = [p for p in contributors if p not in self.folded]
            pots.append({"amount": amount, "eligible": eligible})
            prev_level = level

        scores = {}
        for pot in pots:
            for pid in pot["eligible"]:
                if pid not in scores:
                    scores[pid] = best_hand(self.hole_cards[pid] + self.community)[0]

        pot_results = []
        for pot in pots:
            if pot["amount"] == 0:
                continue
            if len(pot["eligible"]) == 1:
                winners = pot["eligible"]
            else:
                best_score = max(scores[p] for p in pot["eligible"])
                winners = [p for p in pot["eligible"] if scores[p] == best_score]
            share, remainder = divmod(pot["amount"], len(winners))
            for i, w in enumerate(winners):
                self.stacks[w] += share + (1 if i < remainder else 0)
            pot_results.append({
                "amount": pot["amount"],
                "winners": winners,
                "eligible": pot["eligible"],
                "hand": hand_description(scores[winners[0]]) if len(pot["eligible"]) > 1 else None,
            })

        self.last_result = {
            "pots": pot_results,
            "reason": "showdown",
            "hole_cards": {
                pid: [card_label(c) for c in cards]
                for pid, cards in self.hole_cards.items()
                if pid not in self.folded
            },
        }
        self._finish_hand()

    def _finish_hand(self) -> None:
        self.phase = "hand_complete"
        remaining = self._players_with_chips()
        rebuy_possible = self.buyins_open and any(
            self.stacks[p] == 0 for p in self.seats
        )
        if len(remaining) <= 1 and not rebuy_possible:
            self.phase = "game_over"
            self.winner = remaining[0] if remaining else None

    # -- host / player controls outside the betting loop ---------------------

    def close_buyins(self) -> None:
        self.buyins_open = False

    def rebuy(self, player_id: str) -> None:
        if player_id not in self.seats:
            raise ValueError("Not a player at this table.")
        if not self.buyins_open:
            raise ValueError("Buy-ins are closed for this game.")
        if self.stacks[player_id] != 0:
            raise ValueError("You still have chips.")
        if self.phase not in ("hand_complete",):
            raise ValueError("Wait for the current hand to finish.")
        self.stacks[player_id] = STARTING_STACK

    def to_public_state(self, viewer_id: str) -> dict:
        reveal_all = self.phase in ("hand_complete", "game_over")
        hole = {}
        for pid in self.in_hand:
            if pid == viewer_id or reveal_all:
                hole[pid] = [card_label(c) for c in self.hole_cards.get(pid, [])]
        return {
            "game": self.game_type,
            "phase": self.phase,
            "hand_number": self.hand_number,
            "buyins_open": self.buyins_open,
            "button": self.button_pid,
            "community": [card_label(c) for c in self.community],
            "pot": sum(self.total_committed.values()),
            "current_bet": self.current_bet,
            "min_raise": self.min_raise,
            "current_turn": self.current_turn(),
            "players": [
                {
                    "id": pid,
                    "stack": self.stacks[pid],
                    "committed_street": self.committed_street.get(pid, 0),
                    "folded": pid in self.folded,
                    "all_in": pid in self.all_in,
                    "busted": self.stacks[pid] == 0,
                    "in_hand": pid in self.in_hand,
                }
                for pid in self.seats
            ],
            "your_hole_cards": hole.get(viewer_id, []),
            "hole_cards": hole,
            "last_result": self.last_result,
            "winner": self.winner,
        }
