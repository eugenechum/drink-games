# Feature: Drink Games (initial build)

## Scope

Party game app with three games — Liar's Dice, Poker Dice, Texas Hold'em —
played in a room a host creates and others join via QR code or 4-digit code.

## Key decisions

- **Drinking mechanic**: app just declares the loser each round/hand — no
  drink tally, honor system.
- **Liar's Dice**: standard rules, 5 dice/player, 1s wild (except when the
  bid itself is on 1s), loser drops a die, eliminated at 0.
- **Poker Dice**: hand-ranking roll-off (5 dice, up to 3 rolls, keep/reroll
  any), not the bluffing variant. No straights/flushes (dice have no suits) —
  7 standard categories from five-of-a-kind down to high die.
- **Texas Hold'em**: full rules incl. side pots for all-in situations, plus
  buy-back-in for busted players (rebuy to the starting stack before the next
  hand, until the host closes buy-ins).
- **Rooms**: in-memory only, no database. A disconnected player rejoins the
  same room via their existing `player_id` (stored in the browser's
  `localStorage`, keyed by room code) as long as the backend process is still
  running.
- **Host**: plays as a participant, not just a moderator.
- **Players**: up to 8 per room, same cap across all three games.

## Status: built, tested, not yet deployed

- Backend game logic (`backend/games/`) covered by `pytest` (34 tests):
  Liar's Dice bidding/elimination, Poker Dice hand ranking/tie-breaks,
  Hold'em hand evaluator + side-pot math + rebuy rules.
- Full-stack flow verified with a live WebSocket smoke test (create room,
  join, play a round of each game end-to-end) rather than browser automation,
  per this workspace's QA preference. Chip conservation verified through a
  full Hold'em hand (no chips created/destroyed across betting + showdown).
- `npm run build` passes for the frontend.
- **Not yet verified**: the actual UI in a browser (casino styling, QR scan
  flow, mobile layout) — do a manual pass before treating this as fully done.
- **Not yet deployed** to Substrait — no database declared (intentional).

## Known simplifications (acceptable for a casual party app)

- Hold'em: an all-in raise for less than a full legal raise still reopens
  the betting round to other players (real casino rules sometimes restrict
  this).
- No reconnect grace period beyond "the room process is still alive" — if
  the backend restarts, all rooms are gone.
