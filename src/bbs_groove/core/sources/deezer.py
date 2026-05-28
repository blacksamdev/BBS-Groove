"""Source Deezer — api.deezer.com public, sans clé."""
import re
import requests


class DeezerSource:
    """Charge des tracks depuis URLs Deezer (track/album/playlist/artiste)."""

    API = 'https://api.deezer.com'
    TIMEOUT = 10

    # ------------------------------------------------------------------ #
    #  Entrée principale                                                   #
    # ------------------------------------------------------------------ #

    def get_tracks(self, url: str) -> list[dict]:
        kind, dz_id = self._parse(url)
        if kind == 'track':
            t = self._api(f'/track/{dz_id}')
            return [self._fmt(t)] if t and 'id' in t else []
        if kind == 'album':
            return self._album(dz_id)
        if kind == 'playlist':
            return self._playlist(dz_id)
        if kind == 'artist':
            return self._artist(dz_id)
        return []

    # ------------------------------------------------------------------ #
    #  Parseurs                                                            #
    # ------------------------------------------------------------------ #

    @staticmethod
    def is_deezer(url: str) -> bool:
        return 'deezer.com' in url

    @staticmethod
    def _parse(url: str) -> tuple[str, str]:
        m = re.search(r'deezer\.com(?:/\w{2})?/(track|album|playlist|artist)/(\d+)', url)
        if m:
            return m.group(1), m.group(2)
        return '', ''

    # ------------------------------------------------------------------ #
    #  Sources                                                             #
    # ------------------------------------------------------------------ #

    def _album(self, dz_id: str) -> list[dict]:
        data = self._api(f'/album/{dz_id}')
        if not data:
            return []
        album_name = data.get('title', '')
        year = (data.get('release_date') or '')[:4]
        cover = data.get('cover_xl') or data.get('cover_big') or data.get('cover', '')
        tracks = data.get('tracks', {}).get('data', [])
        return [self._fmt(t, album=album_name, year=year, cover=cover) for t in tracks]

    def _playlist(self, dz_id: str) -> list[dict]:
        tracks = []
        url = f'/playlist/{dz_id}/tracks?limit=200'
        while url:
            data = self._api(url)
            if not data:
                break
            for t in data.get('data', []):
                tracks.append(self._fmt(t))
            url = data.get('next', '').replace(self.API, '') or None
        return tracks

    def _artist(self, dz_id: str) -> list[dict]:
        data = self._api(f'/artist/{dz_id}/top?limit=50')
        if not data:
            return []
        return [self._fmt(t) for t in data.get('data', [])]

    # ------------------------------------------------------------------ #
    #  Formatage                                                           #
    # ------------------------------------------------------------------ #

    def _fmt(self, t: dict, album: str = '', year: str = '', cover: str = '') -> dict:
        art = t.get('artist', {})
        alb = t.get('album', {})
        cover = cover or alb.get('cover_xl') or alb.get('cover_big') or alb.get('cover', '')
        yr = year or (t.get('release_date') or alb.get('release_date') or '')[:4]
        contributors = t.get('contributors', [])
        all_artists = ', '.join(c['name'] for c in contributors) if contributors else art.get('name', '')
        return {
            'title':       t.get('title', ''),
            'artist':      art.get('name', ''),
            'all_artists': all_artists,
            'duration_ms': int(t.get('duration', 0)) * 1000,
            'artwork_url': cover,
            'spotify_id':  '',
            'year':        yr,
            'album':       album or alb.get('title', ''),
            'needs_enrich': False,
        }

    # ------------------------------------------------------------------ #
    #  HTTP                                                                #
    # ------------------------------------------------------------------ #

    def _api(self, path: str) -> dict | None:
        try:
            r = requests.get(f'{self.API}{path}', timeout=self.TIMEOUT)
            r.raise_for_status()
            return r.json()
        except Exception:
            return None
