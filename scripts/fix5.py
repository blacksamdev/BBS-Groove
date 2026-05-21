#!/usr/bin/env python3
path = '/home/bbs/Documents/WIP/Groove/src/bbs_groove/ui/main_window.py'
with open(path) as f:
    content = f.read()

# Fix 1 : _fetch_candidates — premier candidat = version jouée par défaut
old1 = """        try:
            from bbs_groove.core.resolver import Resolver
            candidates = Resolver().resolve_candidates(track)
            if candidates and index == self._playlist.current_index:
                self._candidates = candidates
                self._signals.candidates_ready.emit(candidates, current_url)
        except Exception as e:
            print(f'[fetch_candidates] {e}')"""
new1 = """        try:
            from bbs_groove.core.resolver import Resolver
            candidates = Resolver().resolve_candidates(track)
            if candidates and index == self._playlist.current_index:
                self._candidates = candidates
                # Si l URL courante ne matche aucun candidat,
                # le premier EST ce qui joue (même algo durée)
                if not any(c['url'] == current_url for c in candidates):
                    effective_url = candidates[0]['url']
                else:
                    effective_url = current_url
                self._signals.candidates_ready.emit(candidates, effective_url)
        except Exception as e:
            print(f'[fetch_candidates] {e}')"""
print('1 effective_url:', old1 in content)
content = content.replace(old1, new1)

# Fix 2 : _on_return_from_gaming — déclencher enrichissement si artwork absent
old2 = """        # Artwork
        art_url = track.get('artwork_url')
        if art_url:
            import threading
            threading.Thread(target=self._fetch_artwork, args=(art_url,), daemon=True).start()"""
new2 = """        # Artwork
        art_url = track.get('artwork_url')
        import threading
        if art_url:
            threading.Thread(target=self._fetch_artwork, args=(art_url,), daemon=True).start()
        elif track.get('spotify_id'):
            # Track pas encore enrichi (changement en gaming mode) — enrichir maintenant
            threading.Thread(target=self._enrich_track, args=(idx,), daemon=True).start()"""
print('2 enrich on return:', old2 in content)
content = content.replace(old2, new2)

with open(path, 'w') as f:
    f.write(content)
print('Done')
