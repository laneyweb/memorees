# 07: Backup, proxy and versioning hygiene

**What to build:** the operational tail: one-folder backup actually restores,
proxy serves the app at the public URL, and releases stay traceable.

**Blocked by:** 01, 02, 03, 04, 05, 06 (runs after behaviour is verified).

**Status:** ready-for-agent

- [ ] Copying the data volume aside and back preserves users, albums and photos
- [ ] Public URL serves the app with correct share links (base URL set)
- [ ] Signup lock flag honoured after the owner account exists
- [ ] Release notes name version, commit and migration (if any)
