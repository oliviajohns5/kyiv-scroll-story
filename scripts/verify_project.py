#!/usr/bin/env python3
from pathlib import Path
import json, re, sys
root=Path(sys.argv[1] if len(sys.argv)>1 else '.')
required=['index.html','styles.css','script.js','favicon.svg','content/story.json','image-sources/real-photo-manifest.json','credits.html','CREDITS.md']
missing=[p for p in required if not (root/p).exists()]
if missing: raise SystemExit(f"missing files: {missing}")
story=json.loads((root/'content/story.json').read_text())
assert len(story['chapters']) >= 6, 'need at least six chapters'
ids=[c['id'] for c in story['chapters']]
assert len(ids)==len(set(ids)), 'chapter ids must be unique'
for chapter in story['chapters']:
    for key in ('image', 'mobile_image'):
        asset = root / chapter[key].lstrip('/')
        assert asset.exists() and asset.stat().st_size > 100_000, f'missing or undersized {key}: {asset}'
        assert '/retouched/' in chapter[key], f'live story must use real-photo retouches: {chapter[key]}'
html=(root/'index.html').read_text()
for token in ['viewport','description','chapterNav','staticStory']:
    assert token in html, f'missing {token}'
css=(root/'styles.css').read_text()
assert 'prefers-reduced-motion' in css, 'missing reduced-motion fallback'
js=(root/'script.js').read_text()
assert 'fetch(\'/content/story.json\')' in js or 'fetch("/content/story.json")' in js, 'script must load editable story json'
print(f"OK: {len(story['chapters'])} chapters, static files verified")
