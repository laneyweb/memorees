# Contributing to Memorees (for developers)

End-user docs live in [README.md](README.md). This file is the dev side:
how the app is built, tested, specified and released.

## Stack

Single container: **FastAPI + SQLite** (stdlib `sqlite3`, WAL mode), vanilla
JS frontend served from `frontend/index.html` (no build step, no framework).
Pillow + pillow-heif for EXIF and HEIF→JPEG previews; 400px `_t.jpg`
thumbs live next to previews and are backfilled on first view.

Layout: `backend/app.py` (API + pages), `frontend/index.html`,
`compose.yaml`, `Dockerfile`, `requirements.txt`, `VERSION`,
`.env.example`. Host state lives in `DATA_DIR` (`memorees.db`,
`originals/`, `previews/`) — never commit it.

## Words and plan

- `GLOSSARY.md` is the ubiquitous language; use it in code, tickets, docs.
- `docs/SPEC-verify-v1.md` is the spec (problem, solution, user stories…).
- `.scratch/remote-verify/issues/` holds one file per ticket with blocking edges.
- `NEXT.md` is the session bookmark.

## Test suites (all must be green before pushing)

| Suite | Run | Covers |
|---|---|---|
| Remote smoke | `python scripts/smoke.py --base <url> --user <u> --password <pw>` | 26 HTTP checks vs a live host |
| Static UI | `python scripts/check_ui.py` | 38 markup/CSS invariants |
| Visual | `cd visual && npx playwright test` | owner/public/tablet flows in real Chromium + review shots in `visual-shots/` |
| README shots | backend on :8019, then `node visual/readme-shots.mjs` | regenerates `docs/shots/` |

Visual needs a local backend on :8019 (`DATA_DIR=.scratch/visual-data`).
`prototype/<name>` branches hold throwaway UI demos, never merged to `main`.

## Versioning

`VERSION` holds semver; `compose.yaml` image tag tracks it. Patch-bump on
every functional `main` push, minor for new behavior, major for 1.0.
`scripts/deploy.sh` stamps build hash + date. `git tag vX.Y.Z` on request
or milestones. Docs-only changes skip the bump.
