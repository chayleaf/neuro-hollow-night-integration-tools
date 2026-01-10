from PIL import Image, ImageDraw
from pathlib import Path
import os, sys, io, json, functools, struct, math
#rr = Path("HUD Anim/Health Max Up")
rr = Path("/home/user/Downloads/oo/Health Max Up")
w = 0
h = 0
imgs = []
qq = [(4, 16), (2, 4), (0, 2), (-4, 16), (0, 4), (0, 3), (0, 12), (0, 4), (0, 2), (0, 12), (0, 4), (0, 2), (0, 11), (-1, 13)]
for q, (i, r) in zip(qq, enumerate(sorted(os.listdir(rr), key=lambda x: x.zfill(20)))):
    img = Image.open(rr/r)
    w = max(w, img.width)
    h = max(h, img.height)
    imgs.append((img, q))

for i, (img, q) in enumerate(imgs):
    canv = Image.new("RGBA", (w, h))
    canv.alpha_composite(
        img,
        ((canv.width - img.width) // 2 - q[0], (canv.height - img.height) // 2 - q[1])
    )
    canv.save('tt/' + str(i) + '.png')
