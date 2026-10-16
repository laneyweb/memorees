# Memorees V1 — Remote Verification Spec

## Problem Statement

Memorees 0.1.0 is deployed on a home server and reachable over the internet.
Before sharing public album links with family, the owner needs confidence that
the deployed build actually behaves the way the grill sessions settled:
Variant A scrapbook UI, local accounts, multiple albums with per-photo
multiline comments, JPG/PNG/HEIF uploads with EXIF plus taken/upload dates,
settings-controlled EXIF visibility (GPS off by default), readonly public
slideshows with viewer controls, and honest version/build info.

## Solution

A remote verification pass against the deployed host, expressed as
tracer-bullet tickets, each verifiable end to end over the public HTTP API
and the served pages. Gaps found become hardening tickets against the same
acceptance suite. A small standard-library smoke script encodes the
machine-checkable half so any host can be re-verified after upgrades.

## User Stories

1. As an owner, I want to create my account with a username and password, so that my albums are private to me.
2. As an owner, I want to log in and out from desktop and tablet browsers, so that sessions behave sanely everywhere.
3. As an owner, I want to disable open signup after creating my account, so that strangers cannot self-register.
4. As an owner, I want to create, rename and delete memory albums, so that I can organise memories into many albums.
5. As an owner, I want to upload JPG, PNG and HEIF photos in bulk, so that phone camera rolls just work.
6. As an owner, I want HEIF photos viewable in a normal browser, so that iPhone shots need no manual conversion.
7. As an owner, I want to write a multiline comment per photo, so that each image carries its own story.
8. As an owner, I want key EXIF shown (camera, lens, exposure, dimensions) plus taken date and upload date, so that the memories keep their context.
9. As an owner, I want GPS hidden on public views by default, so that home locations do not leak.
10. As an owner, I want a settings page choosing which data shows, so that I control the public view.
11. As an owner, I want a caption font per album (handwritten / modern sans / serif bookish), so that each album has its own feel.
12. As an owner, I want a transition effect per album (fade / slide / ken-burns / none), so that slideshows feel alive.
13. As an owner, I want each album to mint a public link that needs no login, so that family can view without accounts.
14. As an owner, I want to regenerate a public link, so that a leaked link can be revoked.
15. As a viewer, I want prev / next / pause controls plus fullscreen, so that I can drive the slideshow.
16. As a viewer, I want small / medium / large view sizes, so that the show fits my screen.
17. As a viewer, I want the album name and author shown, so that I know whose memories these are.
18. As a viewer, I want swipe navigation on a tablet, so that touch just works.
19. As a viewer, I want light and dark themes, so that evening viewing is comfortable.
20. As an owner, I want an About page showing version, build hash and date, so that bug reports can name the build.
21. As an owner, I want one compose file with a single data volume, so that backup is copying one folder.
22. As an owner, I want access through Nginx Proxy Manager, so that the homelab stays on standard ports.
23. As an owner, I want A− / A+ buttons scaling the comment plus tags, so that I can read comfortably.
24. As an owner, I want to delete a photo from an album, so that mistakes and duplicates can go.
25. As an owner, I want big albums to page quietly as I scroll, so that 100 photos feel instant.
26. As an owner, I want small grid thumbnails, so that grids load fast on tablets.

## Implementation Decisions

- Verification goes through the highest seam available: the public HTTP API
  and the served HTML pages. No new test seams are introduced; the smoke
  script speaks plain HTTP like a browser would.
- Login state is a cookie session; the script keeps it in a cookie jar.
- HEIF acceptance is by upload round-trip (server converts to a JPEG
  preview); generating HEIF client-side is out of scope for the script.
- EXIF privacy is asserted server-side on the public payload, not by
  inspecting pixels.
- Tablet behaviour is asserted by responsive markup plus a manual swipe
  checklist; no device lab is required.
- The deployed build hash is compared against the repo HEAD so a stale
  container cannot silently pass.

## Testing Decisions

- A good test here checks external behaviour only: status codes, JSON
  shapes, bytes that render, never internals of the server process.
- The machine half lives in one dependency-free script so it runs on any
  host with Python 3; the human half (tablet swipe, visual feel) is a
  checklist inside its ticket.
- Prior art: the throwaway three-variant UI prototype (kept on its own
  branch) was the manual verification method during design; these tickets
  are its repeatable successor.

## Out of Scope

- The future hosted (non-Docker, DirectAdmin) offering.
- OAuth / email login, collaborative album editing, public downloads or
  bulk export, markdown in comments, native tablet apps.

## Further Notes

- Remote host and throwaway credentials are supplied at run time, never
  stored in the repo; rotate any password shared in chat after the run.
- Smoke results for the first run are recorded on the verification ticket.
