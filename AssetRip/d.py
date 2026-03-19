from PIL import Image, ImageDraw
from pathlib import Path
import os, sys, io, json, functools, struct, math, hashlib
import numpy as np

def find_ofs(
    im0: Image.Image,
    im1: Image.Image,
) -> tuple[int, int]:
    assert im0.mode == "RGBA"
    assert im1.mode == "RGBA"
    rgba0 = np.asarray(im0, dtype=np.uint8)
    rgba1 = np.asarray(im1, dtype=np.uint8)
    h0, w0 = rgba0.shape[:2]
    h1, w1 = rgba1.shape[:2]
    assert h1 >= h0
    assert w1 >= w0
    best = 9999999999
    ret = (0, 0)
    for y in range(0, h1 - h0 + 1):
        for x in range(0, w1 - w0 + 1):
            score = np.absolute(rgba1[y : y + h0:, x : x + w0] - rgba0).sum()
            if not score: return x, y
            if score < best:
                best = score
                ret = (x, y)
    return ret

imgs: list[Image] = []
names = []
rq = Path("Grimmchild Anim")
rr = Path("/home/user/Downloads/pp")
qq = {}
th = 0
for w in os.listdir(rr):
    qq[w] = []
    for i, r in enumerate(sorted(os.listdir(rr / w), key=lambda x: x.zfill(20))):
        qq[w].append(None)
        im = Image.open(rr / w / r)
        im0 = Image.open(rq / w / r)
        print(w, i, im.width, im0.width, im.height, im0.height)
        if im.height < im0.height or im.width < im0.width or im.width % 2 != im0.width % 2 or im.height % 2 != im0.height % 2:
            w00 = max(im.width, im0.width)
            h00 = max(im.height, im0.height)
            im1 = Image.new("RGBA", (w00 + (w00 - im0.width) % 2, h00 + (h00 - im0.height) % 2))
            im1.alpha_composite(
                im,
                ((im1.width - im.width) // 2, (im1.height - im.height) // 2),
            )
            im = im1
        ox, oy = find_ofs(im0, im)
        o1x, o1y = ox * 2 - (im.width - im0.width), oy * 2 - (im.height - im0.height)
        if o1x or o1y:
            im1 = Image.new("RGBA", (im.width + abs(o1x), im.height + abs(o1y)))
            im1.alpha_composite(
                im,
                (-o1x if o1x < 0 else 0, -o1y if o1y < 0 else 0),
            )
            im = im1
        bbl, bbt, bbr, bbb = im.getbbox()
        bbl = min(bbl, (im.width - im0.width) // 2)
        bbr = max(bbr, (im.width + im0.width) // 2)
        bbt = min(bbt, (im.height - im0.height) // 2)
        bbb = max(bbb, (im.height + im0.height) // 2)
        cx, cy = min(bbl, im.width - bbr), min(bbt, im.height - bbb)
        if cx or cy:
            im = im.crop((cx, cy, im.width - cx, im.height - cy))
            os.makedirs('aaaa/' + w, exist_ok=True)
            im.save(f'aaaa/{w}/{i}.png')
        imgs.append((im, w, i))
        th += imgs[-1][0].height
th /= len(imgs)
imgs.sort(key=lambda x: (-x[0].height,-x[0].width))

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
