from pathlib import Path
import sys, json, os, math, io, functools
from collections import namedtuple

assets = Path("/home/user/code/modding/AssetRip/out/")

# print(scenes[6])
# print(scMap['Tutorial_01'])
# sys.exit()


def resolved(f):
    def ret(m, n):
        if isinstance(n, dict):
            assert n["m_FileID"] == 0
            n = n["m_PathID"]
        if isinstance(m, int):
            m = f"level{m}"
        elif (
            not m.startswith("shareda")
            and not m.startswith("res")
            and not m.startswith("level")
        ):
            m = f"level{sceneI[m]}"
        return f(m, n)

    return ret


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
        if k == "__r":
            return self.__r

        def resolve(x, y):
            if isinstance(x, list):
                return [resolve(v, y) for v in x]
            elif isinstance(x, dict):
                if x.get("m_FileID", None) == 0 and "m_PathID" in x.keys():
                    return resource(y, x)
                if "Array" in x.keys():
                    return resolve(x["Array"], y)
                return UnityThing(x, self.__r)
            return x

        if k not in self.__cache.keys():
            if k not in self.__d.keys():
                raise ValueError(
                    f"property `{k}` not found, available: " + repr([*self.__d.keys()])
                )
            self.__cache[k] = resolve(self.__d[k], self.__r)
        return self.__cache[k]

    def __init__(self, d, r, p=None):
        self.__d = d
        self.__cache = {}
        self.__r = r
        if p is not None:
            self.__p = p


oo = Path("/home/user/code/modding/AssetRip/out")
resMap: dict = {}


@resolved
@functools.cache
def resource(m, n):
    global resMap, oo
    if n == 0:
        return None
    if m in resMap.keys():
        mm = resMap[m]
    else:
        mm = {}
        for x in os.listdir(oo / m):
            if " - " in x:
                mm[int(x.split(" - ")[0])] = oo / m / x
            else:
                mm[int(x.split(".")[0])] = oo / m / x
        resMap[m] = mm
    with open(mm[n], "rt") as f:
        return UnityThing(json.load(f), m, n)


nMap = {}


def assetByName(m, n):
    global nMap, oo
    if isinstance(m, int):
        m = f"level{m}"
    elif (
        not m.startswith("shareda")
        and not m.startswith("res")
        and not m.startswith("level")
    ):
        m = f"level{sceneI[m]}"
    # print(m)
    if m in nMap.keys():
        mm = nMap[m]
    else:
        mm = {}
        for x in os.listdir(oo / m):
            if " - " in x:
                i = int(x.split(" - ")[0])
                w = x.split(" - ", 1)[1].removesuffix(".json")
                if w not in mm.keys():
                    mm[w] = []
                mm[w].append(i)
        nMap[m] = mm
    if n not in nMap[m].keys():
        return []
    return nMap[m][n]


def gosByName(m, n):
    for i in assetByName(m, n):
        r = resource(m, i)
        if "m_Component" in r.__d.keys():
            yield r


Pos = namedtuple("Pos", "x y z")


def transform(x):
    lp = x.m_LocalPosition
    ls = x.m_LocalScale
    if x.m_Father is None:
        return (Pos(x=lp.x, y=lp.y, z=lp.z), Pos(x=ls.x, y=ls.y, z=ls.z))
    pp, ps = transform(x.m_Father)
    return (
        Pos(x=pp.x + ps.x * lp.x, y=pp.y + ps.y * lp.y, z=pp.z + ps.z * lp.z),
        Pos(x=ps.x * ls.x, y=ps.y * ls.y, z=ps.z * ls.z),
    )


def goPos(m, n):
    o = goByName(m, n)
    if not o:
        return None
    tr = o.m_Component[0].component
    # print('tr', tr)
    return transform(tr)[0]


def goPosS(m, n):
    # print(m, n)
    p = goPos(m, n)
    if not p:
        return None
    return f"{p.x}, {p.y}"


allDoors = set()


def parseDoor(mn):
    m, n = mn.split("[")
    n = n.split("]")[0]
    allDoors.add((m, n))
    return m, n
    if n == "left2":
        try:
            goPos(m, n)
        except:
            n = "left1"
            goPos(m, n)
    elif n == "door_stagExit":
        try:
            goPos(m, n)
        except:
            n = "door_station"
            goPos(m, n)
    else:
        goPos(m, n)
    return m, n


with open(assets / "globalgamemanagers/11.json", "rt") as f:
    scenes = [x.split("/")[-1].split(".")[0] for x in json.load(f)["scenes"]["Array"]]
    sceneI = {x: i for i, x in enumerate(scenes)}

wh = [None for i in range(len(scenes))]


def zip2(*x):
    i = 1
    for r in x[1:]:
        i += 1
        assert len(r) == len(x[0])
    return zip(*x)


pdts = [
    "Integer",
    "Boolean",
    "Float",
    "String",
    "Color",
    "ObjectReference",
    "LayerMask",
    "Enum",
    "Vector2",
    "Vector3",
    "Vector4",
    "Rect",
    "Array",
    "Character",
    "AnimationCurve",
    "FsmFloat",
    "FsmInt",
    "FsmBool",
    "FsmString",
    "FsmGameObject",
    "FsmOwnerDefault",
    "FunctionCall",
    "FsmAnimationCurve",
    "FsmEvent",
    "FsmObject",
    "FsmColor",
    "Unsupported",
    "GameObject",
    "FsmVector3",
    "LayoutOption",
    "FsmRect",
    "FsmEventTarget",
    "FsmMaterial",
    "FsmTexture",
    "Quaternion",
    "FsmQuaternion",
    "FsmProperty",
    "FsmVector2",
    "FsmTemplateControl",
    "FsmVar",
    "CustomClass",
    "FsmArray",
    "FsmEnum",
]

for i, sc in enumerate(scenes):
    for tmo in gosByName(i, "TileMap"):
        tm = tmo.m_Component[1].component
        wh[i] = (tm.width, tm.height)
    for sm in gosByName(i, "_SceneManager"):
        for comp in map(lambda x: x.component, sm.m_Component):
            if "fsm" not in comp.__d.keys():
                continue
            if (
                "Music" in comp.fsm.name
                or "music" in comp.fsm.name
                or "dreamgate" in comp.fsm.name
            ):
                continue
            for st in comp.fsm.states:
                if st.name == "Set":
                    ad = st.actionData
                    for k, v in ad.__d.items():
                        v = getattr(ad, k)
                        if len(v):
                            print(k, len(v))
                    params = []
                    n = 0
                    for i, (pdt, pn, pdp, pbs) in enumerate(zip(
                        ad.paramDataType,
                        ad.paramName,
                        ad.paramDataPos,
                        ad.paramByteDataSize,
                    )):
                        params.append((pdts[pdt], pn, pdp, ad.byteData[n:n+pbs]))
                        n += pbs
                    si = []
                    for x in ad.actionStartIndex:
                        si.append(x)
                    for aname, cname, aen, aope, asi, asi2, ahash in zip2(
                        ad.actionNames,
                        ad.customNames,
                        ad.actionEnabled,
                        ad.actionIsOpen,
                        ad.actionStartIndex,
                        ad.actionStartIndex[1:] + [len(params)],
                        ad.actionHashCodes,
                    ):
                        print(aname, cname, aen, aope, params[asi:asi2], ahash)
    print(i)
    print(wh[i])
