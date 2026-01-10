from PIL import Image, ImageDraw
from pathlib import Path
import os, sys, io, json, functools, struct, math

imgs: list[list[Image]] = []
ww = []
names = []
rr = Path("/home/user/Downloads/oo")
for w in os.listdir(rr):
    names.append(w)
    imgs.append([])
    ww.append(0)
    for r in sorted(os.listdir(rr / w), key=lambda x: x.zfill(20)):
        imgs[-1].append(Image.open(rr / w / r))
        ww[-1] = max(ww[-1], imgs[-1][-1].width)

canv = Image.new("RGBA", (max(w * len(y) for w, y in zip(ww, imgs)), sum(x[0].height for x in imgs)))

y = 0
for n, w, ims in zip(names, ww, imgs):
    print(json.dumps(n) + ',', str(w) + ',', str(ims[0].height) + ',', len(ims))
    for i, im in enumerate(ims):
        canv.alpha_composite(
            im,
            (i * w, y),
        )
    y += ims[0].height
canv.save("anim.png")
