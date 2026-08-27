# Drink Games

A phone-friendly party game app: a host creates a room, friends join by
scanning a QR code or typing a 4-digit code, and the host starts a round of
**Liar's Dice**, **Poker Dice**, or **Texas Hold'em** on a shared,
casino-styled table. No accounts, no database — rooms live only in memory
while the app is running.

## Stack

- **Backend**: FastAPI + WebSockets (`backend/`), no database. Rooms and game
  state live in process memory (`backend/rooms.py`); each game is its own
  state machine under `backend/games/`.
- **Frontend**: React + Vite + Tailwind (`frontend/`), casino felt theme.

## Run locally

```bash
cd backend && pip install -r requirements.txt && uvicorn main:app --reload
```

```bash
cd frontend && npm install && npm run dev
```

The Vite dev server proxies `/api` (including the WebSocket) to the backend
on `:8000`, so it behaves the same as production.

## Tests

```bash
cd backend && pip install pytest && pytest
```

Covers the three game state machines (bidding/elimination rules, dice hand
ranking, Hold'em side pots and hand evaluation) and the room store.

## Deploy

Deploys to Substrait via `/substrait:deploy` — no database is declared, so
there's nothing to migrate. See `CLAUDE.md` for the deployment contract.
