from bbs_groove.logging_utils import log
import yt_dlp


class Resolver:
    """Résout un dict track (titre + artiste) en URL audio YouTube.

    resolve()            → URL directe (meilleur match durée)
    resolve_candidates() → liste des 5 résultats avec métadonnées
    """

    _YDL_OPTS = {
        'format':       'bestaudio/best',
        'quiet':        True,
        'no_warnings':  True,
        'noplaylist':   True,
        'extract_flat': False,
    }
    _YDL_FLAT = {
        'quiet':        True,
        'no_warnings':  True,
        'noplaylist':   True,
        'extract_flat': True,
    }

    _DURATION_THRESHOLD = 0.15  # 15% d'écart max

    def resolve(self, track: dict) -> str | None:
        """Retourne l'URL du meilleur candidat selon la durée Spotify."""
        candidates = self.resolve_candidates(track)
        if not candidates:
            return None
        # Prend le premier (déjà trié par score durée)
        return candidates[0]['url']

    def resolve_candidates(self, track: dict) -> list[dict]:
        """Retourne jusqu'à 5 candidats triés par proximité de durée.

        Chaque candidat : {url, title, channel, duration_s, score}
        Le premier est le meilleur match.
        """
        artist   = track.get('artist', '')
        title    = track.get('title', '')
        duration = track.get('duration_ms', 0) / 1000

        query = f"ytsearch5:{artist} - {title}"

        try:
            with yt_dlp.YoutubeDL(self._YDL_FLAT) as ydl:
                info = ydl.extract_info(query, download=False)
                if not info:
                    return []

                entries = info.get('entries') or [info]
                candidates = []

                for entry in entries:
                    if not entry:
                        continue
                    url = self._extract_url(entry)
                    if not url:
                        continue
                    yt_dur = entry.get('duration') or 0
                    score  = (abs(yt_dur - duration) / duration
                              if duration > 0 and yt_dur > 0 else 1.0)
                    candidates.append({
                        'url':         url,
                        'webpage_url': entry.get('webpage_url', ''),
                        'title':       entry.get('title', ''),
                        'channel':     entry.get('channel') or entry.get('uploader', ''),
                        'duration_s':  yt_dur,
                        'score':       score,
                    })

                # Trier par score (plus proche = meilleur)
                candidates.sort(key=lambda c: c['score'])
                return candidates

        except Exception as e:
            log(f"Resolver: {title} : {e}", "warning")

        return []

    def resolve_from_url(self, yt_url: str) -> str | None:
        """Résout une URL YouTube (pérenne) en URL streaming fraîche."""
        try:
            with yt_dlp.YoutubeDL(self._YDL_OPTS) as ydl:
                info = ydl.extract_info(yt_url, download=False)
                if info:
                    return self._extract_url(info)
        except Exception as e:
            log(f"Resolver.resolve_from_url: {e}", "warning")
        return None

    @staticmethod
    def _extract_url(entry: dict) -> str | None:
        if not entry:
            return None
        if 'url' in entry:
            return entry['url']
        formats = entry.get('formats', [])
        audio = [f for f in formats
                 if f.get('vcodec') == 'none' and f.get('acodec') != 'none']
        if audio:
            return audio[-1]['url']
        if formats:
            return formats[-1]['url']
        return None
