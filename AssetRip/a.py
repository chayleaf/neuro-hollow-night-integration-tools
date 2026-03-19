import os, sys, io, json, functools, struct, math
from pathlib import Path
from PIL import Image, ImageDraw
from collections import namedtuple

b = Path(
    "/data/data/Games/SteamLibrary/steamapps/common/Hollow Knight/hollow_knight_Data"
)
o = Path("out")
r = "resources.assets"


def resolved(f):
    def ret(n):
        if isinstance(n, dict):
            assert n["m_FileID"] == 0
            n = n["m_PathID"]
        return f(n)

    return ret


resMap = {}
for x in os.listdir(o / r):
    if " - " in x:
        resMap[int(x.split(" - ")[0])] = o / r / x
    else:
        resMap[int(x.split(".")[0])] = o / r / x


class UnityThing(object):
    def __repr__(self):
        ret = []
        for k, v in self.__d.items():
            ret.append(f"{k}={repr(v)}")
        return "{" + ", ".join(ret) + "}"

    def __getattr__(self, k):
        if k == "__p":
            return self.__p
        if k == "__d":
            return self.__d

        def resolve(x):
            if isinstance(x, list):
                return [resolve(v) for v in x]
            elif isinstance(x, dict):
                if x.get("m_FileID", None) == 0 and "m_PathID" in x.keys():
                    return resource(x)
                if "Array" in x.keys():
                    return resolve(x["Array"])
                return UnityThing(x)
            return x

        if k not in self.__cache.keys():
            if k not in self.__d.keys():
                raise ValueError(
                    f"property `{k}` not found, available: " + repr([*self.__d.keys()])
                )
            self.__cache[k] = resolve(self.__d[k])
        return self.__cache[k]

    def __init__(self, d, p=None):
        self.__d = d
        self.__cache = {}
        if p is not None:
            self.__p = p


@resolved
@functools.cache
def resource(n):
    global resMap
    if n == 0:
        return None
    with open(resMap[n], "rt") as f:
        return UnityThing(json.load(f), n)


# https://wikis.khronos.org/opengl/S3_Texture_Compression
def undxt5(w, h, data):
    file = io.BytesIO(data)
    ret = []
    rows = [[], [], [], []]
    for row in range(h // 4):
        for x in rows:
            x.clear()
        for col in range(w // 4):
            a0, a1, at0, at1, c0, c1, ct = struct.unpack("<BBIHHHI", file.read(16))
            a = [a0, a1]
            at = at0 + (at1 << 32)
            num = 7 if a0 > a1 else 5
            a.extend((a0 * (num - i) + a1 * i) // num for i in range(1, num))
            if len(a) < 8:
                a.extend([0, 255])
            c = [
                (
                    ((x >> 11) * 527 + 23) >> 6,
                    (((x >> 5) & 0x3F) * 259 + 33) >> 6,
                    ((x & 0x1F) * 527 + 23) >> 6,
                )
                for x in (c0, c1)
            ]
            num = 3 if c0 > c1 else 2
            c.extend(
                tuple(
                    (d * (num - i) + e * i) // num
                    for d, e in zip(c[0], c[1])
                )
                for i in range(1, num)
            )
            if len(c) < 4:
                c.append((0, 0, 0))
            for i in range(16):
                rows[i >> 2].extend(c[(ct >> (i * 2)) & 0b11])
                rows[i >> 2].append(a[(at >> (i * 3)) & 0b111])
        for row in rows:
            ret.extend(row)
    return bytes(ret)


def img(x):
    if x.m_TextureFormat == 12:
        if os.path.exists("cache/" + x.m_Name + ".png"):
            return Image.open("cache/" + x.m_Name + ".png")
    if x.m_IsReadable:
        data = (bytes([*map(ord, getattr(x, "image data"))]),)
    else:
        of = x.m_StreamData.offset
        sz = x.m_StreamData.size
        p = b / x.m_StreamData.path
        with open(p, "rb") as f:
            f.seek(of)
            data = f.read(sz)
    if x.m_TextureFormat == 12:
        data = undxt5(x.m_Width, x.m_Height, data)
    else:
        print(x.m_TextureFormat)
    image = Image.frombytes(
        "RGBA",
        (x.m_Width, x.m_Height),
        data,
    )
    image = image.transpose(Image.FLIP_TOP_BOTTOM)
    if x.m_TextureFormat == 12:
        os.makedirs("cache", exist_ok=True)
        image.save("cache/" + x.m_Name + ".png")
    return image


atlases = {}
textures = {}

# os.makedirs("imgs", exist_ok=True)
for n in [
#     {"m_FileID": 0, "m_PathID": 15295},
#     {"m_FileID": 0, "m_PathID": 15971},
#     {"m_FileID": 0, "m_PathID": 15763},
#     {"m_FileID": 0, "m_PathID": 15583},
#     {"m_FileID": 0, "m_PathID": 15783},
#     {"m_FileID": 0, "m_PathID": 15154},
#     {"m_FileID": 0, "m_PathID": 15362},
#     {"m_FileID": 0, "m_PathID": 15618},
#     {"m_FileID": 0, "m_PathID": 16010},
#     {"m_FileID": 0, "m_PathID": 15152},
#     {"m_FileID": 0, "m_PathID": 15588},
#     {"m_FileID": 0, "m_PathID": 16080},
#     {"m_FileID": 0, "m_PathID": 15132},
#     {"m_FileID": 0, "m_PathID": 15091},
#     {"m_FileID": 0, "m_PathID": 15991},
#     {"m_FileID": 0, "m_PathID": 15236},
#     {"m_FileID": 0, "m_PathID": 15203},
#     {"m_FileID": 0, "m_PathID": 15621},
#     {"m_FileID": 0, "m_PathID": 16087},
#     {"m_FileID": 0, "m_PathID": 15265},
#     {"m_FileID": 0, "m_PathID": 15522},
#     {"m_FileID": 0, "m_PathID": 15006},
#     {"m_FileID": 0, "m_PathID": 15035},
#     {"m_FileID": 0, "m_PathID": 15447},
#     {"m_FileID": 0, "m_PathID": 15206},
#     {"m_FileID": 0, "m_PathID": 15390},
#     {"m_FileID": 0, "m_PathID": 16073},
#     {"m_FileID": 0, "m_PathID": 15705},
#     {"m_FileID": 0, "m_PathID": 15293},
#     {"m_FileID": 0, "m_PathID": 15698},
#     {"m_FileID": 0, "m_PathID": 15051},
#     {"m_FileID": 0, "m_PathID": 16254},
#     {"m_FileID": 0, "m_PathID": 14985},
#     {"m_FileID": 0, "m_PathID": 16037},
#     {"m_FileID": 0, "m_PathID": 15598},
#     {"m_FileID": 0, "m_PathID": 15734},
#     {"m_FileID": 0, "m_PathID": 15102},
#     {"m_FileID": 0, "m_PathID": 15029},
#     {"m_FileID": 0, "m_PathID": 15678},
#     {"m_FileID": 0, "m_PathID": 15987},
#     {"m_FileID": 0, "m_PathID": 16412},
#     {"m_FileID": 0, "m_PathID": 16138},
#     {"m_FileID": 0, "m_PathID": 15585},
#     {"m_FileID": 0, "m_PathID": 15475},
#     {"m_FileID": 0, "m_PathID": 15415},
#     {"m_FileID": 0, "m_PathID": 15126},
#     {"m_FileID": 0, "m_PathID": 15977},
#     {"m_FileID": 0, "m_PathID": 16006},
#     {"m_FileID": 0, "m_PathID": 15534},
#     {"m_FileID": 0, "m_PathID": 15703},
#     {"m_FileID": 0, "m_PathID": 15594},
#     {"m_FileID": 0, "m_PathID": 15270},
#     {"m_FileID": 0, "m_PathID": 15336},
#     {"m_FileID": 0, "m_PathID": 16007},
#     {"m_FileID": 0, "m_PathID": 16327},
#     {"m_FileID": 0, "m_PathID": 16375},
#     {"m_FileID": 0, "m_PathID": 16304},
#     {"m_FileID": 0, "m_PathID": 16338},
#     {"m_FileID": 0, "m_PathID": 16359},
#     {"m_FileID": 0, "m_PathID": 16316},
#     {"m_FileID": 0, "m_PathID": 16406},
#     {"m_FileID": 0, "m_PathID": 16401},
#     {"m_FileID": 0, "m_PathID": 16383},
#     {"m_FileID": 0, "m_PathID": 16332},
#     {"m_FileID": 0, "m_PathID": 16300},
#     {"m_FileID": 0, "m_PathID": 16399},
#     {"m_FileID": 0, "m_PathID": 16407},
#     {"m_FileID": 0, "m_PathID": 16391},
#     {"m_FileID": 0, "m_PathID": 16350},
#     {"m_FileID": 0, "m_PathID": 16376},
#     {"m_FileID": 0, "m_PathID": 16279},
#     {"m_FileID": 0, "m_PathID": 16386},
#     {"m_FileID": 0, "m_PathID": 16417},
#     {"m_FileID": 0, "m_PathID": 16296},
#     {"m_FileID": 0, "m_PathID": 15598},
     {"m_FileID": 0, "m_PathID": 2181},
]:
    try:
        fullc = resource(n)#.m_Sprite
        if fullc.m_SpriteAtlas is None:
            tex = img(fullc.m_RD.texture)
        else:
            if fullc.m_SpriteAtlas.m_Name in atlases.keys():
                at = atlases[fullc.m_SpriteAtlas.m_Name]
            else:
                at = {}
                for x in fullc.m_SpriteAtlas.m_RenderDataMap:
                    at[repr(x.first)] = x.second
                atlases[fullc.m_SpriteAtlas.m_Name] = at
            rd = at[repr(fullc.m_RenderDataKey)]
            if fullc.m_Name in ['Town', 'Tutorial_01']:
                print(fullc)
                print(rd)
                print()
            # print(rd, '==========', fullc.m_RD)
            # print(rd)
            if rd.__d["texture"]["m_PathID"] not in textures.keys():
                textures[rd.__d["texture"]["m_PathID"]] = img(rd.texture).transpose(
                    Image.FLIP_TOP_BOTTOM
                )
            tex = textures[rd.__d["texture"]["m_PathID"]]
            tex = tex.crop(
                (
                    rd.textureRect.x,
                    rd.textureRect.y,
                    rd.textureRect.x + rd.textureRect.width,
                    rd.textureRect.y + rd.textureRect.height,
                )
            ).transpose(Image.FLIP_TOP_BOTTOM)
    except:
        print('err')
        continue
    tex.save("imgs/" + fullc.m_Name + ".png")
sys.exit()


def dumpAnim(n):
    animObj = resource(n)
    # print(animObj)
    assert len(animObj.m_Component) == 2
    q = Path(animObj.m_Name)
    for clip in animObj.m_Component[-1].component.clips:
        print(clip.name)
        if clip.name != 'Fly 4':
            #continue
            pass # sys.exit()
        for i, fr in enumerate(clip.frames):
            c = fr.spriteCollection
            s = fr.spriteId
            sd = c.spriteDefinitions[s]
            bd0, _bd1 = sd.boundsData
            _bd0, bd1 = sd.untrimmedBoundsData
            print(' ', i, bd0.x * 64, bd0.y * 64, _bd1.x * 64, _bd1.y * 64, bd1.x * 64, bd1.y * 64)
            assert str(sd.indices) == "[0, 3, 1, 2, 3, 0]"
            # print(sd)
            # print(sd['uvs'])
            tex = img(c.textures[0])
            # print(sd)
            p0 = sd.uvs[0]
            p1 = sd.uvs[3]
            od = q / clip.name / (str(i) + ".png")
            os.makedirs(od.parent, exist_ok=True)
            if p0.x > p1.x and p1.x > p1.y:
                p0, p1 = p1, p0
                # print(od)
            tex = (
                tex.transpose(Image.FLIP_TOP_BOTTOM)
                .crop(
                    tuple(
                        round(x)
                        for x in [
                            p0.x * tex.width,
                            p0.y * tex.height,
                            p1.x * tex.width,
                            p1.y * tex.height,
                        ]
                    )
                )
                .transpose(Image.FLIP_TOP_BOTTOM)
            )
            if sd.flipped:
                t1 = tex.transpose(Image.FLIP_TOP_BOTTOM).rotate(90, expand=True)
                assert t1.height == tex.width
                assert t1.width == tex.height
                tex = t1
            #tex1 = Image.new("RGBA", (round(bd1.x * 64), round(bd1.y * 64)))
            #tex1.alpha_composite(
            #    tex,
            #    (round((bd1.x - _bd1.x) * 32 + bd0.x * 64), round((bd1.y - _bd1.y) * 32 - bd0.y * 64))
            #)
            tex1 = tex
            tex1.save(od)


for n in []:
    animObj = resource(n)
    assert len(animObj.m_Component) == 2
    q = Path(animObj.m_Name)
    for clip in animObj.m_Component[-1].component.clips:
        print(clip.name, end=' ')
        for i, fr in enumerate(clip.frames):
            d = fr.spriteCollection.spriteDefinitions[fr.spriteId].boundsData[0]
            print(int(d.x*64), int(d.y*64), int(d.z*64), end='; ')
        print()
#sys.exit()
# for n in [5474]:  # [4040]: [7741]:
#    dumpAnim(n)
for n in [7645]:
    dumpAnim(n)
sys.exit()

Pos = namedtuple("Pos", "x y z")


def tr(x):
    lp = x.m_LocalPosition
    ls = x.m_LocalScale
    if x.m_Father is None:
        return (Pos(x=lp.x, y=lp.y, z=lp.z), Pos(x=ls.x, y=ls.y, z=ls.z))
    pp, ps = tr(x.m_Father)
    return (
        Pos(x=pp.x + ps.x * lp.x, y=pp.y + ps.y * lp.y, z=pp.z + ps.z * lp.z),
        Pos(x=ps.x * ls.x, y=ps.y * ls.y, z=ps.z * ls.z),
    )


imgs = []
texts = []


def dumpObj(m, level, c):
    global imgs
    doPrint = False
    if m.__p in c:
        return
    c.add(m.__p)
    if doPrint:
        print(" " * (level * 4), m.m_Name, "{")
    nameRet = None
    if m.m_Name == 'Dream_Gate_Pin':
        return
    if doPrint:
        print(" " * (level * 4), m.m_Component[0].component, "{")
    fullc = None
    halfc = None
    for comp in m.m_Component[1:]:
        cont = False
        for k in [
            "m_LinearVelocityBlending",
            "m_EnlightenVertexStream",
            "edgeCollider2D",
            "m_CullTransparentMesh",
            "fontRU",
            "m_margins",
            "m_Mesh",
        ]:
            if k in comp.component.__d.keys():
                cont = True
                break
        if cont:
            continue
        if "visitedString" in comp.component.__d.keys():
            #print('aodcanjdoiwanjcoi')
            nameRet = comp.component.visitedString
        if "fullSpriteDisplayed" in comp.component.__d.keys():
            fullc = comp.component.fullSprite
            if doPrint:
                print(
                    " " * (level * 4 + 2),
                    "full sprite",
                    comp.component.fullSprite.m_Name,
                )
        elif "m_text" in comp.component.__d.keys():
            if doPrint:
                print(" " * (level * 4 + 2), "text", repr(comp.component.m_text))
            texts.append((tr(m.m_Component[0].component), comp.component.m_text))
        elif "m_Sprite" in comp.component.__d.keys():
            if doPrint:
                print(" " * (level * 4 + 2), "sprite", comp.component.m_Sprite.m_Name)
            halfc = comp.component.m_Sprite
        elif "fsm" in comp.component.__d.keys():
            if doPrint:
                print(" " * (level * 4 + 2), "fsm", comp.component.fsm.name)
        else:
            d = comp.component.__d
            # if 'pd' in d.keys():
            #    pd = d['pd']
            #    d['pd'] = None
            if doPrint:
                print(" " * (level * 4 + 2), comp.component)
            # if 'pd' in d.keys():
            #    d['pd'] = pd
    name = nameRet
    for y in (x.m_GameObject for x in m.m_Component[0].component.m_Children):
        if y.m_Name == 'Compass Icon':
            break
        name1 = dumpObj(y, level + 1, c)
        name = name or name1
    if doPrint:
        print(" " * (level * 4), "}")
    return
    if fullc is None:
        fullc = halfc
    if fullc is not None:
        if name:
            print('!!')
        if fullc.m_SpriteAtlas is None:
            tex = img(fullc.m_RD.texture)
        else:
            if fullc.m_SpriteAtlas.m_Name in atlases.keys():
                at = atlases[fullc.m_SpriteAtlas.m_Name]
            else:
                at = {}
                for x in fullc.m_SpriteAtlas.m_RenderDataMap:
                    at[repr(x.first)] = x.second
                atlases[fullc.m_SpriteAtlas.m_Name] = at
            rd = at[repr(fullc.m_RenderDataKey)]
            if fullc.m_Name in ['Town', 'Tutorial_01']:
                print(fullc)
                print(rd)
                print()
            # print(rd, '==========', fullc.m_RD)
            # print(rd)
            if rd.__d["texture"]["m_PathID"] not in textures.keys():
                textures[rd.__d["texture"]["m_PathID"]] = img(rd.texture).transpose(
                    Image.FLIP_TOP_BOTTOM
                )
            tex = textures[rd.__d["texture"]["m_PathID"]]
            tex = tex.crop(
                (
                    rd.textureRect.x,
                    rd.textureRect.y,
                    rd.textureRect.x + rd.textureRect.width,
                    rd.textureRect.y + rd.textureRect.height,
                )
            ).transpose(Image.FLIP_TOP_BOTTOM)
        imgs.append((name if name else fullc.m_Name, tr(m.m_Component[0].component), tex, fullc.m_Pivot))
            # tex.save("out.png")

            # print(rd)
            # print(fullc)
            # print(fullc.m_SpriteAtlas)
            # raise Exception()
    #return nameRet


m = resource(4791)
# dumpObj(m, 0, set())
# sys.exit()
# print(len(imgs))
# minXyz = Pos(99999, 99999, 99999)
# maxXyz = Pos(-99999, -99999, -99999)
# psc = 64
# ssc = 64
# sc = 100
# for name, (p, s), im, pv in imgs:
#     if (p.x < -10000):
#         print(name)
#         sys.exit()
#     p = Pos(p.x * psc, p.y * -psc, p.z * psc)
#     s = Pos(s.x * ssc, s.y * -ssc, s.z * ssc)
#     w, h = abs(int(im.width * s.x / sc)), abs(int(im.height * s.y / sc))
#     p = Pos(p.x - pv.x * w, p.y - pv.y * h, p.z)
#     q = Pos(p.x + w, p.y + h, p.z)
#     minXyz = Pos(min(minXyz.x, p.x), min(minXyz.y, p.y), min(minXyz.z, p.z))
#     maxXyz = Pos(max(maxXyz.x, q.x), max(maxXyz.y, q.y), max(maxXyz.z, q.z))
# print(minXyz, maxXyz)
# canv = Image.new(
#     "RGBA", (math.ceil(maxXyz.x - minXyz.x), math.ceil(maxXyz.y - minXyz.y))
# )
# imgs.sort(key=lambda x: -x[1][0].z)
# draw = ImageDraw.Draw(canv)
# for name, (p, s), im, pv in imgs:
#     p = Pos(p.x * psc, p.y * -psc, p.z * psc)
#     s = Pos(s.x * ssc, s.y * -ssc, s.z * ssc)
#     w, h = abs(int(im.width * s.x / sc)), abs(int(im.height * s.y / sc))
#     p = Pos(p.x - pv.x * w, p.y - pv.y * h, p.z)
#     if w <= 0 or h <= 0:
#         continue
#     im = im.resize((w, h))
#     if s.x < 0:
#         im = im.transpose(Image.FLIP_LEFT_RIGHT)
#     if s.y > 0:
#         im = im.transpose(Image.FLIP_TOP_BOTTOM)
#     canv.alpha_composite(
#         im,
#         (int(p.x - minXyz.x), int(p.y - minXyz.y)),
#     )
#     draw.rectangle([(int(p.x - minXyz.x), int(p.y - minXyz.y)), (int(p.x - minXyz.x + im.width), int(p.y - minXyz.y + im.height))], outline=(255, 0, 0, 255))
#     draw.text((int(p.x - minXyz.x), int(p.y - minXyz.y)), name, fill=(255, 0, 0, 255))
#     #print(name, p, s, im)
# for (p, s), t in texts:
#     p = Pos(p.x * psc, p.y * -psc, p.z * psc)
#     draw.text((int(p.x - minXyz.x), int(p.y - minXyz.y)), t, fill=(0, 255, 0, 255))
#     #print(p, t)
# print('a')
# canv.save('out.png')
# # print([img[0] for img in imgs])
# sys.exit()
for i, x in enumerate(x.m_GameObject for x in m.m_Component[0].component.m_Children):
    if i == 11:
        # 11 = dream gate pin
        continue
    if i > 14:
        # 15 = compass
        # 16 = shade (oh useful)
        # 17 = flame pins
        # 18 = dreamer pins
        # 19 = markers
        break
    #print(i, x.m_Name)
    for j, y in enumerate(
        y.m_GameObject for y in x.m_Component[0].component.m_Children
    ):
        if y.m_Name == "Grub Pins" or 'Area Name' in y.m_Name:
            continue
        q = x.m_Component[0].component.m_LocalPosition
        p = y.m_Component[0].component.m_LocalPosition
        print("        |", json.dumps(y.m_Name), '->', str(p.x + q.x) + ',', p.y + q.y)
        for z in y.m_Component:
            pass # print("   ", z.component)
        #print()
