# Memorees — where we are (bookmark)

## Status
- `main` at **0.2.1** (paged grids, 400px thumbs, size-persistence fix, no-store HTML).
- Remote host `https://memorees.darrenlane.com` verified green: smoke **26/26**, all tickets 01–09 machine-green.
- Local suites: `check_ui.py` 36/36, Playwright visual 3/3.

## Words we use
`GLOSSARY.md` — Owner, Viewer, Memory Album, Public Link, View Size (small/medium/large), Comment Zoom, Thumbnail, Logo, Data Volume, Signup Lock.

## Rules in force
- Patch-bump `VERSION` (+ compose image tag) on every functional push; tags on request.
- Host config only in `.env` (`BASE_URL`, `ALLOW_SIGNUP`, `HOST_PORT`, `DATA_DIR`); `compose.yaml` stays generic.
- Deploy only from `main`: `git pull && sh scripts/deploy.sh`. Prototype branches never touch the server.

## Open human items
- [ ] Ticket 04: one real HEIF phone upload, check it shows.
- [ ] Ticket 06: tablet sign-off (swipe, buttons, auto-hide bars).
- [ ] Ticket 07: backup trial (copy `./data` aside and back).
- [ ] Rotate the `darren` password (shared in chat earlier).

## Useful commands
- Remote smoke: `python scripts/smoke.py --base https://memorees.darrenlane.com --user darren --password <pw>`
- Static checks: `python scripts/check_ui.py`
- Visual: `cd visual && npx playwright test` (needs backend on :8019)
- Deploy (host): `cd /root/docker/memorees && git pull && sh scripts/deploy.sh`
