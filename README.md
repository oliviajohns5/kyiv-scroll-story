# Kyiv — City Above the River

A mobile-first, scroll-driven illustrated story through Kyiv, Ukraine.

- Seven full-screen chapters loaded from `content/story.json`
- Separate desktop and mobile artwork
- Sticky scroll camera with cinematic pan, zoom, mist and paper texture
- Compact mobile typography and safe-area-aware controls
- Reduced-motion readable fallback
- Static HTML/CSS/JavaScript, deployed from GitHub to Vercel

## Local verification

```bash
npm run verify
npm run serve
```

Artwork generation is restricted to the five models listed in `image-generation/allowed-models.json`.

Deployment is Git-linked to Vercel from the main branch.
