# 03: Album lifecycle plus revocable public link

**What to build:** an owner creating, renaming, re-linking and deleting an
album remotely, with the public link changing on regeneration and dying on
delete.

**Blocked by:** 02 (needs an authenticated owner session).

**Status:** ready-for-agent

- [ ] Create lists the album; rename persists; font/transition choices persist
- [ ] Regenerating the link changes the public id; the old id 404s
- [ ] Deleting the album removes it and its public id 404s
- [ ] First run result recorded (create id 1 / regen / delete round-trip green)
