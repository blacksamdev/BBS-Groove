import yt_dlp


class Resolver:
    """Résout un dict track (titre + artiste) en URL audio YouTube."""

    _YDL_OPTS = {
        'format':        'bestaudio/best',
        'quiet':         True,
        'no_warnings':   True,
        'noplaylist':    True,
        'extract_flat':  False,
    }

    def resolve(self, track: dict) -> str | None:
        """Retourne l'URL audio directe ou None si échec."""
        query = f"ytsearch1:{track['artist']} - {track['title']}"
        try:
            with yt_dlp.YoutubeDL(self._YDL_OPTS) as ydl:
                info = ydl.extract_info(query, download=False)
                if not info:
                    return None
                entry = info['entries'][0] if 'entries' in info else info
                # URL directe si disponible
                if 'url' in entry:
                    return entry['url']
                # Sinon meilleur format audio pur
                formats = entry.get('formats', [])
                audio = [f for f in formats
                         if f.get('vcodec') == 'none' and f.get('acodec') != 'none']
                if audio:
                    return audio[-1]['url']
                if formats:
                    return formats[-1]['url']
        except Exception as e:
            print(f"[Resolver] {track.get('title', '?')} : {e}")
        return None
