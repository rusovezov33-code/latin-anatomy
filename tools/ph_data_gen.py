# -*- coding: utf-8 -*-
from __future__ import annotations
import json, re, sys
from pathlib import Path
from collections import defaultdict, OrderedDict

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from ph_forms import parse_dict, noun_forms, adj_forms, self_check
from ph_userlist import parse_minimum, COVERAGE_SPEC, COVERAGE_ADJ

HTML = (ROOT / "index.html").read_text(encoding="utf-8")

def nrm(s):
    s = s.lower().replace("ё", "е").replace("æ", "ae").replace("œ", "oe")
    return re.sub(r"\s+", " ", re.sub(r"[^a-zа-я0-9]+", " ", s)).strip()

def extract_js_array(src, name):
    m = re.search(rf"const {name} = (\[[\s\S]*?\]);", src)
    if not m:
        raise SystemExit("cannot find " + name)
    return json.loads(m.group(1))

UNITS = extract_js_array(HTML, "UNITS")
TEACHER_PHRASES = extract_js_array(HTML, "TEACHER_PHRASES")

LEX = {}
INDEX = defaultdict(list)

def add_noun(dict_form, rus="", src="game", warn="", prefer=False):
    meta = parse_dict(dict_form)
    if not meta or meta["kind"] != "noun":
        return None
    nom = meta["nom"]
    key = "|".join([nom.lower().replace("(", "").replace(")", ""), meta.get("gen", ""), meta.get("g", "")])
    forms = noun_forms(meta)
    meta = {**meta, "rus": rus, "src": src, "warn": warn, "forms": forms, "key": key}
    if prefer:
        for oldk in list(LEX):
            old = LEX[oldk]
            if oldk.startswith("adj:"):
                continue
            if old.get("nom", "").lower() != nom.lower():
                continue
            if nom.lower() == "os" and old.get("gen") != meta.get("gen"):
                continue
            del LEX[oldk]
        LEX[key] = meta
    elif key not in LEX or (not LEX[key].get("rus") and rus):
        LEX[key] = meta
    for fk in ("ns", "gs", "np", "gp"):
        INDEX[nrm(forms[fk])].append(key)
        alt = forms[fk].replace("ae", "e").replace("oe", "e")
        if alt != forms[fk]:
            INDEX[nrm(alt)].append(key)
    return meta

def add_adj(dict_form, rus=""):
    meta = parse_dict(dict_form)
    if not meta or meta["kind"] != "adj":
        return
    meta = {**meta, "rus": rus, "forms_set": adj_forms(meta)}
    key = "adj:" + meta["nom"].lower()
    LEX[key] = meta
    for f in meta["forms_set"]:
        INDEX[nrm(f)].append(key)

for u in UNITS:
    uid = u["id"]
    for rec in u["words"]:
        lat, rus = rec[0], rec[1]
        if uid == "u7" or "," not in lat:
            continue
        if uid in ("u5", "u6"):
            add_adj(lat, rus)
        else:
            add_noun(lat, rus, src="game")

add_noun("fractura, ae f", "перелом", src="prompt")
add_noun("ruptura, ae f", "разрыв", src="prompt")

def parse_teacher_line(line, default_src):
    line = re.sub(r"\s+", " ", line).strip()
    line = re.sub(r"^\d+\.\s*", "", line)
    if not line or "pelvis renalis" in line:
        return
    if re.match(r"m\.\s*\w+-", line) or line.startswith("musculus "):
        return
    line = line.replace("(=os coccygis)", "").replace("it s n", "itis n")
    rus = ""
    if "–" in line or "—" in line:
        latp, rus = re.split(r"[–—]", line, maxsplit=1)
        rus = rus.replace("-", " ").strip(" .")
    elif " -" in line:
        latp, rus = line.split(" -", 1)
        rus = rus.strip(" .")
    else:
        latp = line
    latp = latp.strip(" -")
    latp = re.sub(r",\s*", ", ", latp)
    latp = re.sub(r",(?=\S)", ", ", latp)
    warn = ""
    if latp.startswith("ungius"):
        latp = latp.replace("ungius", "unguis")
        warn = "у преподавателя опечатка «ungius»; верно unguis, is m"
    if "palatum" in latp and latp.rstrip().endswith("m") and not latp.rstrip().endswith("um, i n"):
        if re.search(r"palatum,\s*i\s*m", latp):
            warn = "у преподавателя palatum, i m; по пособию (с. 15) слова 2 скл. на -um — среднего рода (n)"
    add_noun(latp, rus, src=default_src, warn=warn)

for path, src in [
    (Path("/tmp/1 склонение - сущ.txt"), "teacher-1"),
    (Path("/tmp/2 склонение - сущ.txt"), "teacher-2"),
    (Path("/tmp/3 склонение - сущ.txt"), "teacher-3"),
]:
    if path.exists():
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            parse_teacher_line(line, src)

for extra, rus in [
    ("systema, atis n", "система"), ("diaphragma, atis n", "диафрагма"),
    ("mater, tris f", "мозговая оболочка"), ("rete, is n", "сеть"),
    ("olecranon, i n", "локтевой отросток"), ("acetabulum, i n", "вертлужная впадина"),
    ("folium, i n", "лист"), ("hallux, ucis m", "большой палец стопы"),
    ("appendix, icis f", "аппендикс, придаток"), ("tempus, oris n", "висок"),
    ("unguis, is m", "ноготь"), ("sanguis, inis m", "кровь"),
    ("porta, ae f", "ворота"),
    ("coxa, ae f", "таз, бедро"),
    ("ilium, i n", "подвздошная кость (ilium)"),
    ("ischium, i n", "седалищная кость (ischium)"),
    ("apex, icis m", "верхушка"),
    ("cavitas, atis f", "полость"),
    ("constrictor, oris m", "констриктор"),
    ("flexor, oris m", "сгибатель"),
    ("index, icis m", "указательный палец"),
    ("pollex, icis m", "большой палец кисти"),
    ("phalanx, ngis f", "фаланга"),
    ("pharynx, ngis m", "глотка"),
    ("thorax, acis m", "грудь, грудная клетка"),
    ("nodulus, i m", "узелок"),
    ("rotator, oris m", "ротатор"),
    ("sphincter, eris m", "сфинктер"),
    ("lumbus, i m", "поясница"),
    ("lumbi, orum m", "поясница (мн.)"),
]:
    nom0 = extra.split(",")[0].lower()
    if not any(k.startswith(nom0 + "|") or k == nom0 for k in LEX):
        add_noun(extra, rus, src="teacher-extra")

for extra, rus in [
    ("gluteus, a, um", "ягодичный"), ("glutaeus, a, um", "ягодичный"),
    ("durus, a, um", "твёрдый"), ("synovialis, e", "синовиальный"),
    ("horizontalis, e", "горизонтальный"), ("coronarius, a, um", "венечный"),
    ("abdominalis, e", "брюшной"),
    ("acusticus, a, um", "слуховой"),
    ("alveolaris, e", "альвеолярный"),
    ("asper, a, um", "шершавый"),
    ("cranialis, e", "черепной"),
    ("dexter, a, um", "правый"),
    ("sinister, a, um", "левый"),
    ("felleus, a, um", "жёлчный"),
    ("intestinalis, e", "кишечный"),
    ("latissimus, a, um", "широчайший"),
    ("liber, a, um", "свободный"),
    ("lingualis, e", "язычный"),
    ("longissimus, a, um", "длиннейший"),
    ("muscularis, e", "мышечный"),
    ("orbitalis, e", "глазничный"),
    ("radialis, e", "лучевой"),
    ("renalis, e", "почечный"),
    ("ruber, a, um", "красный"),
    ("sacer, a, um", "крестцовый"),
    ("sanguineus, a, um", "кровяной"),
    ("sternalis, e", "грудинный"),
    ("superior, ius", "верхний"),
    ("ulnaris, e", "локтевой"),
    ("vaginalis, e", "влагалищный"),
    ("vertebralis, e", "позвоночный"),
    ("pius, a, um", "мягкий (pia mater)"),
]:
    add_adj(extra, rus)

def add_adj_forms(nom, rus, forms, dict_form=""):
    key = "adj:" + nom.lower()
    LEX[key] = {"kind": "adj", "nom": nom, "rus": rus, "dict": dict_form or nom, "forms_set": set(forms)}
    for f in forms:
        INDEX[nrm(f)].append(key)

add_adj_forms("major", "большой", ["major", "majus", "majoris", "majores", "majora", "majorem", "maiorum", "majorum"], "major, majus")
add_adj_forms("minor", "малый", ["minor", "minus", "minoris", "minores", "minora", "minorem", "minorum"], "minor, minus")
add_adj_forms("teres", "круглый", ["teres", "teretis", "teretes", "teretium", "teretem", "tereti"], "teres, etis")

USER_MIN = parse_minimum()
USER_NOUNS = USER_MIN["nouns"]
add_adj("arachnoideus, a, um", "паутинный")
add_adj("renalis, e", "почечный")
# Prefer the teacher's lexical minimum (user list) over game wording,
# except where the textbook clearly contradicts it.
USER_WARN = {
    "palatum": "⚠ В минимуме «palatum, i m»; по пособию (с. 15) слова 2 скл. на -um — среднего рода (n). В словосочетаниях формы как у среднего рода; уточните у преподавателя.",
    "larynx": "⚠ В минимуме «larynx, yngis m»; в карточках игры это слово записано как ж. р. (f). Берём род из минимума (m).",
}
for d, ents in USER_NOUNS.items():
    for e in ents:
        lat, rus, warn = e["dict"], e["rus"], ""
        nom = e["nom"].lower()
        if nom == "palatum":
            lat, warn = "palatum, i n", USER_WARN["palatum"]
        elif nom == "larynx":
            lat, warn = "larynx, ngis m", USER_WARN["larynx"]
        add_noun(lat, rus, src="user-min", warn=warn, prefer=True)
# spelling doublets from the same minimum
if any(v.get("nom") == "peritonaeum" for v in LEX.values()):
    add_noun("peritoneum, i n", "брюшина", src="user-min")
if any(v.get("nom") == "caecum" for v in LEX.values()):
    add_noun("cecum, i n", "слепая кишка", src="user-min")

def lookup_token(tok, prefer_gen=False):
    keys = [k for k in INDEX.get(nrm(tok), []) if k in LEX]
    if not keys:
        return None
    nt = nrm(tok)
    def score(k):
        ent = LEX[k]
        noun = 0 if k.startswith("adj:") else 1
        f = ent.get("forms") or {}
        if prefer_gen:
            match = 2 if nt in (nrm(f.get("gs", "")), nrm(f.get("gp", ""))) else (1 if nt in (nrm(f.get("ns", "")), nrm(f.get("np", ""))) else 0)
        else:
            match = 2 if nt in (nrm(f.get("ns", "")), nrm(f.get("np", ""))) else (1 if nt in (nrm(f.get("gs", "")), nrm(f.get("gp", ""))) else 0)
        bone = 1 if ent.get("nom") == "os" and f.get("gs") == "ossis" and nt == "os" else 0
        return (noun, match, bone, len(ent.get("nom", "")))
    keys = sorted(set(keys), key=score, reverse=True)
    return LEX[keys[0]]

def analyze(lat):
    lat0 = lat.split("|")[0].strip()
    raw_toks = [x for x in re.split(r"\s+", lat0) if x and x not in ("et", "vel")]
    tokens, nouns, unmatched = [], [], []
    first_noun = True
    for raw in raw_toks:
        tok = raw.strip(" ,;:")
        ent = lookup_token(tok, prefer_gen=not first_noun)
        if not ent:
            unmatched.append(tok)
            tokens.append({"form": tok, "dict": tok, "rus": "", "d": "?", "g": "?", "slot": "A", "fn": "слово из термина преподавателя", "end": "—", "head": tok, "distr": [], "forms": []})
            continue
        if ent.get("kind") == "adj":
            tokens.append({"form": tok, "dict": ent["dict"], "rus": ent.get("rus") or "", "d": "прил.", "g": "", "slot": "A", "fn": "согласованное определение", "end": "—", "head": ent["nom"], "distr": [], "forms": []})
            continue
        f = ent["forms"]
        slot = "N" if first_noun else "G"
        first_noun = False
        fns, ends = [], []
        nt = nrm(tok)
        if slot == "N":
            if nt == nrm(f["ns"]):
                fns.append("Nom. Sg."); ends.append(f["end"]["ns"])
            if nt == nrm(f["np"]):
                fns.append("Nom. Pl."); ends.append(f["end"]["np"])
        else:
            if nt == nrm(f["gs"]):
                fns.append("Gen. Sg."); ends.append(f["end"]["gs"])
            if nt == nrm(f["gp"]):
                fns.append("Gen. Pl."); ends.append(f["end"]["gp"])
        if not fns:
            fns, ends = ["форма"], ["—"]
        ufn, uend = [], []
        for a, b in zip(fns, ends):
            if a not in ufn:
                ufn.append(a); uend.append(b)
        dform = ent.get("dict") or (ent["nom"] + ", " + ent.get("gen", "") + " " + ent.get("g", ""))
        tokens.append({
            "form": tok, "dict": dform, "rus": ent.get("rus") or "", "d": ent["d"], "g": ent["g"],
            "slot": slot, "fn": " или ".join(ufn), "end": " / ".join(uend), "head": ent["nom"],
            "distr": [f[k] for k in ("ns", "gs", "np", "gp") if f[k] != tok][:3],
            "forms": [f[k] for k in ("ns", "gs", "np", "gp")],
        })
        nouns.append(ent)
    decls = sorted({n["d"] for n in nouns if isinstance(n.get("d"), int)})
    return {"tokens": tokens, "decls": decls, "unmatched": unmatched, "nouns": nouns}

POOL = OrderedDict()

def add_phrase(lat, rus, src, warn=""):
    lat, rus = lat.strip(), rus.strip()
    if not lat or not rus:
        return
    key = nrm(lat.split("|")[0])
    info = analyze(lat)
    rec = {"id": src + "-" + str(len(POOL)), "lat": lat, "rus": rus, "warn": warn, "src": src,
           "tokens": info["tokens"], "decls": info["decls"], "unmatched": info["unmatched"]}
    if key in POOL:
        old = POOL[key]
        al = []
        for x in (old["rus"].split("|") + rus.split("|")):
            if x and x not in al:
                al.append(x)
        old["rus"] = "|".join(al)
        if warn and not old["warn"]:
            old["warn"] = warn
        return
    POOL[key] = rec

for lat, rus in [
    ("fractura costae", "перелом ребра|перелом одного ребра"),
    ("fractura costarum", "перелом рёбер|перелом нескольких рёбер"),
    ("fracturae costae", "переломы ребра"),
    ("fracturae costarum", "переломы рёбер|переломы нескольких рёбер"),
    ("fractura vertebrae", "перелом позвонка"),
    ("fracturae vertebrarum", "переломы позвонков"),
    ("papilla linguae", "сосочек языка"),
    ("papillae linguae", "сосочки языка"),
    ("glandulae buccae", "железы щеки"),
    ("glandulae linguae", "железы языка"),
    ("ruptura gingivae", "разрыв десны"),
    ("rupturae arteriarum", "разрывы артерий"),
]:
    add_phrase(lat, rus, "prompt")

for row in [
    ("ветвь нерва", "ramus nervi", ""),
    ("ямка черепа", "fossa cranii", ""),
    ("ствол головного мозга", "truncus encephali|truncus cerebri", "⚠ «головной мозг» у преподавателя — encephalon; засчитывается и truncus cerebri"),
    ("вырезка грудины", "incisura sterni", ""),
    ("связка матки", "ligamentum uteri", ""),
    ("связка надколенника", "ligamentum patellae", ""),
    ("борозда языка", "sulcus linguae", ""),
    ("нерв плеча", "nervus brachii", ""),
    ("ветви нервов", "rami nervorum", ""),
    ("связки лопаток", "ligamenta scapularum", ""),
    ("нервы плеч", "nervi brachiorum", ""),
    ("сумки мышц", "bursae musculorum", ""),
    ("складки прямой кишки", "plicae recti", ""),
    ("губы матки", "labia uteri", ""),
    ("луковицы вен", "bulbi venarum", ""),
    ("скелет конечностей", "skeleton membrorum", ""),
    ("шейка ребра", "collum costae", ""),
    ("перегородка носа", "septum nasi", ""),
    ("устье трубы", "ostium tubae", ""),
    ("оболочка пищевода", "tunica oesophagi", ""),
    ("изгиб прямой кишки", "flexura recti", ""),
    ("рукоятка грудины", "manubrium sterni", ""),
    ("щель связки", "fissura ligamenti", ""),
    ("вены большого мозга", "venae cerebri", ""),
    ("удерживатели мышц", "retinacula musculorum", ""),
    ("бугорки плечевых костей", "tubercula humerorum", ""),
    ("влагалища пальцев", "vaginae digitorum", ""),
    ("артерии головного мозга", "arteriae encephali|arteriae cerebri", ""),
    ("мышцы нёба", "musculi palati", ""),
    ("устья вен", "ostia venarum", ""),
    ("артерии щёк", "arteriae buccarum", ""),
]:
    add_phrase(row[1], row[0], "teacher32", row[2])

for rus, lat in TEACHER_PHRASES:
    add_phrase(lat, rus, "teacher312")

for lat, rus in [
    ("arcus vertebrae", "дуга позвонка"),
    ("arcus vertebrarum", "дуги позвонков"),
    ("arteria genus", "коленная артерия|артерия колена"),
    ("caput costae", "головка ребра"),
    ("articulatio genus", "сустав колена"),
    ("articulationes genuum", "суставы коленей"),
    ("digitus manus", "палец руки|палец кисти"),
    ("digiti manuum", "пальцы рук|пальцы кистей"),
    ("facies ossis", "поверхность кости"),
    ("facies ossium", "поверхности костей"),
    ("cornu ventriculi", "рог желудочка"),
    ("cornua ventriculorum", "рога желудочков"),
    ("ostium ductus", "устье протока"),
    ("ostia ductuum", "устья протоков"),
    ("sulcus sinus", "борозда пазухи"),
    ("sulci sinuum", "борозды пазух"),
    ("tendo manus", "сухожилие руки|сухожилие кисти"),
    ("tendines manuum", "сухожилия рук|сухожилия кистей"),
    ("bulbus cornus", "луковица рога"),
    ("bulbi cornuum", "луковицы рогов"),
    ("crista capitis costae", "гребень головки ребра"),
    ("medulla ossium", "костный мозг"),
    ("medulla spinalis", "спинной мозг"),
    ("vena portae", "воротная вена"),
    ("atrium cordis", "предсердие"),
    ("bulbus oculi", "глазное яблоко"),
    ("articulatio coxae", "тазобедренный сустав"),
    ("os coxae", "тазовая кость"),
    ("os ischii", "седалищная кость"),
    ("os ilii", "подвздошная кость"),
]:
    add_phrase(lat, rus, "textbook")

for sp in USER_MIN["set_phrases"]:
    add_phrase(sp["lat"], sp["rus"], "usermin")

def lex_named(alias):
    alias = alias.lower()
    if alias == "os_ossis":
        for v in LEX.values():
            if v.get("nom") == "os" and (v.get("forms") or {}).get("gs") == "ossis":
                return v
        return None
    if alias == "os_oris":
        for v in LEX.values():
            if v.get("nom") == "os" and (v.get("forms") or {}).get("gs") == "oris":
                return v
        return None
    alts = {
        "peritoneum": ("peritoneum", "peritonaeum"),
        "caecum": ("caecum", "cecum"),
        "commissura": ("commissura", "comissura"),
    }.get(alias, (alias,))
    for v in LEX.values():
        if v.get("nom", "").lower() in alts:
            return v
    return None

def form_of(alias, slot):
    ent = lex_named(alias)
    if not ent:
        raise SystemExit("coverage: unknown noun " + alias)
    return ent["forms"][slot]

coverage_added = []
for a, sa, b, sb, rus, warn in COVERAGE_SPEC:
    lat = form_of(a, sa) + " " + form_of(b, sb)
    alts = [lat]
    if "peritonei" in lat:
        alts.append(lat.replace("peritonei", "peritonaei"))
    if "caeci" in lat:
        alts.append(lat.replace("caeci", "ceci"))
    add_phrase("|".join(dict.fromkeys(alts)), rus, "pattern", warn)
    coverage_added.append(lat)

for a, sa, adj, rus, warn in COVERAGE_ADJ:
    lat = form_of(a, sa) + " " + adj
    add_phrase(lat, rus, "usermin", warn)
    coverage_added.append(lat)

for p in POOL.values():
    if p.get("warn"):
        continue
    for tok in p["tokens"]:
        head = (tok.get("head") or (tok.get("dict") or "").split(",")[0]).lower()
        for v in LEX.values():
            if v.get("nom", "").lower() == head and v.get("warn"):
                p["warn"] = v["warn"]
                break
        if p.get("warn"):
            break

by_decl = {1: [], 2: [], 3: [], 4: [], 5: []}
unmatched_ph = []
for p in POOL.values():
    if not p["decls"]:
        unmatched_ph.append(p)
    for d in p["decls"]:
        if d in by_decl:
            by_decl[d].append(p)

def th(iid, html):
    return {"id": iid, "th": True, "intro": html, "st": []}

def ch_item(iid, q, a, opts, h=""):
    o = []
    for x in [a] + list(opts):
        if x not in o:
            o.append(x)
    return {"id": iid, "ans": a, "parse": "", "st": [{"k": "ch", "q": q, "a": [a], "o": o[:4], "h": h, "lat": False}]}

def phrase_item_full(p, dir_, full=True):
    if not p:
        return None
    st = []
    rus0 = p["rus"].split("|")[0]
    lat0 = p["lat"].split("|")[0]
    if full and dir_ == "rl":
        for t in p["tokens"]:
            if t["slot"] not in ("N", "G"):
                continue
            opts = [t["form"]] + [x for x in (t.get("distr") or []) if x and x != t["form"]]
            st.append({"k": "ch", "q": "«" + rus0 + "» — " + ("главное слово («что?»)" if t["slot"] == "N" else "зависимое («чего?»)") + ", " + t["dict"], "a": [t["form"]], "o": (opts[:4] or [t["form"]]), "h": t["fn"] + ", окончание " + t["end"], "lat": True})
    if full and dir_ == "lr":
        for t in [x for x in p["tokens"] if x["slot"] in ("N", "G")][:2]:
            opts = [t["fn"].split(" или ")[0]] + [x for x in ("Nom. Sg.", "Gen. Sg.", "Nom. Pl.", "Gen. Pl.") if x != t["fn"].split(" или ")[0]]
            st.append({"k": "ch", "q": "<span class=\"lat\">" + lat0 + "</span> — <span class=\"lat\">" + t["form"] + "</span>: какая форма?", "a": [t["fn"].split(" или ")[0]], "o": opts[:4], "h": ("Первое слово — «что?»" if t["slot"] == "N" else "Второе слово — «чего?»") + " (" + t["rus"] + ")"})
    if dir_ == "rl":
        st.append({"k": "ty", "q": "<div class=\"prompt\"><b style=\"font-size:1.35rem\">" + rus0 + "</b></div><div class=\"hint\" style=\"text-align:center\">Переведите на латынь</div>", "a": lat0, "alts": p["lat"].split("|"), "lat": True, "h": p["warn"], "tokens": p["tokens"]})
        ans = rus0 + " — <span class=\"lat\">" + lat0 + "</span>"
    else:
        st.append({"k": "ty", "q": "<div class=\"prompt\"><span class=\"lat big\">" + lat0 + "</span></div><div class=\"hint\" style=\"text-align:center\">Переведите на русский</div>", "a": rus0, "alts": p["rus"].split("|"), "lat": False, "h": ""})
        ans = "<span class=\"lat\">" + lat0 + "</span> — " + rus0
    parse = "".join("<div>" + str(j + 1) + ") <b class=\"lat\">" + t["form"] + "</b> ← " + t["dict"] + " (" + t["rus"] + ") — " + str(t["d"]) + " скл., " + t["fn"] + ", окончание <b>" + t["end"] + "</b></div>" for j, t in enumerate(p["tokens"]))
    return {"id": p["id"] + "-" + dir_, "ans": ans, "parse": parse, "st": st}

def phrase_item(p, dir_, full=True):
    if not p:
        return None
    return {"p": p["id"], "dir": dir_, "full": bool(full)}

def find_ph(*needles):
    for p in POOL.values():
        blob = (p["lat"] + " " + p["rus"]).lower()
        if all(n.lower() in blob for n in needles):
            return p
    return None

def chunked(decl, phrases, size=7, label="Фразы преподавателя", tag="p"):
    lessons = []
    nn = [p for p in phrases if not any(t["slot"] == "A" for t in p["tokens"])]
    rest = [p for p in phrases if p not in nn]
    ordered = nn + rest
    parts = [ordered[i:i + size] for i in range(0, len(ordered), size)]
    if parts and len(parts[-1]) < 3 and len(parts) > 1:
        parts[-2].extend(parts.pop())
    for i, part in enumerate(parts):
        items = [th("d%d-%s%dt" % (decl, tag, i), "<span class=\"badge\">%s · часть %d</span><div class=\"kl-th\"><p>Разберите каждое: главное слово — «что?» (Nom.), зависимое — «чего?» (Gen.). Число у каждого слова своё. Сначала выбор формы, потом напишите словосочетание целиком.</p></div>" % (label, i + 1))]
        for p in part:
            it = phrase_item(p, "rl", True)
            if it:
                items.append(it)
        lessons.append({"id": "d%d-%s%d" % (decl, tag, i), "title": "%s (%d)" % (label, i + 1), "items": items})
    return lessons

HINT = {
    1: "Первое существительное — в <b>Nom.</b> («что?»), второе — в <b>Gen.</b> («чего?»). У 1 скл. Gen. Sg. <b>-ae</b>, Gen. Pl. <b>-arum</b> (пособие, с. 12). Окончание <b>-ae</b> бывает и Gen. Sg., и Nom. Pl. — смотрите место слова. Слова и словосочетания — из материалов преподавателя и пособия Провоторовой. Знак ⚠ — уточните у преподавателя.",
    2: "То же правило: Nom. + Gen. Во 2 скл. Gen. Sg. <b>-i</b>, Gen. Pl. <b>-orum</b> (с. 15). Мужской род: Nom. Pl. <b>-i</b>; средний: Nom. Pl. <b>-a</b>. Окончание <b>-i</b> бывает и Gen. Sg., и Nom. Pl. — как <b>-ae</b> в 1 скл.",
    3: "Признак 3 скл. — Gen. Sg. на <b>-is</b> (с. 41). Основу берут из Gen. Sg.: corpus, corporis → corpor-. Gen. Pl. <b>-um</b> или <b>-ium</b> (с. 42–44). Словарную форму учите целиком.",
    4: "Признак 4 скл. — Gen. Sg. на <b>-us</b> (с. 53). У мужского рода совпадают Nom. Sg., Gen. Sg. и Nom. Pl. (все на <b>-us</b>). Gen. Pl. <b>-uum</b>. Средний род: Nom. Sg. <b>-u</b>, Nom. Pl. <b>-ua</b>.",
    5: "Признак 5 скл. — Gen. Sg. на <b>-ei</b> (с. 53). В анатомии почти всегда <span class=\"lat\">facies, ei f</span>. Nom. Sg. и Nom. Pl. совпадают (<b>-es</b>). Gen. Pl. <b>-erum</b>.",
}

def lessons_for(decl, phrases):
    L = []
    if decl == 1:
        L.append({"id": "d1-l1", "title": "Правило и разбор", "items": [
            th("d1-l1t", """<span class="badge">Правило · пособие с. 11–12</span>
<div class="kl-th"><p>В словосочетании из двух существительных первое отвечает на вопрос <b>что?</b> и стоит в <b>именительном падеже (Nom.)</b>. От него задаём вопрос <b>чего?</b> — второе слово стоит в <b>родительном (Gen.)</b>.</p>
<p>Число у каждого слова своё: смотрите русский текст отдельно для каждого слова.</p></div>
<span class="badge">Разбор: fractura costae — перелом ребра</span>
<div class="kl-parse">
<div>1) Главное слово — <span class="lat">fractura</span>: что? Один перелом → <b>Nom. Sg.</b></div>
<div>2) От него вопрос «чего?» — второе слово в Gen.</div>
<div>3) Число второго слова отдельно: одного ребра, не нескольких.</div>
<div>4) Словарь: <span class="lat">fractura, ae f</span> → Nom. Sg. на <b>-a</b>: <b class="lat">fractura</b>. <span class="lat">costa, ae f</span> → Gen. Sg. на <b>-ae</b>: <b class="lat">costae</b>.</div>
<div>Ответ: <b class="lat">fractura costae</b>.</div></div>"""),
            phrase_item(find_ph("fractura vertebrae"), "rl", True),
        ]})
        L.append({"id": "d1-l2", "title": "Четыре комбинации и -ae", "items": [
            th("d1-l2t", """<span class="badge">Число каждого слова · ловушка -ae</span>
<div class="kl-th"><p>Меняется только число — слова те же:</p>
<p><span class="lat">fractura costae</span> — один перелом, одного ребра<br>
<span class="lat">fractura costarum</span> — один перелом, нескольких рёбер<br>
<span class="lat">fracturae costae</span> — несколько переломов, одного ребра<br>
<span class="lat">fracturae costarum</span> — несколько переломов, нескольких рёбер</p>
<p>Окончание <b>-ae</b> бывает двум вещам: <b>Gen. Sg.</b> (чего? одного) и <b>Nom. Pl.</b> (что? несколько). Место слова подсказывает смысл: первое — «что?», второе — «чего?».</p>
<table class="kl-t"><tr><th></th><th>ед. ч.</th><th>мн. ч.</th></tr><tr><th>Nom. (что?)</th><td>-a</td><td>-ae</td></tr><tr><th>Gen. (чего?)</th><td>-ae</td><td>-arum</td></tr></table></div>"""),
            ch_item("d1-ae1", "В <span class=\"lat\">fracturae vertebrarum</span> окончание <span class=\"lat\">-ae</span> у первого слова — это…", "Nom. Pl. («переломы»)", ["Gen. Sg. («перелома»)", "Gen. Pl.", "Nom. Sg."], "Первое слово — «что?». Несколько переломов → Nom. Pl."),
            ch_item("d1-ae2", "В <span class=\"lat\">fractura vertebrae</span> слово <span class=\"lat\">vertebrae</span> — это…", "Gen. Sg. («позвонка»)", ["Nom. Pl. («позвонки»)", "Gen. Pl.", "Nom. Sg."], "Второе слово — «чего?». Позвонок один → Gen. Sg. на -ae."),
            ch_item("d1-why", "Почему «перелом рёбер» — <span class=\"lat\">fractura costarum</span>, а не <span class=\"lat\">fractura costae</span>?", "Рёбер несколько → Gen. Pl. на -arum", ["costa — слово 2 склонения", "После fractura всегда идёт -arum", "costarum — это Nom. Pl."], "Второе слово отвечает на «чего?» → Gen. Рёбер много → Gen. Pl. -arum."),
            phrase_item(find_ph("fractura costarum"), "rl", True),
            phrase_item(find_ph("fracturae costarum"), "rl", True),
        ]})
        L.append({"id": "d1-l3", "title": "Знакомые слова", "items": [
            th("d1-l3t", """<span class="badge">Ещё примеры из знакомых слов</span>
<div class="kl-th"><p>Тот же разбор: что? / чего? и число каждого слова.</p>
<p><span class="lat">papilla linguae</span> — сосочек языка. Дальше: «сосочки языка», «железы щеки», «железы языка».</p></div>"""),
            phrase_item(find_ph("papillae linguae"), "rl", True),
            phrase_item(find_ph("glandulae buccae"), "rl", True),
            phrase_item(find_ph("glandulae linguae"), "rl", True),
            phrase_item(find_ph("ruptura gingivae"), "rl", True),
        ]})
    elif decl == 2:
        L.append({"id": "d2-l1", "title": "Правило и 2 скл.", "items": [
            th("d2-l1t", """<span class="badge">2 склонение · пособие с. 15</span>
<div class="kl-th"><p>Правило то же: первое слово — <b>что?</b> (Nom.), второе — <b>чего?</b> (Gen.).</p>
<p>Признак 2 скл. — Gen. Sg. на <b>-i</b>. Мужской род в Nom. Sg. на <b>-us</b>, средний на <b>-um</b> или <b>-on</b>.</p>
<table class="kl-t"><tr><th></th><th>Nom. Sg.</th><th>Gen. Sg.</th><th>Nom. Pl.</th><th>Gen. Pl.</th></tr>
<tr><th>m</th><td>-us</td><td>-i</td><td>-i</td><td>-orum</td></tr>
<tr><th>n</th><td>-um, -on</td><td>-i</td><td>-a</td><td>-orum</td></tr></table>
<p>Ловушка как с <b>-ae</b>: <span class="lat">nervi</span> — и «нерва» (Gen. Sg.), и «нервы» (Nom. Pl.).</p></div>
<span class="badge">Разбор: ramus nervi — ветвь нерва</span>
<div class="kl-parse">
<div>1) <span class="lat">ramus, i m</span>: что? Одна ветвь → Nom. Sg. <b class="lat">ramus</b></div>
<div>2) «Чего?» — нерва, одного → Gen. Sg. от <span class="lat">nervus, i m</span> на <b>-i</b>: <b class="lat">nervi</b></div>
<div>Несколько ветвей нескольких нервов — <span class="lat">rami nervorum</span>.</div></div>"""),
            ch_item("d2-i1", "В <span class=\"lat\">rami nervorum</span> слово <span class=\"lat\">rami</span> — это…", "Nom. Pl. («ветви»)", ["Gen. Sg.", "Gen. Pl.", "Nom. Sg."], "Первое слово — «что?». Несколько ветвей → Nom. Pl. на -i."),
            ch_item("d2-why", "Почему <span class=\"lat\">rami nervorum</span>, а не <span class=\"lat\">rami nervarum</span>?", "nervus — 2 скл.: Gen. Pl. -orum", ["-arum бывает только у ветвей", "nervorum — это Nom. Pl.", "Так звучит лучше"], "-arum — у 1 скл.; nervus, i m — 2 скл. → -orum."),
            phrase_item(find_ph("rami nervorum"), "rl", True),
        ]})
        L.append({"id": "d2-l2", "title": "Средний род: -um → -a", "items": [
            th("d2-l2t", """<span class="badge">Средний род 2 скл. · с. 15–16</span>
<div class="kl-th"><p>В Nom. Pl. средний род получает <b>-a</b>, не <b>-i</b>: <span class="lat">ligamentum</span> → <span class="lat">ligamenta</span>. Не путайте это <b>-a</b> с Nom. Sg. 1 склонения.</p>
<p>Греческие слова на <b>-on</b> (<span class="lat">encephalon, ganglion, skeleton, colon</span>) склоняются так же: Gen. Sg. <b>-i</b>.</p></div>
<span class="badge">Разбор: septum nasi — перегородка носа</span>
<div class="kl-parse">
<div>1) <span class="lat">septum, i n</span> — что? → Nom. Sg. <b class="lat">septum</b></div>
<div>2) <span class="lat">nasus, i m</span> — чего? одного носа → Gen. Sg. <b class="lat">nasi</b></div></div>"""),
            ch_item("d2-n1", "<span class=\"lat\">ligamenta scapularum</span> — что такое <span class=\"lat\">ligamenta</span>?", "Nom. Pl. среднего рода («связки»)", ["Nom. Sg. 1 склонения", "Gen. Sg.", "Gen. Pl."], "ligamentum → ligamenta: средний род 2 скл. во мн. ч. на -a."),
            phrase_item(find_ph("septum nasi"), "rl", True),
            phrase_item(find_ph("ligamenta scapularum"), "rl", True),
        ]})
    elif decl == 3:
        L.append({"id": "d3-l1", "title": "Основа и Gen. на -is", "items": [
            th("d3-l1t", """<span class="badge">3 склонение · пособие с. 41–44</span>
<div class="kl-th"><p>Признак — Gen. Sg. на <b>-is</b>. Основу берут из Gen. Sg., отбросив <b>-is</b>: <span class="lat">corpus, corporis n</span> → основа <b>corpor-</b>. Словарную форму учат целиком.</p>
<table class="kl-t"><tr><th></th><th>Nom. Sg.</th><th>Gen. Sg.</th><th>Nom. Pl.</th><th>Gen. Pl.</th></tr>
<tr><th>m, f</th><td>разные</td><td>-is</td><td>-es</td><td>-um / -ium</td></tr>
<tr><th>n</th><td>разные</td><td>-is</td><td>-a / -ia</td><td>-um / -ium</td></tr></table></div>
<span class="badge">Разбор: caput costae — головка ребра</span>
<div class="kl-parse">
<div>1) <span class="lat">caput, itis n</span> — что? Одна головка → Nom. Sg. <b class="lat">caput</b></div>
<div>2) <span class="lat">costa, ae f</span> — чего? Одного ребра → Gen. Sg. <b class="lat">costae</b></div>
<div>Не <span class="lat">caput costarum</span>: -arum значит «рёбер». Это разбор ошибки из пособия (с. 13).</div></div>"""),
            ch_item("d3-cap", "«Головка ребра» — как правильно?", "caput costae", ["caput costarum", "caput costa", "capitis costae"], "Ребро одно → Gen. Sg. costae."),
            phrase_item(find_ph("caput costae"), "rl", True),
            phrase_item(find_ph("crista capitis costae"), "rl", True),
        ]})
        L.append({"id": "d3-l2", "title": "Gen. Pl.: -um или -ium", "items": [
            th("d3-l2t", """<span class="badge">Gen. Pl. 3 скл. · с. 42–44</span>
<div class="kl-th"><p><b>Согласный тип → -um</b>: основа на одну согласную — <span class="lat">radix → radicum</span>, <span class="lat">margo → marginum</span>.</p>
<p><b>Смешанный тип → -ium</b>: основа на две согласные (<span class="lat">dens → dentium</span>, <span class="lat">os → ossium</span>) или одинаковое число слогов в Nom. и Gen. Sg. (<span class="lat">canalis — canalis → canalium</span>).</p>
<p>Исключение: <span class="lat">vas, vasis n</span> — Gen. Pl. <span class="lat">vasorum</span> (форма в пособии / КР).</p></div>"""),
            ch_item("d3-ium", "Gen. Pl. от <span class=\"lat\">dens, dentis m</span> — «зубов»?", "dentium", ["dentum", "dentorum", "dentis"], "Основа dent- на две согласные → -ium."),
            ch_item("d3-um", "Gen. Pl. от <span class=\"lat\">radix, icis f</span> — «корней»?", "radicum", ["radicium", "radicorum", "radicis"], "Основа radic- на одну согласную → -um."),
        ]})
    elif decl == 4:
        L.append({"id": "d4-l1", "title": "Окончания и ловушка -us", "items": [
            th("d4-l1t", """<span class="badge">4 склонение · пособие с. 53</span>
<div class="kl-th"><p>Признак — Gen. Sg. на <b>-us</b>. Обычно мужской род; женский в анатомии — <span class="lat">manus, us f</span> (кисть).</p>
<table class="kl-t"><tr><th></th><th>Nom. Sg.</th><th>Gen. Sg.</th><th>Nom. Pl.</th><th>Gen. Pl.</th></tr>
<tr><th>m (и f)</th><td>-us</td><td>-us</td><td>-us</td><td>-uum</td></tr>
<tr><th>n</th><td>-u</td><td>-us</td><td>-ua</td><td>-uum</td></tr></table>
<p>У мужского рода <b>совпадают</b> Nom. Sg., Gen. Sg. и Nom. Pl. (все <span class="lat">arcus</span>, <span class="lat">ductus</span>). Падеж узнаёте по месту в словосочетании и по смыслу.</p></div>
<span class="badge">Разбор: arcus vertebrae — дуга позвонка (с. 11)</span>
<div class="kl-parse">
<div>1) <span class="lat">arcus, us m</span> — что? Одна дуга → Nom. Sg. <b class="lat">arcus</b></div>
<div>2) <span class="lat">vertebra, ae f</span> — чего? Одного позвонка → Gen. Sg. <b class="lat">vertebrae</b></div>
<div>Несколько дуг нескольких позвонков: <b class="lat">arcus vertebrarum</b> (первое слово внешне то же — Nom. Pl. тоже -us).</div></div>"""),
            ch_item("d4-us", "У <span class=\"lat\">ductus, us m</span> форма <span class=\"lat\">ductus</span> может быть…", "Nom. Sg., Gen. Sg. или Nom. Pl.", ["Только Nom. Sg.", "Только Gen. Pl.", "Только Nom. Pl."], "с. 53: у м. р. 4 скл. эти три формы совпадают. Gen. Pl. — ductuum."),
            phrase_item(find_ph("arcus vertebrae"), "rl", True),
            phrase_item(find_ph("arcus vertebrarum"), "rl", True),
        ]})
        L.append({"id": "d4-l2", "title": "Средний род и пары из пособия", "items": [
            th("d4-l2t", """<span class="badge">Средний род 4 скл. · с. 53–54</span>
<div class="kl-th"><p><span class="lat">cornu, us n</span> (рог), <span class="lat">genu, us n</span> (колено): Nom. Sg. на <b>-u</b>, Nom. Pl. на <b>-ua</b>, Gen. Sg. <b>-us</b>, Gen. Pl. <b>-uum</b>.</p>
<p>Пример пособия: <span class="lat">cornu</span> — <span class="lat">cornus</span> — <span class="lat">cornua</span> — <span class="lat">cornuum</span>.</p></div>"""),
            phrase_item(find_ph("cornu ventriculi"), "rl", True),
            phrase_item(find_ph("ostium ductus"), "rl", True),
            phrase_item(find_ph("digitus manus"), "rl", True),
            phrase_item(find_ph("arteria genus"), "rl", True),
        ]})
    else:
        L.append({"id": "d5-l1", "title": "facies и окончания 5 скл.", "items": [
            th("d5-l1t", """<span class="badge">5 склонение · пособие с. 53</span>
<div class="kl-th"><p>Признак — Gen. Sg. на <b>-ei</b>. Как правило женский род. В анатомии почти всегда <span class="lat">facies, ei f</span> — лицо, поверхность.</p>
<table class="kl-t"><tr><th></th><th>ед. ч.</th><th>мн. ч.</th></tr>
<tr><th>Nom. (что?)</th><td>facies (-es)</td><td>facies (-es)</td></tr>
<tr><th>Gen. (чего?)</th><td>faciei (-ei)</td><td>facierum (-erum)</td></tr></table>
<p>Nom. Sg. и Nom. Pl. совпадают (<b>-es</b>). Gen. Sg. — это <span class="lat">faciei</span>, не <span class="lat">facies</span>.</p></div>
<span class="badge">Разбор: facies ossis — поверхность кости</span>
<div class="kl-parse">
<div>1) <span class="lat">facies, ei f</span> — что? Одна поверхность → Nom. Sg. <b class="lat">facies</b></div>
<div>2) <span class="lat">os, ossis n</span> — чего? Одной кости → Gen. Sg. <b class="lat">ossis</b></div>
<div>Несколько поверхностей нескольких костей: <b class="lat">facies ossium</b>.</div></div>"""),
            ch_item("d5-ei", "Gen. Sg. от <span class=\"lat\">facies, ei f</span>?", "faciei", ["facies", "facierum", "faciae"], "5 скл.: Gen. Sg. на -ei (с. 53)."),
            phrase_item(find_ph("facies ossis"), "rl", True),
            phrase_item(find_ph("facies ossium"), "rl", True),
        ]})
    for les in L:
        les["items"] = [it for it in les["items"] if it]
    rest = [p for p in phrases if p["src"] != "pattern"]
    pat = [p for p in phrases if p["src"] == "pattern"]
    L.extend(chunked(decl, rest))
    if pat:
        L.extend(chunked(decl, pat, label="Слова минимума", tag="m"))
    return L

TITLES = {1: "I склонение", 2: "II склонение", 3: "III склонение", 4: "IV склонение", 5: "V склонение"}
DP_DATA = {}
order = {"prompt": 0, "teacher32": 1, "textbook": 2, "usermin": 3, "teacher312": 4, "pattern": 5}
warns = []
for d in (1, 2, 3, 4, 5):
    phs = sorted(by_decl[d], key=lambda p: (order.get(p["src"], 9), p["lat"]))
    wN = sum(1 for p in phs if p["warn"])
    DP_DATA[str(d)] = {
        "id": "d%d" % d,
        "title": TITLES[d],
        "hint": HINT[d],
        "pids": [p["id"] for p in phs],
        "lessons": lessons_for(d, phs),
        "warnN": wN,
    }
    for p in phs:
        if p["warn"]:
            warns.append((d, p["lat"], p["warn"]))
        if p["unmatched"]:
            warns.append((d, p["lat"], "не сопоставлены: " + ", ".join(p["unmatched"])))

NOM_ALIAS = {
    "peritonaeum": ("peritonaeum", "peritoneum"),
    "peritoneum": ("peritonaeum", "peritoneum"),
    "caecum": ("caecum", "cecum"),
    "cecum": ("caecum", "cecum"),
    "commissura": ("commissura", "comissura"),
    "c(a)ecum": ("caecum", "cecum"),
    "co(m)missura": ("commissura", "comissura"),
}

def noun_used_in(decl, nom):
    U = DP_DATA[str(decl)]
    wants = {nrm(x) for x in NOM_ALIAS.get(nom.lower(), (nom,))}
    wants.add(nrm(nom))
    for pid in U["pids"]:
        p = next(x for x in POOL.values() if x["id"] == pid)
        for tok in p["tokens"]:
            if tok.get("slot") not in ("N", "G"):
                continue
            heads = {nrm(tok.get("head") or ""), nrm((tok.get("dict") or "").split(",")[0])}
            heads.update(nrm(f) for f in (tok.get("forms") or []))
            heads.add(nrm(tok.get("form") or ""))
            if wants & heads:
                return True
    return False

still_missing = {1: [], 2: [], 3: [], 4: [], 5: []}
for d, ents in USER_NOUNS.items():
    for e in ents:
        if not noun_used_in(d, e["nom"]) and not noun_used_in(d, e["dict"].split(",")[0]):
            still_missing[d].append(e)

# III muscle-agent nouns from the same minimum (listed there as «musculus X»)
for agent, rus in [
    ("adductor", "приводящая мышца"),
    ("buccinator", "щёчная мышца"),
    ("corrugator", "сморщивающая мышца"),
    ("masseter", "жевательная мышца"),
]:
    if not noun_used_in(3, agent):
        still_missing[3].append({"nom": agent, "dict": "", "rus": rus})

def drill_lesson(decl, ents):
    items = [th("d%d-drt" % decl, "<span class=\"badge\">Словарная форма · Gen.</span><div class=\"kl-th\"><p>Эти слова есть в минимуме преподавателя, но отдельной готовой фразы к ним не было. Напишите <b>Gen. Sg.</b> и <b>Gen. Pl.</b> по словарной форме. Затем они входят в словосочетания по правилу «что? + чего?».</p></div>")]
    for e in ents:
        ent = lex_named(e["nom"]) or next((v for v in LEX.values() if v.get("nom", "").lower() == e["nom"].lower()), None)
        if not ent:
            continue
        f = ent["forms"]
        dform = ent.get("dict") or (ent["nom"] + ", " + ent.get("gen", "") + " " + ent.get("g", ""))
        items.append(ch_item("d%d-gs-%s" % (decl, ent["nom"]), "Gen. Sg. («чего?» ед.) от <span class=\"lat\">%s</span> — %s" % (dform, e.get("rus") or ent.get("rus") or ""), f["gs"], [f["gp"], f["ns"], f["np"]], "Родительный падеж ед. ч."))
        items.append(ch_item("d%d-gp-%s" % (decl, ent["nom"]), "Gen. Pl. («чего?» мн.) от <span class=\"lat\">%s</span> — %s" % (dform, e.get("rus") or ent.get("rus") or ""), f["gp"], [f["gs"], f["ns"], f["np"]], "Родительный падеж мн. ч."))
    return {"id": "d%d-dr" % decl, "title": "Слова минимума: Gen. Sg. и Gen. Pl.", "items": [it for it in items if it]}

for d, ents in still_missing.items():
    if ents:
        DP_DATA[str(d)]["lessons"].append(drill_lesson(d, ents))

bad = self_check()
lines = ["FORM CHECK: " + ("OK" if not bad else "FAIL " + "; ".join(bad))]
lines.append("LEX nouns: %d  adjs: %d" % (sum(1 for k in LEX if not k.startswith("adj:")), sum(1 for k in LEX if k.startswith("adj:"))))
lines.append("USER MIN nouns I–V: %s" % ({d: len(USER_NOUNS[d]) for d in (1,2,3,4,5)}))
lines.append("USER MIN adjs: I–II %d, III %d (no new sections)" % (len(USER_MIN["adjs12"]), len(USER_MIN["adjs3"])))
lines.append("coverage phrases generated: %d" % len(coverage_added))
for d in (1,2,3,4,5):
    miss = still_missing[d]
    lines.append("  still without phrase after coverage, %d скл.: %d %s" % (d, len(miss), ", ".join(e["nom"] for e in miss)))
lines.append("POOL unique phrases: %d" % len(POOL))
for d in (1, 2, 3, 4, 5):
    phs = by_decl[d]
    nn = sum(1 for p in phs if not any(t["slot"] == "A" for t in p["tokens"]))
    lines.append("  %d скл.: %d фраз (без прилагательных: %d), уроков: %d" % (d, len(phs), nn, len(DP_DATA[str(d)]["lessons"])))
lines.append("phrases with no noun matched: %d" % len(unmatched_ph))
for p in unmatched_ph[:15]:
    lines.append("  ? %s :: %s unmatched=%s" % (p["lat"], p["rus"], p["unmatched"]))
lines.append("warn rows: %d" % len(warns))
# unique unmatched tokens across assigned phrases
ut = sorted({u for p in POOL.values() for u in p["unmatched"]})
lines.append("unmatched tokens: " + ", ".join(ut[:80]))
(ROOT / "tools" / "ph_report.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
pool = {p["id"]: {k: p[k] for k in ("id", "lat", "rus", "warn", "tokens")} for p in POOL.values()}
bundle = {"pool": pool, "sec": DP_DATA}
(Path("/tmp/dp_data.json")).write_text(json.dumps(bundle, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print("\n".join(lines))
print("wrote /tmp/dp_data.json", Path("/tmp/dp_data.json").stat().st_size, "pool", len(pool))
