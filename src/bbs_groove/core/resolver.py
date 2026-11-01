from bbs_groove.logging_utils import log
import yt_dlp


class Resolver:
    """Résout un dict track (titre + artiste) en URL audio YouTube.

    resolve()            → URL du flux audio DIRECT (meilleur match durée)
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
        """Retourne l'URL du flux audio DIRECT du meilleur candidat.

        On résout le flux audio direct (googlevideo) avec NOTRE yt-dlp, au
        lieu de passer une page youtube.com/watch a mpv : le yt-dlp embarque
        dans le Flatpak mpv est souvent trop ancien et genere des URLs
        rejetees par YouTube (HTTP 403 Forbidden), ce qui faisait echouer
        une partie des titres. En resolvant nous-memes, tous les titres
        passent par le meme yt-dlp (a jour).
        """
        candidates = self.resolve_candidates(track)
        if not candidates:
            return None
        best = candidates[0]
        # Page YouTube du meilleur candidat (webpage_url, sinon l'url flat)
        page = best.get('webpage_url') or best.get('url') or ''
        if page:
            direct = self.resolve_from_url(page)
            if direct:
                return direct
            log(f"Resolver: flux direct indisponible pour {best.get('title', '')}, "
                f"repli sur la page YouTube", "warning")
        # Repli : l'URL telle quelle (mpv tentera de la resoudre lui-meme)
        return best.get('url')

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
        """Résout une URL/page YouTube en URL de flux audio direct (fraiche)."""
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
        # En mode bestaudio (resolve_from_url), yt-dlp place l'URL du format
        # choisi dans entry['url'] : on la prend en priorité. En mode flat
        # (resolve_candidates), entry['url'] est la page youtube.com/watch.
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
