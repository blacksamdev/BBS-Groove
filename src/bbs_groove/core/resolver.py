import yt_dlp


class Resolver:
    """Résout un dict track (titre + artiste) en URL audio YouTube.
    
    Stratégie :
    - Cherche 5 résultats
    - Score chaque résultat par proximité de durée avec Spotify
    - Prend le plus proche si écart < 15%, sinon le premier résultat
    """

    _YDL_OPTS = {
        'format':      'bestaudio/best',
        'quiet':       True,
        'no_warnings': True,
        'noplaylist':  True,
        'extract_flat': False,
    }

    # Seuil d'acceptation : 15% d'écart max avec la durée Spotify
    _DURATION_THRESHOLD = 0.15

    def resolve(self, track: dict) -> str | None:
        """Retourne l'URL audio directe ou None si échec."""
        artist   = track.get('artist', '')
        title    = track.get('title', '')
        duration = track.get('duration_ms', 0) / 1000  # en secondes

        
        query = f"ytsearch5:{artist} - {title}"

        try:
            with yt_dlp.YoutubeDL(self._YDL_OPTS) as ydl:
                info = ydl.extract_info(query, download=False)
                if not info:
                    return None

                entries = info.get('entries') or [info]
                if not entries:
                    return None

                # Scorer par proximité de durée si on connaît la durée Spotify
                best_entry = entries[0]
                if duration > 0:
                    best_score = float('inf')
                    for entry in entries:
                        if not entry:
                            continue
                        yt_dur = entry.get('duration') or 0
                        if yt_dur > 0:
                            score = abs(yt_dur - duration) / duration
                            if score < best_score:
                                best_score = score
                                best_entry = entry

                    # Si aucun résultat dans le seuil, on garde quand même le meilleur
                    # (on joue toujours quelque chose)

                return self._extract_url(best_entry)

        except Exception as e:
            print(f"[Resolver] {title} : {e}")

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
