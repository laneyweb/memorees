# Memorees — where we are (bookmark)

## Status
- `main` at **0.4.0** (the settings screen works: EXIF toggles are reachable and
  save themselves, the theme is a real setting that reaches the public link, the
  default font applies to new albums, exif labels are title-cased).
- **0.3.0** was delete-an-album from the "Your albums" grid, with a confirm dialog;
  the route erases the stored files instead of orphaning them.
- Remote host `https://memorees.darrenlane.com` is still on **0.2.4** - it has not
  had 0.3.0 or 0.4.0 yet. Both need deploying, then a remote smoke run.
- Local suites: `check_ui.py` 51/51, Playwright visual 6/6, local smoke 29/29.

## Words we use
`GLOSSARY.md` — Owner, Viewer, Memory Album, Public Link, View Size (small/medium/large), Comment Zoom, Thumbnail, Logo, Data Volume, Signup Lock.

## Rules in force
- Patch-bump `VERSION` (+ compose image tag) on every functional push; tags on request.
- Host config only in `.env` (`BASE_URL`, `ALLOW_SIGNUP`, `HOST_PORT`, `DATA_DIR`); `compose.yaml` stays generic.
- Deploy only from `main`: `git pull && sh scripts/deploy.sh`. Prototype branches never touch the server.

## Open human items
- [ ] Deploy 0.3.0 + 0.4.0 to the host, then run the remote smoke (29 checks).
- [ ] Ticket 07: backup trial (copy `./data` aside and back).
- [ ] Rotate the `darren` password (shared in chat earlier).
- [ ] Look at the settings screen on a phone - it was only checked at 1280px.

## Closed
- [x] Ticket 04: HEIF phone upload verified.
- [x] Ticket 06: tablet sign-off done (swipe, buttons, auto-hide bars).

## Useful commands
- Remote smoke: `python scripts/smoke.py --base https://memorees.darrenlane.com --user darren --password <pw>`
- Static checks: `python scripts/check_ui.py`
- Visual: `cd visual && npx playwright test` (needs backend on :8019)
- Deploy (host): `cd /root/docker/memorees && git pull && sh scripts/deploy.sh`
