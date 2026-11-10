# -*- coding: utf-8 -*-
"""Re-verify phrase content: endings, lessons, training, sheets, both directions."""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from ph_forms import self_check, parse_dict, noun_forms

html = (ROOT / "index.html").read_text(encoding="utf-8")
sw = (ROOT / "sw.js").read_text(encoding="utf-8")
errs = []

def err(msg):
    errs.append(msg)

bad = self_check()
if bad:
    err("FORM CHECK: " + "; ".join(bad))

m = re.search(r"const DP_POOL = (\{.*?\});\nconst DP_DATA = (\{.*?\});", html, re.S)
if not m:
    raise SystemExit("DP_POOL/DP_DATA missing")
pool = json.loads(m.group(1))
sec = json.loads(m.group(2))

# hydrate like JS
for d, U in sec.items():
    U["phrases"] = [pool[i] for i in U["pids"]]
    items_h = []
    for les in U["lessons"]:
        resolved = []
        for it in les["items"]:
            if it and it.get("p"):
                p = pool.get(it["p"])
                if not p:
                    err(f"d{d} {les['id']}: missing phrase {it['p']}")
                    continue
                # mimic dpPhItem enough to check steps
                rus0, lat0 = p["rus"].split("|")[0], p["lat"].split("|")[0]
                st = []
                if it.get("full") and it.get("dir") == "rl":
                    for t in p["tokens"]:
                        if t["slot"] in ("N", "G"):
                            opts = [t["form"]] + [x for x in (t.get("distr") or []) if x and x != t["form"]]
                            st.append({"k": "ch", "a": [t["form"]], "o": opts[:4] or [t["form"]]})
                st.append({"k": "ty", "dir": it.get("dir"), "alts": (p["lat"] if it.get("dir") == "rl" else p["rus"]).split("|"), "tokens": p["tokens"] if it.get("dir") == "rl" else None})
                resolved.append({"id": p["id"], "st": st, "lat": lat0, "rus": rus0})
            else:
                resolved.append(it)
        les["resolved"] = resolved

# required keys / hooks
for s in [
    "latAnat.v2", "latAnat.finalTest", "latAnat.krPrep", "latAnat.krLearn", "latAnat.lex2", "latAnat.phDecl",
    "function dpUnitBtns", "function startDp", "function dpSheet", "function dpDiagnose",
    'dpUnitBtns(1)', 'dpUnitBtns(2)', 'dpUnitBtns(3)', 'dpUnitBtns(4)', 'dpUnitBtns(5)',
    'get("ph")',
]:
    if s not in html:
        err("missing hook: " + s)
if 'const VERSION = "v12-phdecl-userlist-2026-11-10";' not in sw:
    err("sw.js VERSION not v12-phdecl-userlist-2026-11-10")

need = {
    "fractura costae": (1, "Nom. Sg.", "Gen. Sg."),
    "fractura costarum": (1, "Nom. Sg.", "Gen. Pl."),
    "fracturae costae": (1, "Nom. Pl.", "Gen. Sg."),
    "fracturae costarum": (1, "Nom. Pl.", "Gen. Pl."),
    "fractura vertebrae": (1, "Nom. Sg.", "Gen. Sg."),
    "rami nervorum": (2, "Nom. Pl.", "Gen. Pl."),
    "septum nasi": (2, "Nom. Sg.", "Gen. Sg."),
    "ligamenta scapularum": (2, "Nom. Pl.", "Gen. Pl."),
    "caput costae": (3, "Nom. Sg.", "Gen. Sg."),
    "arcus vertebrae": (4, None, "Gen. Sg."),
    "ostium ductus": (4, "Nom. Sg.", "Gen. Sg."),
    "arteria genus": (4, "Nom. Sg.", "Gen. Sg."),
    "facies ossis": (5, None, "Gen. Sg."),
    "facies ossium": (5, None, "Gen. Pl."),
}
by_lat = {p["lat"].split("|")[0]: p for p in pool.values()}
for lat, (decl, nfn, gfn) in need.items():
    p = by_lat.get(lat)
    if not p:
        err("missing key phrase " + lat)
        continue
    if str(decl) not in [str(x) for x in json.loads("null") or []]:
        pass
    # assigned to expected decl via pids
    if p["id"] not in sec[str(decl)]["pids"]:
        err(f"{lat} not assigned to decl {decl}")
    toks = [t for t in p["tokens"] if t["slot"] in ("N", "G")]
    if len(toks) < 2:
        err(lat + " expected 2+ noun tokens")
        continue
    if nfn and nfn not in toks[0]["fn"]:
        err(f"{lat} head fn {toks[0]['fn']} expected {nfn}")
    if gfn and gfn not in toks[1]["fn"]:
        err(f"{lat} dep fn {toks[1]['fn']} expected {gfn}")

# textbook endings spot-check
tb = [
    ("ala, ae f", "ala", "alae", "alae", "alarum"),
    ("costa, ae f", "costa", "costae", "costae", "costarum"),
    ("nervus, i m", "nervus", "nervi", "nervi", "nervorum"),
    ("tuberculum, i n", "tuberculum", "tuberculi", "tubercula", "tuberculorum"),
    ("caput, itis n", "caput", "capitis", "capita", "capitum"),
    ("os, ossis n", "os", "ossis", "ossa", "ossium"),
    ("ductus, us m", "ductus", "ductus", "ductus", "ductuum"),
    ("cornu, us n", "cornu", "cornus", "cornua", "cornuum"),
    ("genu, us n", "genu", "genus", "genua", "genuum"),
    ("manus, us f", "manus", "manus", "manus", "manuum"),
    ("facies, ei f", "facies", "faciei", "facies", "facierum"),
    ("arcus, us m", "arcus", "arcus", "arcus", "arcuum"),
    ("vas, vasis n", "vas", "vasis", "vasa", "vasorum"),
]
for d, ns, gs, np, gp in tb:
    f = noun_forms(parse_dict(d))
    if (f["ns"], f["gs"], f["np"], f["gp"]) != (ns, gs, np, gp):
        err(f"textbook ending {d}: {f} != {(ns,gs,np,gp)}")

# every lesson / training / sheet both directions
for d, U in sec.items():
    if not U["phrases"]:
        err(f"decl {d} has no phrases")
    if not U["lessons"]:
        err(f"decl {d} has no lessons")
    for les in U["lessons"]:
        if not les["resolved"]:
            err(f"d{d} {les['id']} empty")
        for it in les["resolved"]:
            if not it:
                err(f"d{d} {les['id']} null item")
                continue
            if it.get("th"):
                if not it.get("intro"):
                    err(f"d{d} {les['id']} empty intro")
                continue
            if it.get("st"):
                for s in it["st"]:
                    if s.get("k") == "ch":
                        if not s.get("a") or not s.get("o"):
                            err(f"d{d} {les['id']} bad choice")
                        elif not any(a in s["o"] for a in s["a"]):
                            err(f"d{d} {les['id']} answer not in options: {s['a']} {s['o']}")
                    if s.get("k") == "ty":
                        if not s.get("alts"):
                            err(f"d{d} {les['id']} typed without alts")
    # training: 8 RL + 6 LR possible
    ph = U["phrases"]
    n_rl, n_lr = min(8, len(ph)), min(6, len(ph))
    if n_rl < 1 or n_lr < 1:
        err(f"decl {d} cannot fill training")
    # sheet both directions: every phrase has lat and rus
    for p in ph:
        if not p.get("lat") or not p.get("rus"):
            err(f"decl {d} phrase missing lat/rus {p.get('id')}")
        # RL check would compare norm(lat); LR ruNorm(rus)
        if not p["tokens"]:
            err(f"decl {d} {p['lat']} no tokens (needed for RL diagnose)")

# theory first lessons exist
if not any(l["id"] == "d1-l1" for l in sec["1"]["lessons"]):
    err("missing d1-l1")
if "перелом позвонка" not in html or "fractura costae" not in html:
    err("first lesson prompt content missing")

# handwritten answers
expect_ch = {
    "d1-ae1": "Nom. Pl. («переломы»)",
    "d1-ae2": "Gen. Sg. («позвонка»)",
    "d1-why": "Рёбер несколько → Gen. Pl. на -arum",
    "d2-i1": "Nom. Pl. («ветви»)",
    "d2-why": "nervus — 2 скл.: Gen. Pl. -orum",
    "d2-n1": "Nom. Pl. среднего рода («связки»)",
    "d3-cap": "caput costae",
    "d3-ium": "dentium",
    "d3-um": "radicum",
    "d4-us": "Nom. Sg., Gen. Sg. или Nom. Pl.",
    "d5-ei": "faciei",
}
found = {}
for d, U in sec.items():
    for les in U["lessons"]:
        for it in les["items"]:
            if it and it.get("id") in expect_ch:
                found[it["id"]] = it.get("ans")
                if it.get("ans") != expect_ch[it["id"]]:
                    err(f"theory {it['id']} ans {it.get('ans')!r} != {expect_ch[it['id']]!r}")
missing = set(expect_ch) - set(found)
if missing:
    err("missing theory items " + ", ".join(sorted(missing)))


# user-list nouns must appear in matching declension phrases (aliases ok)
try:
    from ph_userlist import parse_minimum
    um = parse_minimum()
    alias = {"peritonaeum":{"peritoneum","peritonaeum"}, "caecum":{"caecum","cecum"}, "commissura":{"commissura","comissura"}}
    def used(decl, nom):
        wants = {re.sub(r"[^a-z0-9]+","", nom.lower())}
        for a in alias.get(nom.lower(), ()):
            wants.add(re.sub(r"[^a-z0-9]+","", a))
        for p in sec[str(decl)]["phrases"] if False else [pool[i] for i in sec[str(decl)]["pids"]]:
            for tok in p["tokens"]:
                if tok.get("slot") not in ("N","G"):
                    continue
                bag = {re.sub(r"[^a-z0-9]+","", (tok.get("head") or "")) , re.sub(r"[^a-z0-9]+","", (tok.get("dict") or "").split(",")[0])}
                bag.update(re.sub(r"[^a-z0-9]+","", f) for f in (tok.get("forms") or []))
                bag.add(re.sub(r"[^a-z0-9]+","", tok.get("form") or ""))
                if wants & bag:
                    return True
        return False
    for d, ents in um["nouns"].items():
        miss = [e["nom"] for e in ents if not used(d, e["nom"])]
        print(f"user-list coverage {d}: {len(ents)-len(miss)}/{len(ents)} missing={miss}")
        if miss:
            err("user nouns still missing in decl %s: %s" % (d, ", ".join(miss)))
except Exception as e:
    err("user-list coverage check failed: " + str(e))

if errs:
    print("VERIFY FAIL")
    print("\n".join(errs))
    raise SystemExit(1)
print("VERIFY OK")
print("pool", len(pool))
for d in "12345":
    U = sec[d]
    print(f"  {U['title']}: {len(U['phrases'])} фраз, {len(U['lessons'])} уроков, warnN={U['warnN']}")
    print(f"    training {min(8,len(U['phrases']))} RL + {min(6,len(U['phrases']))} LR; sheet {len(U['phrases'])} RL + {len(U['phrases'])} LR")
