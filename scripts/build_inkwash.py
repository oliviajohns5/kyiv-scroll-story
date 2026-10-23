#!/usr/bin/env python3
"""Build photo-faithful ink-wash illustrations without generative synthesis."""
from pathlib import Path
import argparse, hashlib, json, re, time, urllib.error, urllib.request
import cv2
import numpy as np
from PIL import Image, ImageOps

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'assets/source'
OUTPUT=ROOT/'assets'/'inkwash'
MANIFEST=ROOT/'image-sources'/'real-photo-manifest.json'
FOCUS={
('dnipro','desktop'):(.48,.50),('dnipro','mobile'):(.52,.48),('golden-gate','desktop'):(.50,.52),('golden-gate','mobile'):(.50,.49),
('sophia','desktop'):(.50,.53),('sophia','mobile'):(.50,.48),('podil','desktop'):(.50,.54),('podil','mobile'):(.50,.47),
('chimaeras','desktop'):(.50,.52),('chimaeras','mobile'):(.50,.47),('metro','desktop'):(.50,.50),('metro','mobile'):(.50,.50),
('maidan','desktop'):(.50,.53),('maidan','mobile'):(.27,.48)}
SIZES={'desktop':(2048,1152),'mobile':(1152,2048)}

def ensure_source(scene,variant):
 target=SOURCE/f'{scene}-{variant}.jpg'
 if target.exists() and target.stat().st_size>100_000:
  return target
 manifest=json.loads(MANIFEST.read_text())
 thumb=manifest['scenes'][scene][variant]['thumb'].split('?')[0]
 url=re.sub(r'/\d+px-', '/1920px-', thumb)
 request=urllib.request.Request(url,headers={'User-Agent':'KyivScrollStory/2.0 (github.com/oliviajohns5/kyiv-scroll-story)'})
 SOURCE.mkdir(parents=True,exist_ok=True)
 for attempt in range(5):
  try:
   with urllib.request.urlopen(request,timeout=180) as response: target.write_bytes(response.read())
   return target
  except urllib.error.HTTPError as error:
   if error.code!=429 or attempt==4: raise
   time.sleep(12*(attempt+1))
 raise RuntimeError(f'failed to download {url}')

def make(scene,variant,outdir=OUTPUT):
 size=SIZES[variant]
 im=Image.open(ensure_source(scene,variant)).convert('RGB')
 im=ImageOps.fit(im,size,Image.Resampling.LANCZOS,centering=FOCUS[(scene,variant)])
 rgb=np.asarray(im)
 bgr=cv2.cvtColor(rgb,cv2.COLOR_RGB2BGR)
 # Flatten photographic detail into broad watercolor masses.
 smooth=cv2.stylization(bgr,sigma_s=92,sigma_r=.48)
 gray=cv2.cvtColor(smooth,cv2.COLOR_BGR2GRAY)
 gray=cv2.bilateralFilter(gray,11,42,42)
 gray=cv2.normalize(gray,None,34,246,cv2.NORM_MINMAX)
 h,w=gray.shape
 # Warm rice-paper/gray-green duotone.
 dark=np.array([38,54,54],np.float32); light=np.array([244,238,220],np.float32)
 t=(gray.astype(np.float32)/255.0)[...,None]
 wash=dark*(1-t)+light*t
 # Lift whites and soften shadows for translucent pigment.
 wash=wash*.88+np.array([247,241,226],np.float32)*.12
 # Sparse contours from strongly smoothed luminance, not microtexture.
 contour_src=cv2.GaussianBlur(cv2.cvtColor(bgr,cv2.COLOR_BGR2GRAY),(0,0),2.6)
 edges=cv2.Canny(contour_src,48,118)
 edges=cv2.dilate(edges,np.ones((2,2),np.uint8),iterations=1)
 edge_alpha=cv2.GaussianBlur(edges,(0,0),.65).astype(np.float32)/255.0
 edge_tooth=cv2.GaussianBlur(np.random.default_rng(17).uniform(.62,1.0,(h,w)).astype(np.float32),(0,0),1.1)
 alpha=(edge_alpha*edge_tooth*.33)[...,None]
 ink=np.array([31,43,43],np.float32)
 result=wash*(1-alpha)+ink*alpha
 # Preserve only naturally warm highlights as restrained ochre pigment.
 src=rgb.astype(np.float32)
 warm=((src[...,0]>src[...,1]*1.08)&(src[...,0]>src[...,2]*1.18)&(src.mean(axis=2)>92)).astype(np.float32)
 warm=cv2.GaussianBlur(warm,(0,0),2.2)[...,None]*.23
 ochre=np.array([172,119,61],np.float32)
 result=result*(1-warm)+ochre*warm
 # Watercolor bloom and pale mist through lower middle.
 bloom=cv2.GaussianBlur(result,(0,0),3.2)
 result=result*.88+bloom*.12
 yy,xx=np.mgrid[0:h,0:w]
 mist=np.exp(-(((yy-h*.70)/(h*.19))**2+((xx-w*.52)/(w*.72))**2))*0.24
 paper=np.array([244,238,222],np.float32)
 result=result*(1-mist[...,None])+paper*mist[...,None]
 # Fibrous paper grain.
 seed=int(hashlib.sha256(f'{scene}-{variant}'.encode()).hexdigest()[:8],16)
 rng=np.random.default_rng(seed)
 noise=rng.normal(0,2.6,(h,w,1))
 fibers=cv2.GaussianBlur(noise,(0,0),.55)
 if fibers.ndim == 2:
  fibers = fibers[...,None]
 result=np.clip(result+fibers,0,255).astype(np.uint8)
 outdir.mkdir(parents=True,exist_ok=True)
 out=outdir/f'{scene}-{variant}.jpg'
 Image.fromarray(result).save(out,'JPEG',quality=92,optimize=True,progressive=True)
 print(out)
 return out

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--scene',action='append');p.add_argument('--variant',choices=['desktop','mobile','all'],default='all');p.add_argument('--output',type=Path,default=OUTPUT);a=p.parse_args()
 scenes=a.scene or ['dnipro','golden-gate','sophia','podil','chimaeras','metro','maidan'];variants=['desktop','mobile'] if a.variant=='all' else [a.variant]
 for s in scenes:
  for v in variants:make(s,v,a.output)
