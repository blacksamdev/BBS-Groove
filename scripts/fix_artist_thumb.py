import re
path = '/home/bbs/Documents/WIP/Groove/src/bbs_groove/core/sources/spotify.py'
with open(path) as f:
    content = f.read()

# Trouver et remplacer la section problématique
old = r"""                import re as _re
                yt_url  = e.get('url', '')
                vid     = _re.search(r'(?:v=|youtu\.be/)([^&\n]+)', yt_url)
                thumb   = f'https://img.youtube.com/vi/{vid.group(1)}/hqdefault.jpg' if vid else artist_img"""

new = """                yt_url  = e.get('url', '')
                _vid    = re.search(r'(?:v=|youtu\\.be/)([^&]+)', yt_url)
                thumb   = (f'https://img.youtube.com/vi/{_vid.group(1)}/hqdefault.jpg'
                           if _vid else artist_img)"""

print('Found:', old in content)
content = content.replace(old, new)

# Ajouter import re en haut si pas déjà là
if 'import re' not in content[:200]:
    content = 'import re\n' + content
    print('Added import re')

with open(path, 'w') as f:
    f.write(content)

# Vérifier syntaxe
import py_compile
try:
    py_compile.compile(path, doraise=True)
    print('Syntax OK')
except py_compile.PyCompileError as e:
    print(f'Syntax ERROR: {e}')
