# 06: Viewer experience on desktop and tablet

**What to build:** the human half of the slideshow: prev/next/pause,
small/large/full plus true fullscreen, transition selector, per-album font,
light/dark theme, tooltips and hover motion, and tablet swipe with
touch-sized controls.

**Blocked by:** 05 (needs a viewable public album).

**Status:** ready-for-agent

- [ ] Prev/next/pause/autoplay, view sizes and fullscreen all respond
- [ ] Transition and font choices visibly apply; theme toggle persists
- [ ] Narrow viewport collapses cleanly; swipe moves slides; controls are touch-sized
- [x] Machine half covered by the visual suite (owner flow, anon public view, tablet render plus touch swipe, About Back, theme, empty states, zero page errors)
- [x] Slideshows start paused; size choice remembered; whole image shown uncropped; fullscreen fills the screen (suite-asserted)
- [x] Viewer bars auto-hide after 3s idle and return on move/tap (suite-asserted)
- [x] Manual checklist signed off on one real tablet — signed off on tablet/iOS
- [ ] App chrome: every button navigates somewhere (About Back returns to the previous screen, never dead)
- [ ] New-album form opens, creates on Enter, closes on Esc/backdrop/Cancel
- [ ] Empty albums (owner and public) show a friendly placeholder, never a broken image
