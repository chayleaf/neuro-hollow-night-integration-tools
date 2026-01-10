from PIL import Image, ImageDraw
from pathlib import Path
import os, sys, io, json, functools, struct, math, hashlib

imgs: list[Image] = []
names = []
rr = Path("/home/user/Downloads/oo")
qq = {}
th = 0
for w in os.listdir(rr):
    qq[w] = []
    for i, r in enumerate(sorted(os.listdir(rr / w), key=lambda x: x.zfill(20))):
        qq[w].append(None)
        imgs.append((Image.open(rr / w / r), w, i))
        th += imgs[-1][0].height
th /= len(imgs)
imgs.sort(key=lambda x: (abs(x[0].height-th),-x[0].width))

dim = 2048
# print(names)
# print(imgs)
# sys.exit()

canv = Image.new("RGBA", (dim, dim))

x = 0
y = 0
h = 0
rrr = []
hh = {}
for im, name, i in imgs:
    ik = (im.tobytes(), im.width, im.height)
    try:
        v = hh[ik]
        rrr.append((name, i, v[0], v[1], im.width, im.height))
        continue
    except:
        pass
    #print(hashlib.sha1(im.tobytes()).hexdigest())
    if x + im.width > dim:
        y += h
        h = 0
        x = 0
    if y + im.height > dim:
        raise Exception("dim too small")
    h = max(h, im.height)
    hh[ik] = (x, y)
    rrr.append((name, i, x, y, im.width, im.height))
    canv.alpha_composite(
        im,
        (x, y),
    )
    x += im.width
canv.save("anim.png")

for name, i, x, y, w, h in rrr:
    qq[name][i] = (x, y, w, h)

for k, v in qq.items():
    print(json.dumps(k) + ',[|' + ';'.join(f'{x},{y},{w},{h}' for x,y,w,h in v) + '|]')
    

sys.exit()
y = 0
for n, w, ims in zip(names, ww, imgs):
    print(json.dumps(n) + ",", str(w) + ",", str(ims[0].height) + ",", len(ims))
    for i, im in enumerate(ims):
        canv.alpha_composite(
            im,
            (i * w, y),
        )
    y += ims[0].height
canv.save("anim.png")
