# 05: Public readonly slideshow contract and EXIF privacy

**What to build:** the anonymous public payload for an album: no login
needed, album title plus author, per-photo comment and preview, EXIF
filtered by the owner's settings with GPS absent by default.

**Blocked by:** 03, 04 (needs an album containing a commented photo).

**Status:** ready-for-agent

- [ ] Public payload loads with no session and names album plus author
- [ ] Comments and previews are present per photo
- [ ] `gps` key is absent under default settings; visible fields match settings
- [ ] No original-file download or mutation is reachable anonymously
