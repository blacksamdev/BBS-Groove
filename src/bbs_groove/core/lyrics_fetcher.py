"""Récupère les paroles depuis lrclib.net."""
import urllib.request
import urllib.parse
import json


class LyricsFetcher:
    """Cherche les paroles sur lrclib.net — sans clé API, gratuit."""

    _BASE = 'https://lrclib.net/api'

    def fetch(self, artist: str, title: str, duration_ms: int = 0) -> dict | None:
        """Retourne {'synced': [...], 'plain': str} ou None si non trouvé.

        synced = liste de (seconds: float, line: str)
        plain  = texte brut
        """
        query = urllib.parse.urlencode({'q': f'{artist} {title}'})
        url = f'{self._BASE}/search?{query}'
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'BBS-Groove/1.0'})
            with urllib.request.urlopen(req, timeout=8) as r:
                results = json.loads(r.read())
        except Exception:
            return None

        if not results or not isinstance(results, list):
            return None

        # Choisir le meilleur résultat par proximité de durée
        duration_s = duration_ms / 1000
        best = results[0]
        if duration_s > 0:
            best = min(
                results,
                key=lambda item: abs((item.get('duration') or 0) - duration_s)
            )

        plain   = best.get('plainLyrics', '') or ''
        synced_raw = best.get('syncedLyrics', '') or ''

        synced = []
        if synced_raw:
            for line in synced_raw.splitlines():
                # Format : [mm:ss.xx] texte
                if line.startswith('[') and ']' in line:
                    tag, _, text = line.partition(']')
                    tag = tag.lstrip('[')
                    try:
                        parts = tag.split(':')
                        secs = int(parts[0]) * 60 + float(parts[1])
                        synced.append((secs, text.strip()))
                    except (ValueError, IndexError):
                        pass

        if not plain and not synced:
            return None

        return {'synced': synced, 'plain': plain}
