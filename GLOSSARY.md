# Memorees — Word List (GLOSSARY.md)

These are the words we use. Use them in code, tickets, and docs. Do not use
other words for the same thing.

- **Owner**: the person with an account. The owner makes albums and uploads photos.
- **Viewer**: a person who opens a public link. A viewer needs no account and cannot change data.
- **Memory Album (Album)**: a named set of photos with one owner. An album has a font and a transition.
- **Photo**: one image in an album. Formats: JPG, PNG, HEIF.
- **Comment**: the multiline text on one photo. Each photo has its own comment.
- **Public Link**: the readonly URL of one album. Format: `/p/<id>`. No login is needed.
- **Slideshow**: the viewer that shows the photos of one album, one at a time.
- **Viewer Controls**: prev, next, pause/play, view size, and fullscreen.
- **View Size**: small, medium, or large (large is the theatre size; true browser fullscreen is a separate button).
- **Transition**: the effect between slides. Values: fade, slide, ken-burns, none.
- **Caption Font**: the text style of comments. Values: handwritten, modern sans, serif bookish.
- **EXIF Data**: facts stored inside the photo file (camera, lens, exposure, size).
- **Taken Date**: the date the photo was taken (from EXIF data).
- **Upload Date**: the date the photo was added to Memorees.
- **Settings**: the page where the owner selects which data the viewer shows. GPS is OFF by default.
- **Theme**: light or dark display. Each viewer selects it.
- **About Page**: the page that shows version, build hash, and build date.
- **Build**: one release of the code, named by version plus commit hash plus date.
- **Data Volume**: the single `./data` folder that holds the database, originals, and previews. Backup means copy this folder.
- **Base URL**: the public address of the server. It is used to make correct public links.
- **Signup Lock**: the `ALLOW_SIGNUP=false` flag. It stops new accounts after the owner account exists.
