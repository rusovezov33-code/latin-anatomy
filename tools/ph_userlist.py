# -*- coding: utf-8 -*-
"""Parse the teacher's lexical minimum (user docx) and coverage pairings."""
from __future__ import annotations
import re
from pathlib import Path

DOCX_CANDIDATES = [
    Path("/home/box/sand-data/agents/79bb2139-0375-48de-a40b-f7b30bf1dad0/attachments/11b469d6b3543da47491d3746bf48d85baa5dda38422dc35c98f08e0417d75ac.docx"),
    Path("/workspace/latin_user_min.docx"),
]

def expand_optional(s: str) -> str:
    # co(m)missura -> commissura; c(a)ecum -> caecum; periton(a)eum -> peritonaeum
    return re.sub(r"\(([a-zA-Z])\)", r"\1", s)

def split_entry(line: str) -> tuple[str, str]:
    line = re.sub(r"^\d+\.\s*", "", line).strip()
    line = line.replace("\t", " — ")
    line = re.sub(r"\s+", " ", line)
    parts = re.split(r"\s*[—–]\s*|(?<=[A-Za-z])-(?=[А-Яа-яЁё])|\s+-\s+", line, maxsplit=1)
    if len(parts) == 2:
        return parts[0].strip(" -"), re.sub(r"\s+", " ", parts[1]).strip(" -.")
    m = re.match(r"^(.+?\b[mfn])\s*[-—]?\s*(.+)$", line)
    if m and re.search(r"[а-яё]", m.group(2), re.I):
        return m.group(1).strip(" -"), m.group(2).strip(" -.")
    return line.strip(), ""

def load_docx():
    from docx import Document
    path = next((p for p in DOCX_CANDIDATES if p.exists()), None)
    if not path:
        raise FileNotFoundError("user lexical minimum docx not found")
    doc = Document(str(path))
    paras = [p.text.replace("\xa0", " ").strip() for p in doc.paragraphs if p.text.replace("\xa0", " ").strip()]
    sections = {}
    cur = None
    for t in paras:
        if t.startswith("Cуществительные") or t.startswith("Существительные") or t.startswith("Прилагательные") or t.startswith("Устойчивые"):
            cur = t
            sections[cur] = []
        elif cur:
            sections[cur].append(t)
    return path, sections

def parse_minimum():
    path, sections = load_docx()
    nouns = {1: [], 2: [], 3: [], 4: [], 5: []}
    muscles = []
    set_phrases = []
    adjs12, adjs3 = [], []

    sec_map = {
        1: next(k for k in sections if "I склонение" in k and "Прилаг" not in k),
        2: next(k for k in sections if k.startswith("Существительные II")),
        3: next(k for k in sections if "III склонение" in k and "Прилаг" not in k),
        45: next(k for k in sections if "IV" in k and "Существительн" in k),
    }
    from ph_forms import parse_dict
    for dkey, sname in sec_map.items():
        for raw in sections[sname]:
            lat, rus = split_entry(raw)
            rus = rus.replace("(доп)", "").strip(" .")
            rus = rus.replace(".", ", ") if rus.count(".") == 1 and "," not in rus else rus
            if lat.lower().startswith("musculus ") and "," not in lat:
                muscles.append({"lat": lat, "rus": rus, "raw": raw})
                continue
            lat_n = expand_optional(lat)
            # keep a nicer dict string (spaces after commas)
            lat_n = re.sub(r",\s*", ", ", lat_n)
            lat_n = re.sub(r",(?=\S)", ", ", lat_n)
            meta = parse_dict(lat_n)
            decl = meta["d"] if meta and meta.get("kind") == "noun" else (5 if re.search(r",\s*ei\b", lat_n) else (4 if dkey == 45 else dkey))
            nouns[decl].append({"dict": lat_n, "rus": rus, "raw": raw, "orig": lat, "nom": (meta or {}).get("nom", lat_n.split(",")[0].split()[0])})

    adj12_name = next(k for k in sections if "Прилагательные I-II" in k or "Прилагательные I–II" in k)
    adj3_name = next(k for k in sections if "Прилагательные III" in k)
    set_name = next(k for k in sections if "Устойчивые" in k)
    for raw in sections[adj12_name]:
        lat, rus = split_entry(raw)
        adjs12.append({"dict": re.sub(r",\s*", ", ", expand_optional(lat)), "rus": rus.strip()})
    for raw in sections[adj3_name]:
        lat, rus = split_entry(raw)
        adjs3.append({"dict": re.sub(r",\s*", ", ", expand_optional(lat)), "rus": rus.strip()})
    for raw in sections[set_name]:
        lat, rus = split_entry(raw)
        set_phrases.append({"lat": lat.strip(), "rus": rus.strip()})
    return {
        "path": str(path),
        "nouns": nouns,
        "muscles": muscles,
        "set_phrases": set_phrases,
        "adjs12": adjs12,
        "adjs3": adjs3,
    }

# (head_nom, head_slot, dep_nom, dep_slot, rus, alts)
# slots: ns/gs/np/gp — resolved against the lexicon after load
# dep may be None for safety; we always have two nouns except pelvis+adj handled separately
COVERAGE_SPEC = [
    # I as head or dependent
    ("apertura", "ns", "thorax", "gs", "апертура грудной клетки", ""),
    ("columna", "ns", "vertebra", "gp", "столб позвонков", ""),
    ("commissura", "ns", "labium", "gp", "спайка губ", ""),
    ("corona", "ns", "dens", "gs", "коронка зуба|венец зуба", ""),
    ("fascia", "ns", "brachium", "gs", "фасция плеча", ""),
    ("fibra", "ns", "musculus", "gs", "волокно мышцы", ""),
    ("fovea", "ns", "caput", "gs", "ямка головки", ""),
    ("ligamentum", "ns", "nucha", "gs", "связка выи", ""),
    ("palma", "ns", "manus", "gs", "ладонь руки|ладонь кисти", ""),
    ("palpebra", "ns", "oculus", "gs", "веко глаза", ""),
    ("planta", "ns", "pes", "gs", "подошва стопы", ""),
    ("protuberantia", "ns", "occiput", "gs", "выступ затылка", ""),
    ("pulpa", "ns", "dens", "gs", "пульпа зуба", ""),
    ("raphe", "ns", "palatum", "gs", "шов нёба", ""),
    ("squama", "ns", "os_ossis", "gs", "чешуя кости", ""),
    ("corpus", "ns", "tibia", "gs", "тело большеберцовой кости", ""),
    ("trochlea", "ns", "humerus", "gs", "блок плечевой кости", ""),
    ("valva", "ns", "aorta", "gs", "клапан аорты", ""),
    # II
    ("acromion", "ns", "scapula", "gs", "акромион лопатки", ""),
    ("alveolus", "ns", "dens", "gs", "альвеола зуба", ""),
    ("bronchus", "ns", "pulmo", "gs", "бронх легкого|бронх лёгкого", ""),
    ("paries", "ns", "caecum", "gs", "стенка слепой кишки", ""),
    ("cavum", "ns", "os_oris", "gs", "полость рта", ""),
    ("enamelum", "ns", "dens", "gs", "эмаль зуба", ""),
    ("frenulum", "ns", "lingua", "gs", "уздечка языка", ""),
    ("paries", "ns", "ileum", "gs", "стенка подвздошной кишки", ""),
    ("paries", "ns", "jejunum", "gs", "стенка тощей кишки", ""),
    ("caput", "ns", "metacarpus", "gs", "головка пясти", ""),
    ("cavum", "ns", "peritoneum", "gs", "полость брюшины", ""),
    ("segmentum", "ns", "pulmo", "gs", "сегмент легкого|сегмент лёгкого", ""),
    ("spatium", "ns", "collum", "gs", "пространство шеи|промежуток шеи", ""),
    ("arcus", "ns", "supercilium", "gs", "дуга брови", ""),
    ("caput", "ns", "talus", "gs", "головка таранной кости", ""),
    ("os_ossis", "ns", "tarsus", "gs", "кость предплюсны", ""),
    ("membrana", "ns", "tympanum", "gs", "перепонка барабана|барабанная перепонка", ""),
    # III
    ("arcus", "ns", "atlas", "gs", "дуга атланта|дуга 1 шейного позвонка", ""),
    ("os_ossis", "ns", "coccyx", "gs", "кость копчика", ""),
    ("regio", "ns", "crus", "gs", "область голени", ""),
    ("fornix", "ns", "pharynx", "gs", "свод глотки", ""),
    ("meninx", "ns", "encephalon", "gs", "мозговая оболочка головного мозга", ""),
    ("regio", "ns", "occiput", "gs", "область затылка", ""),
    ("trochanter", "ns", "femur", "gs", "вертел бедра", ""),
    ("tuberositas", "ns", "tibia", "gs", "бугристость большеберцовой кости", ""),
    ("regio", "ns", "zygoma", "gs", "область скулы", ""),
    # IV
    ("hiatus", "ns", "oesophagus", "gs", "щель пищевода|расщелина пищевода", ""),
]

# special: noun + adjective from the same teacher list
COVERAGE_ADJ = [
    ("pelvis", "ns", "renalis", "почечная лоханка", ""),
]
