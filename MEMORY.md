# Memory — Drink Games

- Built 2026-08-27. In-memory-only rooms (no database) — rooms and game state
  vanish on backend restart; this is intentional (see [FEATURE-drink-games.md](FEATURE-drink-games.md)).
- Deployed 2026-08-27 via Substrait's GitHub-connected flow (this workspace is
  GitHub-only for new apps): private repo `github.com/eugenechum/drink-games`,
  Substrait slug `drink-games`, live at drink-games.ninjavan.apps.substrait.build.
  Push to `master` + `/substrait:deploy` to ship future changes.
