#!/usr/bin/env python3
"""Generate desktop or mobile chapter art through OpenRouter Image API.

Hard restriction: this script refuses any model outside image-generation/allowed-models.json.
It writes assets/generated/<chapter-id>-<variant>.<ext> and updates content/story.json paths.
"""
from __future__ import annotations
import argparse, base64, json, mimetypes, os, sys, time, urllib.error, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / 'image-generation' / 'allowed-models.json').read_text())
ALLOWED = set(CONFIG['allowed_models'])

def ext_for(media_type: str | None) -> str:
    if media_type == 'image/jpeg': return 'jpg'
    if media_type == 'image/webp': return 'webp'
    if media_type == 'image/svg+xml': return 'svg'
    return 'png'

def payload_for(model: str, prompt: str, aspect_ratio: str, seed: int | None):
    p = {"model": model, "prompt": prompt, "aspect_ratio": aspect_ratio}
    if model == 'recraft/recraft-v4.1-flash':
        p['n'] = 1
    elif model == 'black-forest-labs/flux.2-klein-4b':
        p['output_format'] = 'jpeg'
        p['n'] = 1
        if seed is not None: p['seed'] = seed
    elif model == 'sourceful/riverflow-v2.5-fast':
        p.update({'resolution':'2K','output_format':'jpeg','background':'opaque','n':1})
    elif model == 'krea/krea-2-medium-turbo':
        p.update({'resolution':'1K'})
        if seed is not None: p['seed'] = seed
    elif model == 'meta/muse-image':
        # endpoint advertises no public knobs; keep payload minimal
        pass
    return p

def generate(model: str, prompt: str, out_path_base: Path, aspect_ratio='16:9', seed: int | None=None, timeout=240):
    if model not in ALLOWED:
        raise SystemExit(f"Refusing non-allowed image model: {model}")
    key = os.environ.get('OPENROUTER_API_KEY')
    if not key:
        raise SystemExit('OPENROUTER_API_KEY is not set')
    payload = payload_for(model, prompt, aspect_ratio, seed)
    req = urllib.request.Request(
        'https://openrouter.ai/api/v1/images',
        data=json.dumps(payload).encode(),
        headers={
            'Authorization': f'Bearer {key}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'https://kyiv-scroll-story.vercel.app',
            'X-Title': 'Kyiv - City Above the River'
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data=json.load(r)
    except urllib.error.HTTPError as e:
        body=e.read().decode(errors='ignore')[:1200]
        raise RuntimeError(f"OpenRouter image API HTTP {e.code}: {body}") from e
    item=data['data'][0]
    media=item.get('media_type')
    ext=ext_for(media)
    out=out_path_base.with_suffix('.'+ext)
    out.write_bytes(base64.b64decode(item['b64_json']))
    return {"file": str(out.relative_to(ROOT)), "model": model, "media_type": media, "usage": data.get('usage')}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--model', default=CONFIG['default_model'])
    ap.add_argument('--fallbacks', action='store_true', help='try fallback_order until one succeeds')
    ap.add_argument('--limit', type=int, default=0, help='only first N chapters')
    ap.add_argument('--chapter', help='single chapter id')
    ap.add_argument('--variant', choices=['desktop', 'mobile'], default='desktop')
    ap.add_argument('--aspect-ratio', help='defaults to 16:9 for desktop and 9:16 for mobile')
    args=ap.parse_args()
    story=json.loads((ROOT/'content/story.json').read_text())
    aspect_ratio=args.aspect_ratio or ('9:16' if args.variant == 'mobile' else '16:9')
    models=CONFIG['fallback_order'] if args.fallbacks else [args.model]
    for m in models:
        if m not in ALLOWED: raise SystemExit(f"Configured model is not allowed: {m}")
    chapters=story['chapters']
    if args.chapter: chapters=[c for c in chapters if c['id']==args.chapter]
    if args.limit: chapters=chapters[:args.limit]
    outdir=ROOT/'assets/generated'; outdir.mkdir(parents=True, exist_ok=True)
    results=[]
    for i,ch in enumerate(chapters):
        prompt=ch.get('image_prompt') or ch['text']
        if args.variant == 'mobile':
            prompt += ' Portrait 9:16 reinterpretation for a premium mobile story: keep the main landmark in the upper half, preserve depth, and leave a calm darker lower third for a compact text card. Do not crop the landmark.'
        last_err=None
        for model in models:
            try:
                base=outdir/f"{ch['id']}-{args.variant}"
                res=generate(model, prompt, base, aspect_ratio, seed=21000+i+(1000 if args.variant == 'mobile' else 0))
                ch['mobile_image' if args.variant == 'mobile' else 'image']='/'+res['file']
                results.append({"chapter":ch['id'], **res})
                print(json.dumps(results[-1]), flush=True)
                break
            except Exception as e:
                last_err=str(e)
                print(json.dumps({"chapter":ch['id'],"model":model,"error":last_err}), file=sys.stderr, flush=True)
        else:
            raise SystemExit(f"all allowed models failed for {ch['id']}: {last_err}")
        time.sleep(0.5)
    # update only generated chapter image extensions
    all_chapters={c['id']:c for c in story['chapters']}
    for ch in chapters: all_chapters[ch['id']].update(ch)
    (ROOT/'content/story.json').write_text(json.dumps(story, indent=2), encoding='utf-8')
    (ROOT/'image-generation'/f'last-run-{args.variant}.json').write_text(json.dumps(results, indent=2), encoding='utf-8')

if __name__ == '__main__': main()
