# BBS grOOve 🎵

**Lecteur audio sans pub, sans compte — BBS Suite**

BBS grOOve résout chaque titre Spotify, Deezer ou recherche libre via scraping public, puis joue l'audio depuis YouTube via yt-dlp + mpv. Pas de clé API. Pas de compte. Pas de pub.

---

## Fonctionnalités

- **Multi-sources** : URL Spotify (track, album, playlist, artiste), URL Deezer, ou recherche libre (artiste, titre, album)
- **Résolution intelligente** : sélectionne la version YouTube la plus proche de la durée originale
- **Sélection de version** : choisir manuellement la version YouTube par titre — persistant cross-session
- **Playlists perso** : créer, renommer, supprimer des playlists locales — ajouter/retirer des titres via clic droit ou bouton ☰
- **Sauvegarde** : enregistrer une playlist Spotify/Deezer en local via le bouton 💾
- **Artwork + métadonnées** : pochette, artiste, année affichés
- **Paroles synchronisées** : karaoké défilant via lrclib.net
- **Sleep timer** : arrêt automatique 15/30/45/60 min avec compte à rebours
- **Mode Gaming** : mini-player flottant draggable
- **Shuffle / Repeat** : lecture aléatoire ou en boucle
- **Préchargement** : 3 titres résolus en avance pour une lecture fluide
- **Kill mpv ciblé** : uniquement le process de l'app, pas tous les mpv du système

---

## Interface

```
┌──────┬──────────────────────────────────────────┐
│      │  [URL / recherche libre...]   [Charger] [💾]│
│  🎵  ├──────────────────────────┬───────────────┤
│      │                          │  Artwork      │
│  📋  │   01. Artiste — Titre    │  Titre        │
│      │   02. Artiste — Titre    │  Artiste·Année│
│  🎮  │   ...                    │  ──────────── │
│      │                          │  Versions ▶   │
├──────┴──────────────────────────┴───────────────┤
│  ⇄  ◀◀  ▶  ▶▶  ↺   ━━━━●━━━  🔊━━━  ⏱ Timer  │
└──────────────────────────────────────────────────┘
```

---

## URLs supportées

```
https://open.spotify.com/track/...
https://open.spotify.com/album/...
https://open.spotify.com/playlist/...
https://open.spotify.com/artist/...
https://www.deezer.com/track/...
https://www.deezer.com/album/...
https://www.deezer.com/playlist/...
```

Ou simplement taper un nom d'artiste / titre dans le champ.

---

## Installation Flatpak (recommandée)

```bash
flatpak remote-add --if-not-exists --from bbs-groove \
  https://blacksamdev.github.io/BBS-Groove/bbs-groove.flatpakrepo

flatpak install bbs-groove io.github.blacksamdev.Groove
flatpak run io.github.blacksamdev.Groove
```

**Prérequis** : mpv installé
```bash
flatpak install flathub io.mpv.Mpv
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

## Données locales

Stockées dans `~/.config/bbs-groove/` :

| Fichier | Contenu |
|---------|---------|
| `track_prefs.json` | Versions YouTube préférées par titre |
| `ui_state.json` | État de l'interface |
| `my_playlists.json` | Playlists personnelles |

Aucune donnée envoyée à des tiers.

---

## Stack technique

| Composant | Technologie |
|-----------|-------------|
| Métadonnées Spotify | spotifyscraper (scraping public) |
| Métadonnées Deezer | api.deezer.com (public, sans clé) |
| Recherche libre | yt-dlp ytsearch |
| Résolution audio | yt-dlp + YouTube |
| Lecture | mpv (IPC socket Unix, kill ciblé par PID) |
| Paroles | lrclib.net (sans clé) |
| UI | Python + PyQt6 |
| Mode Gaming | QWidget flottant |
| Packaging | Flatpak |
| Distribution | GitHub Pages |

---

## Licence

GPL-3.0 — développé par blacksamdev

*En hommage à Samuel Bellamy 🏴‍☠️, le Prince des Pirates, capitaine du Whydah.*
