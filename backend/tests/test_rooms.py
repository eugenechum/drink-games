import pytest

from rooms import MAX_PLAYERS, RoomStore


def test_create_room_generates_4_digit_code_and_host():
    store = RoomStore()
    room, host = store.create_room("Alice")
    assert len(room.code) == 4 and room.code.isdigit()
    assert host.is_host is True
    assert room.players[host.id] is host


def test_join_room_adds_player():
    store = RoomStore()
    room, _ = store.create_room("Alice")
    _, joiner = store.join_room(room.code, "Bob")
    assert joiner.is_host is False
    assert len(room.players) == 2


def test_join_missing_room_raises():
    store = RoomStore()
    with pytest.raises(ValueError):
        store.join_room("9999", "Nobody")


def test_join_full_room_raises():
    store = RoomStore()
    room, _ = store.create_room("Host")
    for i in range(MAX_PLAYERS - 1):
        store.join_room(room.code, f"Player{i}")
    assert len(room.players) == MAX_PLAYERS
    with pytest.raises(ValueError):
        store.join_room(room.code, "OneTooMany")


def test_join_after_game_started_raises():
    store = RoomStore()
    room, _ = store.create_room("Host")
    room.game = object()  # any truthy sentinel standing in for a started game
    with pytest.raises(ValueError):
        store.join_room(room.code, "Late")


def test_room_codes_do_not_collide():
    store = RoomStore()
    codes = {store.create_room(f"Host{i}")[0].code for i in range(50)}
    assert len(codes) == 50
