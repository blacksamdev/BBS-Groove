# BBS grOOve 🎵

**Lecteur audio léger — BBS Suite**

BBS grOOve résout chaque titre Spotify via scraping public, puis joue l'audio depuis YouTube via yt-dlp + mpv.

---

## Fonctionnement

- Coller une URL Spotify (track, album, playlist) → lecture immédiate
- Recherche libre artiste / titre
- File de lecture avec shuffle / repeat
- Artwork + métadonnées affichés
- **Mode Gaming** : bascule en tray pystray ultra-léger (~38MB)

---

## Architecture

```
Spotify (scraping public)   → métadonnées + ordre playlist
yt-dlp                      → résolution audio YouTube
mpv                         → lecture audio (IPC socket)
PyQt6                       → UI mode normal
pystray                     → UI mode gaming (tray)
```

---

## Prérequis

- Linux
- mpv installé sur l'hôte
- Flatpak (pour la distribution)

---

## Installation Flatpak

```bash
flatpak remote-add --if-not-exists --from bbs-groove \
  https://blacksamdev.github.io/BBS-Groove/bbs-groove.flatpakrepo

flatpak install bbs-groove io.github.blacksamdev.Groove
```

---

## Installation depuis les sources

```bash
git clone https://github.com/blacksamdev/BBS-Groove.git
cd BBS-Groove
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
./bbs-groove.sh
```

---

## Stack technique

| Composant     | Technologie                    |
|---------------|--------------------------------|
| Métadonnées   | spotifyscraper (scraping public) |
| Audio         | yt-dlp + mpv                   |
| UI normale    | Python + PyQt6                 |
| UI gaming     | pystray (tray icon)            |
| Contrôle mpv  | IPC socket Unix                |
| Packaging     | Flatpak                        |
| Distribution  | GitHub Pages                   |

---

## Licence

GPL-3.0 — développé par blacksamdev — en hommage à Samuel Bellamy 🏴‍☠️, le Prince des Pirates, capitaine du Whydah.
