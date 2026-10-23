# Kyiv — City Above the River

A mobile-first, scroll-driven illustrated story through Kyiv, Ukraine.

- Seven full-screen chapters loaded from `content/story.json`
- Separate desktop and mobile ink-wash illustrations on warm rice paper
- Sticky scroll camera with cinematic pan, zoom, mist and paper texture
- Compact mobile typography and safe-area-aware controls
- Reduced-motion readable fallback
- Static HTML/CSS/JavaScript, deployed from GitHub to Vercel

## Local verification

```bash
npm run verify
npm run serve
```

To rebuild the deterministic artwork from the credited source photographs:

```bash
python3 -m venv .venv-art
.venv-art/bin/pip install -r requirements-art.txt
.venv-art/bin/python scripts/build_inkwash.py
```

## Image integrity

The live chapter artwork starts from real, licensed Wikimedia Commons photographs and is rendered by a deterministic, non-generative pipeline. It uses edge-preserving tonal simplification, gray-green duotone washes, sparse contours, selective ochre highlights, mist, bloom, and paper grain. Because the renderer transforms the source pixels instead of synthesizing a new scene, landmark geometry, perspective, openings, street axes, and object positions remain photographic.

Sources and licenses are listed in [`CREDITS.md`](CREDITS.md) and on the live `/credits.html` page. All 14 desktop/mobile outputs are visually reviewed before publication.

Deployment is Git-linked to Vercel from the main branch.
