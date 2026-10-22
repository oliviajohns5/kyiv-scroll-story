# Kyiv — City Above the River

A mobile-first, scroll-driven illustrated story through Kyiv, Ukraine.

- Seven full-screen chapters loaded from `content/story.json`
- Separate desktop and mobile monochrome photographic retouches
- Sticky scroll camera with cinematic pan, zoom, mist and paper texture
- Compact mobile typography and safe-area-aware controls
- Reduced-motion readable fallback
- Static HTML/CSS/JavaScript, deployed from GitHub to Vercel

## Local verification

```bash
npm run verify
npm run serve
```

## Image integrity

The live chapter artwork is based on real, licensed Wikimedia Commons photographs. The build applies only crop, monochrome tone mapping, contrast, line emphasis, paper texture, vignette, resize, and sharpening. It does not use generative synthesis, so architecture and street geometry remain photographic.

Sources and licenses are listed in [`CREDITS.md`](CREDITS.md) and on the live `/credits.html` page. The live project contains no AI-generated chapter artwork.

Deployment is Git-linked to Vercel from the main branch.
