import os, json
from pathlib import Path
o = Path('out')
for x in os.listdir(o):
    for y in os.listdir(o/x):
        if y.endswith('Area Title Controller.json'):
            print(x+'/'+y)
            with open(o/x/y, 'rt') as f:
                d = json.load(f)["fsm"]
            r = {}
            for (k, f) in [("string", str), ("int", int), ("bool", bool)]:
                for q in d["variables"][k + "Variables"]["Array"]:
                    r[q["name"]] = f(q["value"])
            print(r)

