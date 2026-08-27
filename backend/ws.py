"""WebSocket connection registry: tracks the live socket for each connected
player and fans out messages to a room.
"""
from __future__ import annotations

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self._sockets: dict[str, dict[str, WebSocket]] = {}

    def connect(self, code: str, player_id: str, ws: WebSocket) -> None:
        self._sockets.setdefault(code, {})[player_id] = ws

    def disconnect(self, code: str, player_id: str) -> None:
        room_sockets = self._sockets.get(code)
        if room_sockets:
            room_sockets.pop(player_id, None)
            if not room_sockets:
                self._sockets.pop(code, None)

    def connected_players(self, code: str) -> list[str]:
        return list(self._sockets.get(code, {}).keys())

    async def send_to(self, code: str, player_id: str, message: dict) -> None:
        ws = self._sockets.get(code, {}).get(player_id)
        if ws is not None:
            await ws.send_json(message)

    async def broadcast(self, code: str, build_message) -> None:
        """build_message(player_id) -> dict, called once per connected player
        so each viewer gets their own personalized state (private cards etc)."""
        for player_id, ws in list(self._sockets.get(code, {}).items()):
            await ws.send_json(build_message(player_id))


manager = ConnectionManager()
