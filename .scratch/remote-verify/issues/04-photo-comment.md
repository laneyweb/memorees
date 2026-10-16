# 04: Photo upload with per-photo multiline comment

**What to build:** bulk photo upload to an album with a served preview per
photo, and a multiline comment that round-trips exactly (line breaks kept).

**Blocked by:** 03 (needs an album to upload into).

**Status:** ready-for-agent

- [ ] PNG/JPG upload returns a count and each photo serves its preview bytes
- [ ] A multiline comment saves and reads back byte-identical
- [ ] Taken date (when present in EXIF) and upload date are recorded
- [ ] HEIF checked by real phone upload at least once (script covers PNG/JPG)
