# 01: Remote version and About match the repo build

**What to build:** confidence that the running container is the code we think
it is: the version endpoint reports the shipped version and a build
provenance, and the About page shows the same to a human.

**Blocked by:** None (can start immediately).

**Status:** ready-for-agent

- [ ] `GET /api/version` returns the shipped version and a non-`dev` build hash/date on a real deploy
- [ ] Build hash equals the deployed commit (stale containers fail loudly)
- [ ] Landing page serves and names the product; About view shows version/build/date
- [ ] Result recorded (first run: `0.1.0 / 5c9d456 / 2026-10-16`, all green)
