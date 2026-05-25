import re
from spotify_scraper import SpotifyClient


class SpotifySource:
    """Scrape les métadonnées Spotify via l'API embed publique.
    Zéro clé API. Zéro compte developer. Zéro existence chez Spotify."""

    def __init__(self):
        self._client = SpotifyClient()

    # ------------------------------------------------------------------ #
    #  Public                                                              #
    # ------------------------------------------------------------------ #

    def get_tracks(self, url: str) -> list[dict]:
        url = self._normalize_url(url)
        kind = self._parse_kind(url)
        if kind == 'track':
            track = self._client.get_track_info(url)
            return [self._format_track(track, full=True)] if track else []
        if kind == 'playlist':
            return self._playlist_tracks(url)
        if kind == 'album':
            return self._album_tracks(url)
        if kind == 'artist':
            return self._artist_top_tracks(url)
        return []

    def enrich_track(self, track: dict) -> dict:
        """Récupère les infos complètes d'un track (artwork, album, année).
        Appelé en arrière-plan quand le titre commence à jouer."""
        sid = track.get('spotify_id', '')
        if not sid:
            return track
        try:
            url = f'https://open.spotify.com/track/{sid}'
            full = self._client.get_track_info(url)
            if full:
                enriched = self._format_track(full, full=True)
                # Merger — conserver ce qu'on avait si plus riche
                for key in ('artwork_url', 'album', 'year', 'release_date', 'all_artists'):
                    if enriched.get(key):
                        track[key] = enriched[key]
        except Exception as e:
            pass
        return track

    def close(self):
        self._client.close()

    # ------------------------------------------------------------------ #
    #  Privé                                                               #
    # ------------------------------------------------------------------ #

    def _artist_top_tracks(self, url: str) -> list[dict]:
        """Simule un best-of artiste via YouTube search (API Spotify embed limitée)."""
        print(f'[artist] url={url}', flush=True)
        try:
            info = self._client.get_artist_info(url)
            if not info or not info.get('name'):
                return []
            artist_name = info['name']
            artist_img  = (info.get('images') or [{}])[0].get('url', '')
            import yt_dlp
            opts = {'quiet': True, 'no_warnings': True, 'noplaylist': True, 'extract_flat': True}
            query = f'ytsearch20:{artist_name}'
            with yt_dlp.YoutubeDL(opts) as ydl:
                res = ydl.extract_info(query, download=False)
            entries = res.get('entries', []) if res else []
            tracks = []
            for e in entries:
                if not e:
                    continue
                dur = e.get('duration') or 0
                if not (90 <= dur <= 600):  # 1:30 à 10 min — filtrer interviews/lives trop longs
                    continue
                title = e.get('title', '')
                import re as _re
                yt_url  = e.get('url', '')
                vid     = _re.search(r'v=([^&]+)', yt_url)
]+)', yt_url)
                thumb   = f'https://img.youtube.com/vi/{vid.group(1)}/hqdefault.jpg' if vid else artist_img
                t = self._format_track({
                    'name':        title,
                    'uri':         '',
                    'id':          '',
                    'duration_ms': int(dur * 1000),
                    'artists':     [{'name': artist_name}],
                })
                t['artwork_url'] = thumb
                t['needs_enrich'] = False
                tracks.append(t)
            return tracks
        except Exception as e:
            print(f'[artist] ERROR: {e}', flush=True)
            import traceback; traceback.print_exc()
            return []

    @staticmethod
    def _normalize_url(url: str) -> str:
        return re.sub(r'open\.spotify\.com/intl-[a-z]+/', 'open.spotify.com/', url)

    def _parse_kind(self, url: str) -> str | None:
        for kind in ('track', 'playlist', 'album', 'artist'):
            if f'/{kind}/' in url:
                return kind
        return None

    def _playlist_tracks(self, url: str) -> list[dict]:
        playlist = self._client.get_playlist_info(url)
        if not playlist:
            return []
        tracks = []
        for item in playlist.get('tracks', []):
            t = item.get('track') or item
            if t:
                tracks.append(self._format_track(t, full=False))
        return tracks

    def _album_tracks(self, url: str) -> list[dict]:
        album = self._client.get_album_info(url) if hasattr(self._client, 'get_album_info') else None
        if not album:
            track = self._client.get_track_info(url)
            return [self._format_track(track, full=True)] if track else []
        artwork      = self._extract_artwork(album)
        release_date = album.get('release_date', '') or track.get('release_date', '')
        year         = release_date[:4] if release_date else ''
        tracks = []
        for t in album.get('tracks', []):
            fmt = self._format_track(t, full=False)
            fmt['album']       = album.get('name', '')
            fmt['artwork_url'] = fmt['artwork_url'] or artwork
            fmt['year']        = fmt['year'] or year
            tracks.append(fmt)
        return tracks

    def _format_track(self, track: dict, full: bool = False) -> dict:
        artists_raw = track.get('artists', [])
        if artists_raw:
            all_artists = ', '.join(a.get('name', '') for a in artists_raw if a.get('name'))
            artist = artists_raw[0].get('name', '')
        else:
            artist = track.get('artist', '')
            all_artists = artist

        album = track.get('album', {})
        if isinstance(album, str):
            album_name   = album
            artwork      = None
            release_date = ''
        elif album:
            album_name   = album.get('name', '')
            artwork      = self._extract_artwork(album)
            release_date = album.get('release_date', '') or track.get('release_date', '')
        else:
            album_name   = ''
            artwork      = None
            release_date = ''

        if not artwork:
            artwork = self._extract_artwork(track)

        year = release_date[:4] if release_date else ''

        uri = track.get('uri', '')
        sid = track.get('id', '') or (uri.split(':')[2] if uri.count(':') == 2 else '')
        return {
            'title':        track.get('name', track.get('title', '')),
            'artist':       artist,
            'all_artists':  all_artists,
            'album':        album_name,
            'artwork_url':  artwork,
            'duration_ms':  track.get('duration_ms', track.get('duration', 0)),
            'spotify_id':   sid,
            'year':         year,
            'release_date': release_date,
            'is_explicit':  track.get('is_explicit', False),
            'track_number': track.get('track_number', ''),
            # Flag pour savoir si on doit enrichir
            'needs_enrich': not full and not artwork,
        }

    @staticmethod
    def _extract_artwork(obj: dict) -> str | None:
        if not obj:
            return None
        images = obj.get('images') or obj.get('coverArt', {}).get('sources', [])
        if images and isinstance(images, list):
            return images[0].get('url') or images[0].get('src')
        return None
