# Politique de sécurité

## Versions supportées

Les correctifs de sécurité sont appliqués sur la branche `main`.
Les builds beta sont maintenus en best-effort pendant la phase de test.

## Signaler une vulnérabilité

N'ouvrez **pas** d'issue publique GitHub pour un problème de sécurité.

Utilisez les advisories privés GitHub : https://github.com/blacksamdev/BBS-Groove/security/advisories/new

Merci d'inclure :
- les étapes de reproduction
- la version ou le commit affecté
- l'impact potentiel

Nous accusons réception rapidement, puis nous investiguons et coordonnons une divulgation responsable une fois le correctif disponible.

## Périmètre du projet

Dans le périmètre :
- `src/` (code Python de l'application)
- `io.github.blacksamdev.Groove.json` (manifest Flatpak)
- `.github/workflows/` (pipeline packaging et publication)

Hors périmètre :
- vulnérabilités des composants tiers (`mpv`, `yt-dlp`, `pystray`, runtime KDE)
- problèmes de configuration locale hors projet

Pour les composants tiers, merci de signaler directement au projet amont concerné.
