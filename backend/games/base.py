"""Shared building blocks: a standard card deck and a 5/7-card poker hand
evaluator used by Texas Hold'em. Dice-based games have their own, simpler
evaluators in their own modules.
"""
from __future__ import annotations

import random
from itertools import combinations

RANKS = "23456789TJQKA"
SUITS = "shdc"
RANK_NAMES = {
    14: "Ace", 13: "King", 12: "Queen", 11: "Jack", 10: "10",
    9: "9", 8: "8", 7: "7", 6: "6", 5: "5", 4: "4", 3: "3", 2: "2",
}
CATEGORY_NAMES = {
    8: "Straight Flush", 7: "Four of a Kind", 6: "Full House", 5: "Flush",
    4: "Straight", 3: "Three of a Kind", 2: "Two Pair", 1: "One Pair", 0: "High Card",
}


def new_deck() -> list[dict]:
    deck = [
        {"rank": RANKS.index(r) + 2, "suit": s}
        for r in RANKS
        for s in SUITS
    ]
    random.shuffle(deck)
    return deck


def card_label(card: dict) -> str:
    rank = card["rank"]
    label = "10" if rank == 10 else {14: "A", 13: "K", 12: "Q", 11: "J"}.get(rank, str(rank))
    suit_symbol = {"s": "♠", "h": "♥", "d": "♦", "c": "♣"}[card["suit"]]
    return f"{label}{suit_symbol}"


def evaluate_5(cards: list[dict]) -> tuple:
    """Score a 5-card hand as a tuple: higher tuple = better hand. Comparable directly."""
    ranks = sorted((c["rank"] for c in cards), reverse=True)
    suits = [c["suit"] for c in cards]
    is_flush = len(set(suits)) == 1

    counts: dict[int, int] = {}
    for r in ranks:
        counts[r] = counts.get(r, 0) + 1
    # groups: sorted by (count desc, rank desc)
    groups = sorted(counts.items(), key=lambda kv: (kv[1], kv[0]), reverse=True)
    group_ranks = [r for r, _ in groups]
    group_counts = [c for _, c in groups]

    unique_ranks = sorted(set(ranks), reverse=True)
    is_straight = False
    straight_high = None
    if len(unique_ranks) == 5:
        if unique_ranks[0] - unique_ranks[4] == 4:
            is_straight = True
            straight_high = unique_ranks[0]
        elif unique_ranks == [14, 5, 4, 3, 2]:  # wheel: A-2-3-4-5
            is_straight = True
            straight_high = 5

    if is_straight and is_flush:
        return (8, straight_high)
    if group_counts[0] == 4:
        kicker = max(r for r in ranks if r != group_ranks[0])
        return (7, group_ranks[0], kicker)
    if group_counts[0] == 3 and group_counts[1] == 2:
        return (6, group_ranks[0], group_ranks[1])
    if is_flush:
        return (5, *ranks)
    if is_straight:
        return (4, straight_high)
    if group_counts[0] == 3:
        kickers = sorted((r for r in ranks if r != group_ranks[0]), reverse=True)
        return (3, group_ranks[0], *kickers)
    if group_counts[0] == 2 and group_counts[1] == 2:
        pair_hi, pair_lo = max(group_ranks[0], group_ranks[1]), min(group_ranks[0], group_ranks[1])
        kicker = max(r for r in ranks if r != pair_hi and r != pair_lo)
        return (2, pair_hi, pair_lo, kicker)
    if group_counts[0] == 2:
        kickers = sorted((r for r in ranks if r != group_ranks[0]), reverse=True)
        return (1, group_ranks[0], *kickers)
    return (0, *ranks)


def best_hand(cards: list[dict]) -> tuple[tuple, list[dict]]:
    """Best 5-card hand (score, cards) out of any number (5-7) of cards."""
    best_score = None
    best_combo = None
    for combo in combinations(cards, 5):
        score = evaluate_5(list(combo))
        if best_score is None or score > best_score:
            best_score = score
            best_combo = list(combo)
    return best_score, best_combo


def hand_description(score: tuple) -> str:
    return CATEGORY_NAMES[score[0]]
