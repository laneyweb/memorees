# 10: Delete an album from the albums page

**What to build:** an owner deleting an album from the "Your albums" grid, with
a confirm dialog that names the album and its photo count, warns that the
uploaded images are erased and the public link stops working, and a route that
really removes the stored files.

**Blocked by:** 03 (album lifecycle; this finishes the delete half of it) and
08 (the thumbnail × and the file cleanup this route mirrors).

**Status:** machine-green (local)

- [x] The × on an album card opens the dialog and does not open the album
- [x] The dialog names the album; the count reads "1 photo" / "N photos"
- [x] An album with no photos says "This album has no photos." and promises no file deletion
- [x] Cancel, Escape and a backdrop click close it and change nothing
- [x] Confirm removes the card, keeps the grid, and stacks no second dialog
- [x] `DELETE /api/albums/{aid}` removes the album row, its photo rows, and the
      original, preview and thumbnail files of every photo
- [x] Deleting an album that is absent is 404 (smoke); another owner's album is
      404 (checked by hand against a local host)
- [x] The public link 404s after the delete
- [x] `check_ui.py` invariants pass (41/41); Playwright asserts the card is gone
      and the data dir lost its files; smoke asserts the double delete is 404
