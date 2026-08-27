import pytest

from games.base import best_hand, evaluate_5
from games.holdem import HoldemGame


def card(rank, suit):
    return {"rank": rank, "suit": suit}


def test_hand_ranking_order():
    straight_flush = evaluate_5([card(9, "s"), card(8, "s"), card(7, "s"), card(6, "s"), card(5, "s")])
    quads = evaluate_5([card(9, "s"), card(9, "h"), card(9, "d"), card(9, "c"), card(2, "s")])
    full_house = evaluate_5([card(9, "s"), card(9, "h"), card(9, "d"), card(2, "c"), card(2, "s")])
    flush = evaluate_5([card(9, "s"), card(7, "s"), card(5, "s"), card(3, "s"), card(2, "s")])
    straight = evaluate_5([card(9, "s"), card(8, "h"), card(7, "d"), card(6, "c"), card(5, "s")])
    trips = evaluate_5([card(9, "s"), card(9, "h"), card(9, "d"), card(4, "c"), card(2, "s")])
    two_pair = evaluate_5([card(9, "s"), card(9, "h"), card(4, "d"), card(4, "c"), card(2, "s")])
    pair = evaluate_5([card(9, "s"), card(9, "h"), card(5, "d"), card(4, "c"), card(2, "s")])
    high = evaluate_5([card(9, "s"), card(7, "h"), card(5, "d"), card(4, "c"), card(2, "s")])
    assert straight_flush > quads > full_house > flush > straight > trips > two_pair > pair > high


def test_wheel_straight_ace_low():
    wheel = evaluate_5([card(14, "s"), card(2, "h"), card(3, "d"), card(4, "c"), card(5, "s")])
    assert wheel[0] == 4
    assert wheel[1] == 5  # 5-high, not ace-high


def test_best_hand_picks_best_5_of_7():
    seven = [
        card(14, "s"), card(14, "h"),  # pocket aces
        card(14, "d"), card(14, "c"), card(2, "s"), card(3, "h"), card(4, "d"),
    ]
    score, combo = best_hand(seven)
    assert score[0] == 7  # four of a kind
    assert len(combo) == 5


def _game_with_players(*stacks):
    pids = [f"p{i}" for i in range(len(stacks))]
    game = HoldemGame(pids)
    for pid, stack in zip(pids, stacks):
        game.stacks[pid] = stack
    return game, pids


def test_side_pot_split_with_uneven_all_ins():
    game, (a, b, c) = _game_with_players(100, 300, 300)
    game.in_hand = {a, b, c}
    game.folded = set()
    game.total_committed = {a: 100, b: 300, c: 300}
    game.hole_cards = {
        a: [card(14, "s"), card(14, "h")],   # best hand -> wins main pot
        b: [card(2, "s"), card(3, "h")],      # worst -> loses everywhere it's eligible
        c: [card(13, "s"), card(13, "h")],    # middle -> wins the side pot
    }
    game.community = [card(9, "d"), card(8, "c"), card(4, "s"), card(6, "h"), card(11, "d")]
    game.stacks = {a: 0, b: 0, c: 0}

    game._showdown()

    # main pot: 100*3=300 to a (best hand, eligible for everyone's contribution up to 100)
    assert game.stacks[a] == 300
    # side pot: (300-100)*2=400 between b and c, c has the better hand
    assert game.stacks[c] == 400
    assert game.stacks[b] == 0
    assert sum(game.stacks.values()) == 700


def test_side_pot_folded_player_forfeits_eligibility_but_money_stays_in_pot():
    game, (a, b, c) = _game_with_players(100, 300, 300)
    game.in_hand = {a, b, c}
    game.folded = {b}
    game.total_committed = {a: 100, b: 300, c: 300}
    game.hole_cards = {
        a: [card(14, "s"), card(14, "h")],
        b: [card(2, "s"), card(3, "h")],
        c: [card(13, "s"), card(13, "h")],
    }
    game.community = [card(9, "d"), card(8, "c"), card(4, "s"), card(6, "h"), card(11, "d")]
    game.stacks = {a: 0, b: 0, c: 0}

    game._showdown()

    assert game.stacks[a] == 300  # main pot, only a and c eligible (b folded), a wins
    assert game.stacks[c] == 400  # side pot, only c eligible since a didn't contribute past 100 and b folded
    assert game.stacks[b] == 0
    assert sum(game.stacks.values()) == 700


def test_rebuy_only_when_busted_and_buyins_open():
    game, (a, b) = _game_with_players(1000, 1000)
    game.phase = "hand_complete"
    game.stacks[a] = 0

    with pytest.raises(ValueError):
        game.rebuy(b)  # b still has chips

    game.rebuy(a)
    assert game.stacks[a] == 1000

    game.stacks[a] = 0
    game.close_buyins()
    with pytest.raises(ValueError):
        game.rebuy(a)


def test_full_heads_up_hand_preserves_total_chips():
    game, (a, b) = _game_with_players(1000, 1000)
    game.start_next_hand()
    assert game.phase == "preflop"

    # Heads-up preflop: button/SB acts first.
    first = game.current_turn()
    second = b if first == a else a
    game.apply_action(first, {"type": "call"})
    game.apply_action(second, {"type": "check"})
    assert game.phase == "flop"

    for street in ("flop", "turn", "river"):
        assert game.phase == street
        turn1 = game.current_turn()
        turn2 = b if turn1 == a else a
        game.apply_action(turn1, {"type": "check"})
        game.apply_action(turn2, {"type": "check"})

    assert game.phase == "hand_complete"
    assert sum(game.stacks.values()) == 2000


def test_total_buyin_tracks_initial_stack_and_rebuys():
    game, (a, b) = _game_with_players(1000, 1000)
    assert game.total_buyin[a] == 1000
    game.phase = "hand_complete"
    game.stacks[a] = 0
    game.rebuy(a)
    assert game.total_buyin[a] == 2000
    game.stacks[a] = 0
    game.rebuy(a)
    assert game.total_buyin[a] == 3000


def test_force_end_between_hands_keeps_stacks_untouched():
    game, (a, b) = _game_with_players(700, 1300)
    game.phase = "hand_complete"
    game.force_end()
    assert game.phase == "game_over"
    assert game.forced_end is True
    assert game.winner is None
    assert game.stacks == {a: 700, b: 1300}


def test_force_end_mid_hand_refunds_current_hand_chips():
    game, (a, b) = _game_with_players(1000, 1000)
    game.start_next_hand()
    assert game.phase == "preflop"
    stacks_before = dict(game.stacks)
    committed_before = dict(game.total_committed)

    game.force_end()

    assert game.phase == "game_over"
    for pid in (a, b):
        assert game.stacks[pid] == stacks_before[pid] + committed_before.get(pid, 0)
    assert sum(game.stacks.values()) == 2000


def test_force_end_twice_raises():
    game, (a, b) = _game_with_players(1000, 1000)
    game.force_end()
    with pytest.raises(ValueError):
        game.force_end()


def test_all_in_runs_out_remaining_streets_without_more_betting():
    game, (a, b) = _game_with_players(1000, 1000)
    game.start_next_hand()
    first = game.current_turn()
    second = b if first == a else a
    game.apply_action(first, {"type": "raise", "to": 1000})
    game.apply_action(second, {"type": "call"})
    assert game.phase == "hand_complete"
    assert len(game.community) == 5
    assert sum(game.stacks.values()) == 2000
