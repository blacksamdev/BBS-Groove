# BBS grOOve 🎵

**Lecteur audio sans pub, sans compte — BBS Suite**

BBS grOOve résout chaque titre Spotify, Deezer ou artiste via scraping public, puis joue l'audio depuis YouTube via yt-dlp + mpv. Pas de clé API. Pas de compte. Pas de pub.

---

## Fonctionnalités

- **Multi-sources** : URL Spotify (track, album, playlist, artiste) ou URL Deezer
- **Résolution intelligente** : sélectionne la version YouTube la plus proche de la durée originale
- **Sélection de version** : choisir manuellement la version YouTube souhaitée par titre — persistant d'une session à l'autre
- **Artwork + métadonnées** : pochette, artiste, année affichés
- **Paroles synchronisées** : karaoké défilant via lrclib.net
- **Sleep timer** : arrêt automatique 15/30/45/60 min avec compte à rebours
- **Mode Gaming** : mini-player flottant draggable, léger et non intrusif
- **Shuffle / Repeat** : lecture aléatoire ou en boucle
- **Préchargement** : 3 titres résolus en avance pour une lecture fluide

---

## Captures d'écran

*À venir*

---

## Architecture

```
Spotify / Deezer (scraping public)  → métadonnées + ordre playlist
yt-dlp                              → résolution audio YouTube (scoring durée)
mpv                                 → lecture audio (IPC socket Unix)
PyQt6                               → UI principale
lrclib.net                          → paroles synchronisées (sans clé API)
```

---

## Installation Flatpak (recommandée)

```bash
flatpak remote-add --if-not-exists --from bbs-groove \
  https://blacksamdev.github.io/BBS-Groove/bbs-groove.flatpakrepo

flatpak install bbs-groove io.github.blacksamdev.Groove
flatpak run io.github.blacksamdev.Groove
```

**Prérequis** : mpv installé sur l'hôte
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

## Utilisation

1. Coller une URL Spotify ou Deezer dans le champ en haut
2. Appuyer sur **Charger**
3. La lecture démarre automatiquement

**URLs supportées :**
```
https://open.spotify.com/track/...
https://open.spotify.com/album/...
https://open.spotify.com/playlist/...
https://open.spotify.com/artist/...
https://www.deezer.com/track/...
https://www.deezer.com/album/...
https://www.deezer.com/playlist/...
```

**Mode Gaming** : cliquer sur 🎮 pour basculer en mini-player flottant.

---

## Données locales

BBS grOOve sauvegarde uniquement dans `~/.config/bbs-groove/` :

| Fichier | Contenu |
|---------|---------|
| `track_prefs.json` | Versions YouTube préférées par titre |
| `ui_state.json` | État de l'interface (panel versions, etc.) |

Aucune donnée envoyée à des tiers.

---

## Stack technique

| Composant | Technologie |
|-----------|-------------|
| Métadonnées Spotify | spotifyscraper (scraping public) |
| Métadonnées Deezer | api.deezer.com (public, sans clé) |
| Résolution audio | yt-dlp + YouTube |
| Lecture | mpv (IPC socket Unix) |
| Paroles | lrclib.net (sans clé) |
| UI | Python + PyQt6 |
| Mode Gaming | QWidget flottant |
| Packaging | Flatpak |
| Distribution | GitHub Pages |

---

## Développement

```bash
# Debug
flatpak run io.github.blacksamdev.Groove --debug

# Logs
~/.cache/bbs-groove/groove.log
```

---

## Licence

GPL-3.0 — développé par blacksamdev

*En hommage à Samuel Bellamy 🏴‍☠️, le Prince des Pirates, capitaine du Whydah.*
