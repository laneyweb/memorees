# Memorees 📸 — V1 `0.1.0`

Fun, simple memory albums for homelabs. Variant A (Scrapbook) UI winner.

## Run
```powershell
$env:BUILD_HASH=(git rev-parse --short HEAD); $env:BUILD_DATE=(Get-Date -Format o)
docker compose up --build
# open http://localhost:8000
```

## Nginx Proxy Manager
Forward host → `http://<docker-host>:8000`, websockets off, block common exploits on.
Set `BASE_URL=https://memories.yourdomain.com` so public links are correct.

## Data / backup
`./data` holds `memorees.db` + `originals/` + `previews/`. Back up that folder.

## Notes
- Auth: local user/pass, `ALLOW_SIGNUP=false` to lock.
- Albums: multiple per user, per-album font + transition, revocable `/p/<id>` link.
- Uploads: JPG/PNG/HEIF → JPEG preview served (original kept); EXIF camera/lens/exposure/dims + taken/upload dates; GPS hidden by default.
- Viewer: prev/next/pause, Small/Large/Full + fullscreen, swipe on tablets.
- About page shows version/build/date (`/api/version`).
- Prototype: `prototype-ui` branch holds the throwaway 3-variant demo.
