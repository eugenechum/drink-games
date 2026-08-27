"""In-memory room + player store. No database — rooms live only as long as
the backend process is running. A disconnected player rejoins the same room
by reconnecting the WebSocket with their existing player_id.
"""
from __future__ import annotations

import random
import uuid
from dataclasses import dataclass, field

MAX_PLAYERS = 8


@dataclass
class Player:
    id: str
    name: str
    is_host: bool = False
    connected: bool = False


@dataclass
class Room:
    code: str
    players: dict[str, Player] = field(default_factory=dict)
    game_type: str | None = None
    game: object | None = None

    def player_order(self) -> list[str]:
        return list(self.players.keys())

    def host_id(self) -> str | None:
        for pid, p in self.players.items():
            if p.is_host:
                return pid
        return None


class RoomStore:
    def __init__(self) -> None:
        self.rooms: dict[str, Room] = {}

    def _new_code(self) -> str:
        for _ in range(1000):
            code = f"{random.randint(0, 9999):04d}"
            if code not in self.rooms:
                return code
        raise RuntimeError("Could not allocate a room code.")

    def create_room(self, host_name: str) -> tuple[Room, Player]:
        code = self._new_code()
        room = Room(code=code)
        player = Player(id=uuid.uuid4().hex, name=host_name.strip()[:24] or "Host", is_host=True)
        room.players[player.id] = player
        self.rooms[code] = room
        return room, player

    def join_room(self, code: str, name: str) -> tuple[Room, Player]:
        room = self.rooms.get(code)
        if room is None:
            raise ValueError("Room not found.")
        if len(room.players) >= MAX_PLAYERS:
            raise ValueError("Room is full.")
        if room.game is not None:
            raise ValueError("This game has already started.")
        player = Player(id=uuid.uuid4().hex, name=name.strip()[:24] or "Player")
        room.players[player.id] = player
        return room, player

    def get_room(self, code: str) -> Room | None:
        return self.rooms.get(code)

    def get_player(self, code: str, player_id: str) -> Player | None:
        room = self.rooms.get(code)
        if room is None:
            return None
        return room.players.get(player_id)


store = RoomStore()
