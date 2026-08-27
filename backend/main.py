"""Drink Games backend: FastAPI + WebSockets, no database. Rooms and game
state live entirely in process memory (see rooms.py) — a room is gone once
the process restarts, but a disconnected player can rejoin the same room by
reconnecting the WebSocket with their existing player_id.
"""
from __future__ import annotations

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from games.holdem import HoldemGame
from games.liars_dice import LiarsDiceGame
from games.poker_dice import PokerDiceGame
from rooms import MAX_PLAYERS, Room, store
from ws import manager

app = FastAPI(title="Drink Games")

GAME_CLASSES = {
    "liars_dice": LiarsDiceGame,
    "poker_dice": PokerDiceGame,
    "holdem": HoldemGame,
}


class Health(BaseModel):
    status: str


@app.get("/health", response_model=Health)
def health():
    return {"status": "ok"}


# -- REST: create / join / peek a room --------------------------------------


class CreateRoomIn(BaseModel):
    host_name: str


class JoinRoomIn(BaseModel):
    name: str


class RoomJoinOut(BaseModel):
    code: str
    player_id: str
    player_name: str


class RoomInfoOut(BaseModel):
    exists: bool
    player_count: int = 0
    max_players: int = MAX_PLAYERS
    started: bool = False


@app.post("/api/rooms", response_model=RoomJoinOut)
def create_room(body: CreateRoomIn):
    room, player = store.create_room(body.host_name)
    return {"code": room.code, "player_id": player.id, "player_name": player.name}


@app.post("/api/rooms/{code}/join", response_model=RoomJoinOut)
def join_room(code: str, body: JoinRoomIn):
    try:
        room, player = store.join_room(code, body.name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"code": room.code, "player_id": player.id, "player_name": player.name}


@app.get("/api/rooms/{code}", response_model=RoomInfoOut)
def room_info(code: str):
    room = store.get_room(code)
    if room is None:
        return {"exists": False}
    return {
        "exists": True,
        "player_count": len(room.players),
        "max_players": MAX_PLAYERS,
        "started": room.game is not None,
    }


# -- state broadcasting -------------------------------------------------------


def build_state(room: Room, viewer_id: str) -> dict:
    return {
        "type": "state",
        "room": {
            "code": room.code,
            "game_type": room.game_type,
            "players": [
                {"id": p.id, "name": p.name, "is_host": p.is_host, "connected": p.connected}
                for p in room.players.values()
            ],
        },
        "you": {"id": viewer_id, "is_host": room.players[viewer_id].is_host}
        if viewer_id in room.players
        else None,
        "game": room.game.to_public_state(viewer_id) if room.game else None,
    }


async def broadcast_room(room: Room) -> None:
    await manager.broadcast(room.code, lambda pid: build_state(room, pid))


# -- WebSocket ----------------------------------------------------------------


@app.websocket("/api/ws/{code}")
async def room_socket(websocket: WebSocket, code: str, player_id: str):
    room = store.get_room(code)
    player = room.players.get(player_id) if room else None
    if room is None or player is None:
        await websocket.close(code=4404)
        return

    await websocket.accept()
    player.connected = True
    manager.connect(code, player_id, websocket)
    await broadcast_room(room)

    try:
        while True:
            message = await websocket.receive_json()
            try:
                await handle_message(room, player_id, message)
            except ValueError as e:
                await manager.send_to(code, player_id, {"type": "error", "message": str(e)})
    except WebSocketDisconnect:
        player.connected = False
        manager.disconnect(code, player_id)
        await broadcast_room(room)


async def handle_message(room: Room, player_id: str, message: dict) -> None:
    msg_type = message.get("type")
    player = room.players[player_id]

    if msg_type == "start_game":
        if not player.is_host:
            raise ValueError("Only the host can start a game.")
        if room.game is not None:
            raise ValueError("A game is already in progress.")
        game_type = message.get("game")
        if game_type not in GAME_CLASSES:
            raise ValueError("Unknown game.")
        if len(room.players) < 2:
            raise ValueError("Need at least 2 players to start.")
        room.game_type = game_type
        room.game = GAME_CLASSES[game_type](room.player_order())
        if game_type == "holdem":
            room.game.start_next_hand()
        await broadcast_room(room)
        return

    if room.game is None:
        raise ValueError("No game in progress.")

    if msg_type == "game_action":
        room.game.apply_action(player_id, message.get("action") or {})
    elif msg_type == "next_round":
        if not player.is_host:
            raise ValueError("Only the host can start the next round.")
        if room.game_type == "holdem":
            room.game.start_next_hand()
        else:
            room.game.start_next_round()
    elif msg_type == "rebuy":
        if room.game_type != "holdem":
            raise ValueError("Rebuying only applies to Hold'em.")
        room.game.rebuy(player_id)
    elif msg_type == "close_buyins":
        if not player.is_host:
            raise ValueError("Only the host can close buy-ins.")
        if room.game_type != "holdem":
            raise ValueError("Buy-ins only apply to Hold'em.")
        room.game.close_buyins()
    elif msg_type == "back_to_lobby":
        if not player.is_host:
            raise ValueError("Only the host can return to the game picker.")
        if room.game is not None and getattr(room.game, "phase", None) not in ("game_over",):
            raise ValueError("Can't leave a game that's still in progress.")
        room.game = None
        room.game_type = None
    else:
        raise ValueError(f"Unknown message type: {msg_type}")

    await broadcast_room(room)
