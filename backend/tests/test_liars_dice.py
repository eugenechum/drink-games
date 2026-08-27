import pytest

from games.liars_dice import LiarsDiceGame


def make_game():
    game = LiarsDiceGame(["a", "b", "c"])
    # Deterministic dice for testing bid resolution.
    game.dice_values = {"a": [1, 2, 3, 4, 5], "b": [6, 6, 6, 2, 3], "c": [4, 4, 1, 1, 1]}
    return game


def test_first_turn_is_first_player():
    game = make_game()
    assert game.current_turn() == "a"


def test_bid_must_strictly_increase():
    game = make_game()
    game.apply_action("a", {"type": "bid", "qty": 3, "face": 4})
    with pytest.raises(ValueError):
        game.apply_action("b", {"type": "bid", "qty": 3, "face": 4})
    with pytest.raises(ValueError):
        game.apply_action("b", {"type": "bid", "qty": 2, "face": 6})
    # Legal raise: higher qty
    game.apply_action("b", {"type": "bid", "qty": 4, "face": 2})
    assert game.current_bid == {"qty": 4, "face": 2}
    assert game.current_turn() == "c"


def test_bid_cannot_exceed_total_dice_in_play():
    game = make_game()
    with pytest.raises(ValueError):
        game.apply_action("a", {"type": "bid", "qty": 16, "face": 6})


def test_bid_on_ones_outranks_same_quantity():
    game = make_game()
    game.apply_action("a", {"type": "bid", "qty": 3, "face": 6})
    # Same quantity, face 1 (wild) is a legal raise over face 6 at the same qty.
    game.apply_action("b", {"type": "bid", "qty": 3, "face": 1})
    assert game.current_bid == {"qty": 3, "face": 1}


def test_call_liar_bid_was_true_caller_loses_a_die():
    game = make_game()
    # Total 6s among all dice (incl wild 1s): b has three 6s, plus 1s wild:
    # a has one 1, c has three 1s -> four wild 1s + three 6s = seven dice count for face 6.
    game.apply_action("a", {"type": "bid", "qty": 5, "face": 6})
    game.apply_action("b", {"type": "call_liar"})
    result = game.last_result
    assert result["bid_was_true"] is True
    assert result["loser"] == "b"
    assert game.dice_count["b"] == 4


def test_call_liar_bid_was_false_bidder_loses_a_die():
    game = make_game()
    game.apply_action("a", {"type": "bid", "qty": 15, "face": 5})
    game.apply_action("b", {"type": "call_liar"})
    result = game.last_result
    assert result["bid_was_true"] is False
    assert result["loser"] == "a"
    assert game.dice_count["a"] == 4


def test_elimination_and_winner():
    game = LiarsDiceGame(["a", "b"])
    game.dice_count = {"a": 1, "b": 3}
    game.dice_values = {"a": [2], "b": [3, 3, 3]}
    game.apply_action("a", {"type": "bid", "qty": 4, "face": 3})
    game.apply_action("b", {"type": "call_liar"})
    assert game.last_result["loser"] == "a"
    assert game.dice_count["a"] == 0
    assert game.winner == "b"
    assert game.phase == "game_over"


def test_out_of_turn_action_rejected():
    game = make_game()
    with pytest.raises(ValueError):
        game.apply_action("b", {"type": "bid", "qty": 1, "face": 1})
