import pytest

from games.poker_dice import PokerDiceGame, evaluate_dice


@pytest.mark.parametrize(
    "dice,expected_category",
    [
        ([6, 6, 6, 6, 6], 6),  # five of a kind
        ([6, 6, 6, 6, 2], 5),  # four of a kind
        ([6, 6, 6, 2, 2], 4),  # full house
        ([6, 6, 6, 2, 3], 3),  # three of a kind
        ([6, 6, 2, 2, 3], 2),  # two pair
        ([6, 6, 2, 3, 4], 1),  # one pair
        ([6, 5, 4, 3, 2], 0),  # high die / nothing
    ],
)
def test_hand_categories(dice, expected_category):
    assert evaluate_dice(dice)[0] == expected_category


def test_higher_category_beats_lower():
    assert evaluate_dice([6, 6, 6, 6, 2]) > evaluate_dice([6, 6, 6, 2, 2])  # quads > full house
    assert evaluate_dice([1, 1, 1, 2, 2]) > evaluate_dice([6, 6, 6, 2, 3])  # full house > trips


def test_tie_break_by_kicker_within_same_category():
    # Both one-pair hands: pair of 6s with a 5 kicker beats pair of 6s with a 4 kicker.
    assert evaluate_dice([6, 6, 5, 3, 2]) > evaluate_dice([6, 6, 4, 3, 2])
    # Both full houses: trip-rank breaks the tie (5s-over-2s beats 1s-over-3s).
    assert evaluate_dice([3, 3, 1, 1, 1]) < evaluate_dice([5, 5, 5, 2, 2])


def test_rolling_and_reveal_flow():
    game = PokerDiceGame(["a", "b"])
    game.apply_action("a", {"type": "roll"})
    assert game.rolls_used["a"] == 1
    assert game.phase == "rolling"
    game.apply_action("a", {"type": "stand"})
    assert game.done["a"] is True

    with pytest.raises(ValueError):
        game.apply_action("a", {"type": "roll"})

    game.apply_action("b", {"type": "roll"})
    game.apply_action("b", {"type": "stand"})
    assert game.phase == "revealed"
    assert game.last_result is not None
    assert set(game.last_result["winners"]) | set(game.last_result["losers"])


def test_max_three_rolls_auto_stands():
    game = PokerDiceGame(["a", "b"])
    game.apply_action("a", {"type": "roll"})
    game.apply_action("a", {"type": "roll", "keep": [True] * 5})
    game.apply_action("a", {"type": "roll", "keep": [True] * 5})
    assert game.done["a"] is True
    with pytest.raises(ValueError):
        game.apply_action("a", {"type": "roll", "keep": [True] * 5})


def test_win_loss_tally_after_reveal():
    game = PokerDiceGame(["a", "b"])
    game.apply_action("a", {"type": "roll"})
    game.apply_action("a", {"type": "stand"})
    game.dice["a"] = [6, 6, 6, 6, 6]
    game.apply_action("b", {"type": "roll"})
    game.dice["b"] = [1, 2, 3, 4, 5]
    game.apply_action("b", {"type": "stand"})
    assert game.wins["a"] == 1
    assert game.losses["b"] == 1
    assert game.wins["b"] == 0
    assert game.losses["a"] == 0


def test_force_end_marks_game_over():
    game = PokerDiceGame(["a", "b"])
    game.force_end()
    assert game.phase == "game_over"
    assert game.forced_end is True
    with pytest.raises(ValueError):
        game.force_end()


def test_start_next_round_resets_state():
    game = PokerDiceGame(["a", "b"])
    for pid in ("a", "b"):
        game.apply_action(pid, {"type": "roll"})
        game.apply_action(pid, {"type": "stand"})
    assert game.phase == "revealed"
    game.start_next_round()
    assert game.phase == "rolling"
    assert all(v == 0 for v in game.rolls_used.values())
    assert all(d == [0, 0, 0, 0, 0] for d in game.dice.values())
