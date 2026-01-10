from pathlib import Path
import sys, json, os, math, io, functools
from collections import namedtuple

p = Path("RandomizerMod/RandomizerMod/Resources")
_logic = {}
_data = {}
for a, b in [(p / "Logic", _logic), (p / "Data", _data)]:
    for x in os.listdir(a):
        with open(a / x, "rt", encoding="utf-8-sig") as f:
            t = f.read()
            b[x.split(".")[0]] = json.loads(
                "\n".join([x.split("//")[0] for x in t.split("\n")])
            )
AND = 1
OR = 2
LPAREN = 3
RPAREN = 4


def tokenize(x: str):
    ret: list[int | str] = []
    tok = ""
    escape = False
    for c in x:
        if escape:
            tok += c
            if c == "]":
                escape = False
            continue
        if c == "[":
            tok += c
            escape = True
            continue
        if c.isspace():
            add = None
        elif c == "|":
            add = OR
        elif c == "+":
            add = AND
        elif c == "(":
            add = LPAREN
        elif c == ")":
            add = RPAREN
        else:
            tok += c
            continue
        if tok:
            ret.append(tok)
            tok = ""
        if add is not None:
            ret.append(add)
    if tok:
        ret.append(tok)
        tok = ""
    return ret


trNames = {}
locNames = set()


def resolve(x):
    if x in ["LEFTDASH", "RIGHTDASH", "ANYDASH", "FULLDASH"]:
        return "PlayerData.instance.hasDash"
    if x in trNames.keys():
        return ("transition", x)
    if x in ["ACID", "SWIM"]:
        return "PlayerData.instance.hasAcidArmour"
    if x in ["LEFTCLAW", "RIGHTCLAW", "ANYCLAW", "FULLCLAW"]:
        return "PlayerData.instance.hasWalljump"
    if x in ["LEFTSUPERDASH", "RIGHTSUPERDASH", "FULLSUPERDASH"]:
        return "PlayerData.instance.hasSuperDash"
    if x in ["LEFTSHADOWDASH", "RIGHTSHADOWDASH", "FULLSHADOWDASH"]:
        return "PlayerData.instance.hasShadowDash"
    if x in ["LEFTSLASH", "RIGHTSLASH", "SIDESLASH"]:
        return True
    # ignore charm-gating
    if x.startswith("$LIFEBLOOD") or x in ["KINGSOUL", "VOIDHEART"]:
        return True
    if x in ["UPWALLBREAK"]:
        return True
    if x in ["Lit_Abyss_Lighthouse"]:
        return "PlayerData.instance.abyssLighthouse"
    if x in ["Defeated_Broken_Vessel"]:
        return "PlayerData.instance.killedInfectedKnight"
    if x in ["GREATSLASH"]:
        return "PlayerData.instance.hasNailArt"
    if x in ["CYCLONE"]:
        return "PlayerData.instance.hasCyclone"
    if x in ["LEFTDASHSLASH", "RIGHTDASHSLASH"]:
        return "PlayerData.instance.hasDashSlash"
    if x in ["FIREBALL"]:
        return "PlayerData.instance.fireballLevel > 0"
    if x in ["LEFTSHARPSHADOW", "RIGHTSHARPSHADOW"]:
        return "PlayerData.instance.equippedCharm_16"
    if x in ["WINGS"]:
        return "PlayerData.instance.hasDoubleJump"
    if x in ["Rescued_Sly"]:
        return "PlayerData.instance.slyRescued"
    if x in ["LANTERN"]:
        return "PlayerData.instance.hasLantern"
    if x in ["DARKROOMS"]:
        return False
    if x in ["JIJIUNLOCK"]:
        return "PlayerData.instance.jijiDoorUnlocked"
    if x in ["Rescued_Bretta"]:
        return "PlayerData.instance.brettaRescued"
    if x in ["Nightmare_Lantern_Lit"]:
        return "PlayerData.instance.nightmareLanternLit"
    if x in ["Defeated_Gruz_Mother"]:
        return "PlayerData.instance.killedBigFly"
    if x in ["Defeated_Brooding_Mawlek"]:
        return "PlayerData.instance.killedMawlek"
    if x in ["Defeated_Hornet_1"]:
        return "PlayerData.instance.hornet1Defeated"
    if x in ["Defeated_Hornet_2"]:
        return "PlayerData.instance.hornetOutskirtsDefeated"
    if x in ["Opened_Dung_Defender_Wall"]:
        return "PlayerData.instance.dungDefenderWallBroken"
    if x in ["Defeated_False_Knight"]:
        return "PlayerData.instance.killedFalseKnight"
    if x in ["Defeated_Ancestral_Mound_Baldur"]:
        return "PlayerData.instance.blocker1Defeated"
    if x in ["Defeated_Crossroads_Baldur"]:
        return "PlayerData.instance.blocker2Defeated"
    if x in ["Defeated_Right_Cliffs_Baldur"]:
        return "PlayerData.instance.defeatedDoubleBlockers"
    if x in ["Opened_Mawlek_Wall"]:
        return "PlayerData.instance.crossroadsMawlekWall"
    if x in ["Opened_Shaman_Pillar"]:
        return "PlayerData.instance.shamanPillar"
    if x in ["Upper_Tram", "Lower_Tram"]:
        return ("tram", x)
    if x in ["Left_Elevator"]:
        return "PlayerData.instance.cityLift1"
    if x in ["Right_Elevator"]:
        return "PlayerData.instance.cityLift2"
    if x in ["BRAND"]:
        return "PlayerData.instance.hasKingsBrand"
    if x in ["ELEGANT"]:
        return "PlayerData.instance.hasWhiteKey"
    if x in ["Lever-Dung_Defender"]:
        return "PlayerData.instance.waterwaysAcidDrained"
    if x in ["Defeated_Sanctum_Warrior"]:
        return "PlayerData.instance.killedMageKnight"
    if x in ["Broke_Sanctum_Glass_Floor"]:
        return "PlayerData.instance.brokenMageWindow"
    if x in ["Defeated_Soul_Master"]:
        return "PlayerData.instance.mageLordDefeated"
    if x in ["Defeated_Watcher_Knights"]:
        return "PlayerData.instance.killedBlackKnight"
    if x in ["Opened_Emilitia_Door"]:
        return "PlayerData.instance.city2_sewerDoor"
    if x in ["Opened_Pleasure_House_Wall"]:
        return "PlayerData.instance.bathHouseWall"
    if x in ["LOVE"]:
        return [
            "or",
            "PlayerData.instance.hasLoveKey",
            "PlayerData.instance.openedLoveDoor",
        ]
    if x in ["Broke_Crypts_One_Way_Floor"]:
        return "PlayerData.instance.restingGroundsCryptWall"
    if x in ["Opened_Resting_Grounds_Catacombs_Wall"]:
        return ("location", "RestingGrounds_10")
    if x in ["PLEASUREHOUSEUNLOCK"]:
        return "PlayerData.instance.bathHouseOpened"
    if x in ["Lever-City_Fountain"]:
        return ("transition", "Ruins1_27[right1]")
    # not sure if persistent
    if x in ["Defeated_West_Queen's_Gardens_Arena"]:
        return False
    if x in ["Opened_Gardens_Stag_Exit"]:
        return "PlayerData.instance.openedGardensStagStation"
    if x in ["Defeated_Traitor_Lord"]:
        return "PlayerData.instance.killedTraitorLord"
    if x in ["ALLSTAGS"]:
        return "PlayerData.instance.openedHiddenStation"
    if x in ["Defeated_Elegant_Warrior"]:
        return True
    if x in ["Grey_Mourner"]:
        return "PlayerData.instance.xunRewardGiven"
    if x in ["Lever-Shade_Soul"]:
        # the other condition seems complicated whatever
        return ("transition", "Ruins1_31b[right1]")
    # erm lets just ignore nonpersistent quakes
    if x in [
        "Broke_Lower_Edge_Quake_Floor",
        "Broke_Dung_Defender_Quake_Floor",
        "Broke_Waterways_Bench_Quake_Floor_3",
        "Broke_Flukemarm_Quake_Floor",
        "Broke_Waterways_Bench_Quake_Floor_1",
        "Broke_Waterways_Bench_Quake_Floor_2",
        "Broke_Quake_Floor_After_Soul_Master_1",
        "Broke_Quake_Floor_After_Soul_Master_2",
        "Broke_Quake_Floor_After_Soul_Master_3",
        "Broke_Quake_Floor_After_Soul_Master_4",
        "Broke_Resting_Grounds_Quake_Floor",
        "Broke_Crystal_Peak_Entrance_Quake_Floor",
        "Broke_Cliffs_Dark_Room_Quake_Floor",
    ]:
        return False
    if x in ["Opened_Lower_Kingdom's_Edge_Wall"]:
        return "PlayerData.instance.outskirtsWall"
    # not entirely sure but doesnt really matter
    if x in ["Palace_Entrance_Lantern_Lit"]:
        return "PlayerData.instance.whitePalaceOrb_1"
    if x in ["Palace_Right_Lantern_Lit"]:
        return "PlayerData.instance.whitePalaceOrb_2"
    if x in ["Palace_Left_Lantern_Lit"]:
        return "PlayerData.instance.whitePalaceOrb_3"
    if x in ["Palace_Atrium_Gates_Opened"]:
        return [
            "and",
            "PlayerData.instance.whitePalaceOrb_2",
            "PlayerData.instance.whitePalaceOrb_3",
        ]
    if x in ["Lever-Path_of_Pain"]:
        return [
            "and",
            ("transition", "White_Palace_17[bot1]"),
            "PlayerData.instance.hasDash",
            "PlayerData.instance.hasWalljump",
            "PlayerData.instance.hasDoubleJump",
        ]
    # probably post-boss warps
    if x.startswith("Warp-"):
        return False
    if x.startswith("COMBAT["):
        return True
    if x in ["Broke_Camp_Bench_Wall"]:
        return [
            "or",
            ("transition", "Deepnest_East_11[top1]"),
            [
                "and",
                ("transition", "Deepnest_East_11[right1]"),
                "PlayerData.instance.hasWalljump",
            ],
            [
                "and",
                [
                    "or",
                    ("transition", "Deepnest_East_11[left1]"),
                    ("transition", "Deepnest_East_11[bot1]"),
                ],
                "PlayerData.instance.hasDoubleJump",
                "PlayerData.instance.hasWalljump",
            ],
        ]
    if x in [
        "Broke_Oro_Quake_Floor_1",
        "Broke_Oro_Quake_Floor_2",
        "Broke_Oro_Quake_Floor_3",
    ]:
        return False  # nonpersistent
    if (
        x.endswith("SKIPS")
        or x
        in [
            "INFECTED",
            "DAMAGEBOOSTS",
            "ENEMYPOGOS",
            "SPELLAIRSTALL",
            "AIRSTALL",
            "SPIKETUNNELS",
            "DASHMASTER",
            "PRECISEMOVEMENT",
            "RIGHTSKIPACID",
            "LEFTSKIPACID",
            "FULLSKIPACID",
            "BACKGROUNDPOGOS",
            "$StartLocation[Hallownest's Crown]",
            "DASHSPRINT",
            "SPRINT",
        ]
        or x.startswith("$SHRIEKPOGO")
        or x.startswith("$CASTSPELL")
        or x.startswith("$SHADESKIP")
        or x.startswith("$TAKEDAMAGE")
        or x.startswith("$SLOPEBALL")
    ):
        return False
    if x in ["Opened_Archives_Exit_Wall"]:
        return "PlayerData.instance.oneWayArchive"
    if x in ["Defeated_Shrumal_Ogre_Arena"]:
        return "PlayerData.instance.notchShroomOgres"
    if x in ["Defeated_Mantis_Lords"]:
        return "PlayerData.instance.defeatedMantisLords"
    if x in ["Defeated_Dung_Defender"]:
        return "PlayerData.instance.defeatedDungDefender"
    if x in ["CREST"]:
        return [
            "and",
            "PlayerData.instance.openedCityGate",
            "not PlayerData.instance.cityGateClosed",
        ]
    if x in ["Opened_Waterways_Manhole"]:
        return "PlayerData.instance.openedWaterwaysManhole"
    if x in ["Opened_Waterways_Exit"]:
        return "PlayerData.instance.waterwaysGate"
    if x in ["Opened_Tramway_Exit_Gate"]:
        return "PlayerData.instance.deepnest26b_switch"
    if x in ["Opened_Glade_Door"]:
        return "PlayerData.instance.gladeDoorOpened"
    if x in ["Opened_Resting_Grounds_Floor"]:
        return [
            "or",
            [
                "and",
                [
                    "or",
                    ("transition", "RestingGrounds_06[left1]"),
                    ("transition", "RestingGrounds_06[right1]"),
                ],
                [
                    "or",
                    "PlayerData.instance.hasDash",
                    "PlayerData.instance.hasWallJump",
                    "PlayerData.instance.hasDoubleJump",
                ],
            ],
            ("transition", "RestingGrounds_06[top1]"),
        ]
    if x.startswith("Bench-") or x.endswith("_Hot_Spring"):
        return False
    if x == "Can_Stag":
        return True
    if x.endswith("_Stag"):
        return ("stag", x)
    if x in locNames:
        return ("location", x)
    if x in ["NONE"]:
        return True
    raise ValueError(x)


def parse(x: list[int | str]):
    stack = []
    ret = []
    i = False
    for t in x:
        if t == LPAREN:
            stack.append(ret)
            ret = []
            i = False
        elif t == RPAREN:
            ret0 = ret
            ret = stack.pop()
            i = True
            if not ret:
                ret.append(["and"])
            ret[-1].append(["or", *ret0])
        else:
            if i:
                assert t in [AND, OR]
                if t == AND:
                    pass
                elif t == OR:
                    ret.append(["and"])
            else:
                assert isinstance(t, str)
                resolved = resolve(t)
                if not ret:
                    ret.append(["and"])
                ret[-1].append(resolved)
            i = not i
    return ["or", *ret]


def peval(x, p=("",)):
    if isinstance(x, tuple):
        if x[0] == "location":
            return True
        if x[0] == p[0] and x[1] == p[1]:
            return True
        return False
    elif isinstance(x, list):
        ret = [x[0]]
        ignore = set()
        for y in x[1:]:
            y = peval(y, p)
            if str(y) in ignore:
                continue
            ignore.add(str(y))
            if x[0] == "or" and y == True:
                return True
            if x[0] == "and" and y == False:
                return False
            if x[0] == "or" and y == False:
                continue
            if x[0] == "and" and y == True:
                continue
            if isinstance(y, list) and y[0] == x[0]:
                for w in y[1:]:
                    if str(w) in ignore:
                        continue
                    ignore.add(str(w))
                    ret.append(w)
            else:
                ret.append(y)
        if len(ret) == 2:
            return ret[1]
        if len(ret) == 1:
            if x[0] == "or":
                return False
            if x[0] == "and":
                return True
        return ret
    else:
        assert x is not None
        return x


ans: dict = {"door": {}, "scene": {}}


def pprint(x, lastOp=None):
    if isinstance(x, str):
        return x
    elif isinstance(x, bool):
        return "true" if x else "false"
    elif isinstance(x, list):
        if x[0] == "and":
            ret = " && ".join(map(lambda x: pprint(x, "and"), x[1:]))
            return ret
        elif x[0] == "or":
            ret = " || ".join(map(lambda x: pprint(x, "or"), x[1:]))
            if lastOp == "and":
                return "(" + ret + ")"
            return ret
        else:
            raise ValueError(repr(x))
    else:
        raise ValueError(repr(x))


# refactor a condition by partially evaluating it for each found transportation method
def refactor(q, x, scene):
    global ans
    tr = []
    loc = []
    stag = []
    tram = []

    def tr_loc(x):
        nonlocal tr, loc
        if isinstance(x, tuple):
            if x[0] == "transition":
                tr.append(x[1])
            elif x[0] == "location":
                loc.append(x[1])
            elif x[0] == "stag":
                stag.append(x[1])
            elif x[0] == "tram":
                tram.append(x[1])
            else:
                raise ValueError(x[0])
        elif isinstance(x, list):
            for y in x[1:]:
                tr_loc(y)
        elif isinstance(x, str) or isinstance(x, bool):
            pass
        else:
            raise ValueError(repr(x))

    tr_loc(x)

    # now we can deduce transition accessibility from each part of the room
    # print(tr, loc, stag, tram)
    def assign(x, y, z, w, v):
        q = pprint(peval(w, v))
        if q == "false":
            return
        if y not in x.keys():
            x[y] = {}
        if z in x[y].keys():
            if x[y][z] == q:
                return
            print(x[y][z], q)
            raise ValueError(z)
        x[y][z] = q

    for w in tr:
        if w == q:
            continue
        # print(x, "=>", peval(x, ('transition', w)))
        if w not in ans["door"].keys():
            ans["door"][w] = {}
        assign(ans["door"], w, q, x, ("transition", w))
    for w in loc:
        if w not in ans["scene"].keys():
            ans["scene"][w] = {}
        assign(ans["scene"], w, q, x, ("location", w))
    for w in stag:
        assert len(stag) == 1
        if f"{scene}[door_stagExit]" not in ans["door"].keys():
            ans["door"][f"{scene}[door_stagExit]"] = {}
        assign(ans["door"], f"{scene}[door_stagExit]", q, x, ("stag", w))
    for w in tram:
        name = "door_tram_arrive" if w == "Lower_Tram" else "door_tram"
        if f"{scene}[{name}]" not in ans["door"].keys():
            ans["door"][f"{scene}[{name}]"] = {}
        assign(ans["door"], f"{scene}[{name}]", q, x, ("tram", w))


logic = namedtuple("Logic", _logic.keys())(**_logic)
data = namedtuple("Data", _data.keys())(**_data)
for tr in logic.transitions:
    locNames.add(tr["sceneName"])
    trNames[tr["Name"]] = tr

# print(data)
# print(parse(tokenize(logic.transitions[15]["logic"])))
trTypes = {}
for i, tr in enumerate(logic.transitions):
    # print()
    # print(tr["logic"])
    parsed = parse(tokenize(tr["logic"]))
    # print(f"{i}/{len(logic.transitions)}", parsed)
    refactor(tr["Name"], parsed, tr["sceneName"])
    # onewayin=can enter, cant exit from here
    # onewayout=can exit from here, cant enter
    trTypes[tr["Name"]] = tr["oneWayType"]

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


def goByName(m, n):
    for i in assetByName(m, n):
        r = resource(m, i)
        if "m_Component" in r.__d.keys():
            return r
    return None


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
    scenes = [
        {"name": x.split("/")[-1].split(".")[0], "trs": {}}
        for x in json.load(f)["scenes"]["Array"]
    ]
    sceneI = {x["name"]: i for i, x in enumerate(scenes)}

with open(assets / "resources.assets/19573 - World.json", "rt") as f:
    for scene in json.load(f)["Scenes"]["Array"]:
        k = sceneI[scene["SceneName"]]
        for v in scene["Transitions"]["Array"]:
            try:
                goByName(v["DestinationSceneName"], v["DestinationDoorName"]).m_Name
                goByName(k, v["DoorName"]).m_Name
            except KeyboardInterrupt:
                raise
            except:
                continue
            scenes[k]["trs"][v["DoorName"]] = {
                "scene": v["DestinationSceneName"],
                "door": v["DestinationDoorName"],
                "reachability": {"door": {}, "scene": {}},
            }
# print(scenes)
with open("o.json", "wt") as f:
    json.dump(ans, f, indent=" ", sort_keys=True)


for scene, v in ans["scene"].items():
    for targetDoor, cond in v.items():
        tds, td = parseDoor(targetDoor)
        sc = scenes[sceneI[tds]]
        # print(sc['trs'].keys())
        # print(scene, '->', targetDoor, ':', cond)
        if td not in sc["trs"].keys():
            # print('wrong1', tds, td)
            continue
        if scene != tds:
            # print('?', scene, '->', targetDoor)
            continue
        sc["trs"][td]["reachability"]["scene"][scene] = cond

for door, v in ans["door"].items():
    ds, d = parseDoor(door)
    for targetDoor, cond in v.items():
        tds, td = parseDoor(targetDoor)
        sc = scenes[sceneI[tds]]
        if td not in sc["trs"].keys():
            # print('wrong', tds, td)
            continue
        if ds != tds:
            # print('?', door, '->', targetDoor, cond)
            continue
        sc["trs"][td]["reachability"]["door"][d] = cond
        # print(door, '->', targetDoor, ':', cond)
# within room navi
# onewayin=can enter there but not go back
# onewayout=can exit from here but not go back
scMap = {}
trMap = {}
for sc in scenes:
    scN = sc["name"]
    for tn, tr in sc["trs"].items():
        # important: only mark transitions that were not marked as unreachable
        if (
            not tr["reachability"]["door"]
            and not tr["reachability"]["scene"]
            and trTypes.get(f"{scN}[{tn}]", None) != "OneWayOut"
        ):
            tr["reachability"]["scene"][scN] = "true"
        for k, v in tr["reachability"]["scene"].items():
            if k not in scMap.keys():
                scMap[k] = {}
            assert k == scN
            scMap[k][tn] = v
        for k, v in tr["reachability"]["door"].items():
            if scN not in trMap.keys():
                trMap[scN] = {}
            t = trMap[scN]
            if k not in t.keys():
                t[k] = {}
            t[k][tn] = v

# print("    let sceneIdx s =\n        match s with")
# for i, sc in enumerate(scenes):
#    print("        |", json.dumps(sc["name"]), "->", i)
# print("        | _ -> 0")
# print("    let sceneDoors s =\n        match s with")
# for k, v in scMap.items():
#    print(
#        "        |",
#        sceneI[k],
#        "->",
#        "[",
#        "; ".join(f"{json.dumps(q)}, {w}, {goPosS(k, q)}" for q, w in v.items()),
#        "]",
#    )
# print("        | _ -> []")
print("    let doorDoors s d = \n        match s, d with")
for sk, v in trMap.items():

    def dist(a, b):
        return ((a.x - b.x) ** 2 + (a.y - b.y) ** 2) ** 0.5

    def dire(a, b):
        angle = math.atan2(b.y - a.y, b.x - a.x)
        d = int(angle * (8.0 / math.pi) + 16.5) % 16
        return [
            "Dir.E",
            "Dir.Nee",
            "Dir.Ne",
            "Dir.Nne",
            "Dir.N",
            "Dir.Nnw",
            "Dir.Nw",
            "Dir.Nww",
            "Dir.W",
            "Dir.Sww",
            "Dir.Sw",
            "Dir.Ssw",
            "Dir.S",
            "Dir.Sse",
            "Dir.Se",
            "Dir.See",
        ][d]

    for dk, v in v.items():
        p0 = goPos(sk, dk)
        print(
            "        |",
            str(sceneI[sk]) + ",",
            json.dumps(dk),
            "->",
            "[",
            "; ".join(
                f"{json.dumps(q)}, {w}, {dist(p0, p)}, {dire(p0, p)}, {p.x}, {p.y}"
                for p, q, w in [(goPos(sk, q), q, w) for q, w in v.items()]
            ),
            "]",
        )
print("        | _ -> []")
for sc, d in allDoors:
    if sc in sceneI.keys():
        sc = scenes[sceneI[sc]]
        if d not in sc["trs"].keys():
            sc["trs"][d] = {}
# print("    let sceneDoorsAll s =\n        match s with")
# for i, sc in enumerate(scenes):
#   if sc["trs"]:
#       print(
#           "        |",
#           i,
#           "-> [|",
#           "; ".join(
#               f'{json.dumps(k[0])}, {k[1]}'
#               for k in [(k, goPosS(sc["name"], k)) for k in sc["trs"].keys()] if k[1]
#           ),
#           "|]",
#       )
# print("        | _ -> [||]")

am = {
    "areaDirtmouth": "mapDirtmouth",
    "areaCrossroads": "mapCrossroads",
    "areaGreenpath": "mapGreenpath",
    "areaFogCanyon": "mapFogCanyon",
    "areaQueensGardens": "mapRoyalGardens",
    "areaFungalWastes": "mapFungalWastes",
    "areaCity": "mapCity",
    "areaWaterways": "mapWaterways",
    "areaCrystalPeak": "mapMines",
    "areaDeepnest": "mapDeepnest",
    "areaCliffs": "mapCliffs",
    "areaKingdomsEdge": "mapOutskirts",
    "areaRestingGrounds": "mapRestingGrounds",
    "areaAncientBasin": "mapAbyss",
}
m = resource("resources.assets", 4791)
reachability = [None for i in range(len(scenes))]
for k in m.m_Component[1].component.__d.keys():
    if not k.startswith("area"):
        continue
    area = getattr(m.m_Component[1].component, k)
    for scene in area.m_Component[0].component.m_Children:
        go = scene.m_GameObject
        if "Name" in go.m_Name or go.m_Name == "Grub Pins":
            continue
        # print(go.m_Name)
        for c in go.m_Component[1:]:
            if "m_RenderingLayerMask" in c.component.__d.keys():
                continue
            # print(' ', c.component)
        # print(go.m_IsActive)
        n1 = go.m_Name
        if n1 not in sceneI.keys():
            n1 = n1[::-1].split("_", 1)[1][::-1]
        if n1 in sceneI.keys():
            reachability[sceneI[n1]] = (am[k], go.m_IsActive)
        # print('        |', sceneI[go.m_Name], '->', 'if', am[k], 'then', 'Always' if go.m_IsActive else 'Visited', 'else Never')
# print('    let reachability s =\n        match s with')
# for i, y in enumerate(scenes):
#    if y['name'].startswith('Room_') or y['name'].endswith('_room') or '_House_' in y['name']:
#        reachability[i] = (True, 'Passthru')
#    if y['name'] == 'Abyss_15':
#        reachability[i] = ('mapAbyss', False)
#    if y['name'] == 'Deepnest_East_17':
#        reachability[i] = ('mapOutskirts', False)
#    if y['name'] in ['Deepnest_45_v02', 'Deepnest_Spider_Town']:
#        reachability[i] = ('mapDeepnest', False)
#    if y['name'] == 'Mines_35':
#        reachability[i] = ('mapMines', False)
#    if y['name'] == 'RestingGrounds_07':
#        reachability[i] = ('mapRestingGrounds', False)
#    if y['name'] == 'Cliffs_03':
#        reachability[i] = ('mapCliffs', False)
#    if y['name'] in ['Fungus1_35', 'Fungus1_36']:
#        reachability[i] = ('mapGreenpath', False)
#    if reachability[i]:
#        a, b = reachability[i]
#        if a != True:
#            a = 'PlayerData.instance.' + a
#        if a == True:
#            print('        |', i, '-> Passthru')
#        else:
#            print('        |', i, '->', 'if', a, 'then', 'Always' if b else 'Visited', 'else Never')
# print('        | _ -> Never')
# print("    let sceneNames =\n        [|")
# for i, sc in enumerate(scenes):
#   print("       ", json.dumps(sc["name"]))
# print("        |]")

# print('    let doorTarget s d =\n        match s, d with')
# for i, sc in enumerate(scenes):
#    for k, v in sc['trs'].items():
#        if v['scene'] not in sceneI.keys():
#            continue
#        print('        |', str(i) + ',', json.dumps(k), '->', str(sceneI[v['scene']]) + ',', json.dumps(v['door']))
# print('        | _ -> 0, ""')

# for x in [329, 330, 331, 74, 75]:
#    p = goPos(x, 'Tram Call Box')
#    print(x, ',', p.x, ',', p.y)
# for x in [7, 9, 77, 107, 120, 145, 166, 220, 233, 244, 281, 346]:
#    p = goPos(x, "stag_station_front" if x == 7 else 'door_stagExit' if x in [9,346] else "stag_door")
#    print(x, p.x, ',', p.y)
# for x in [79, 80, 122, 123]:
#   p = goPos(x, 'elev_entrance')
#   print(x, ',', p.x, ',', p.y)
