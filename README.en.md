# BBS grOOve 🎵

[🇫🇷 Version française](README.md)

**Lightweight audio player — BBS Suite**

BBS grOOve scrapes Spotify metadata via the public embed API, then plays audio from YouTube via yt-dlp + mpv.

---

## Quick Install (Flatpak)

### 1. Add the BBS grOOve repository

```bash
flatpak remote-add --if-not-exists --from bbs-groove \
  https://blacksamdev.github.io/BBS-Groove/bbs-groove.flatpakrepo
```

### 2. Install

```bash
flatpak install bbs-groove io.github.blacksamdev.Groove
```

---

## Usage

- **Paste a Spotify URL** (track, album, playlist) → immediate playback
- **Free search** by artist / title
- **Gaming Mode** : switches to an ultra-light system tray (~38MB)
- Media keys work natively via MPRIS

---

## Update

```bash
flatpak update io.github.blacksamdev.Groove
```

---

## Installation without Flatpak

System dependencies: `mpv`, `python3`

```bash
git clone https://github.com/blacksamdev/BBS-Groove.git
cd BBS-Groove
make install-deps
make install-user
```

System-wide installation:
```bash
sudo make install
```

---

## Build from source (Flatpak)

```bash
git clone https://github.com/blacksamdev/BBS-Groove.git
cd BBS-Groove
sudo flatpak-builder --install --force-clean build-dir io.github.blacksamdev.Groove.json
flatpak run io.github.blacksamdev.Groove
```

---

## Architecture

```
Spotify (public scraping)   → metadata + playlist order
yt-dlp                      → YouTube audio resolution
mpv                         → audio playback (IPC socket)
PyQt6                       → normal mode UI
pystray                     → gaming mode (tray)
```

---

## Tech Stack

| Component   | Technology                      |
|-------------|---------------------------------|
| Metadata    | spotifyscraper (public scraping) |
| Audio       | yt-dlp + mpv                    |
| Normal UI   | Python + PyQt6                  |
| Gaming UI   | pystray (tray icon)             |
| mpv control | Unix IPC socket                 |
| Packaging   | Flatpak                         |
| Distribution| GitHub Pages                    |

---

## Licence

GPL-3.0 — developed by **blacksamdev** — in tribute to Samuel Bellamy 🏴‍☠️, the Prince of Pirates, captain of the Whydah.
