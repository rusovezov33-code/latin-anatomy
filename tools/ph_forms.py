# -*- coding: utf-8 -*-
"""Form generation for Latin nouns (Nom/Gen, Sg/Pl) per Провоторова 2021."""
import re

VOWELS = set("aeiouy")

def syll(s):
    return len(re.findall(r"[aeiouy]+", s.lower()))

def cpre(a, b):
    i = 0
    while i < len(a) and i < len(b) and a[i] == b[i]:
        i += 1
    return i

# Verified against пособие (с. 12, 15, 43–44, 53) and KR keys in the game.
GEN3_FIX = {
    ("hepar", "atis"): "hepatis",
    ("pancreas", "atis"): "pancreatis",
    ("frons", "ntis"): "frontis",
    ("venter", "ntris"): "ventris",
    ("venter", "tris"): "ventris",
    ("gaster", "tris"): "gastris",
    ("mater", "tris"): "matris",
    ("hallux", "ucis"): "hallucis",
    ("occput", "itis"): "occipitis",
    ("occiput", "itis"): "occipitis",
    ("ungius", "is"): "unguis",
    ("unguis", "is"): "unguis",
    ("larynx", "ngis"): "laryngis",
    ("larynx", "yngis"): "laryngis",
    ("phalanx", "ngis"): "phalangis",
    ("pharynx", "ngis"): "pharyngis",
    ("pharynx", "yngis"): "pharyngis",
    ("meninx", "ngis"): "meningis",
    ("coccyx", "ygis"): "coccygis",
    ("thorax", "acis"): "thoracis",
    ("apex", "icis"): "apicis",
    ("index", "icis"): "indicis",
    ("pollex", "icis"): "pollicis",
    ("flexor", "oris"): "flexoris",
    ("rotator", "oris"): "rotatoris",
    ("constrictor", "oris"): "constrictoris",
    ("pubes", "is"): "pubis",
    ("femur", "oris"): "femoris",
    ("tempus", "oris"): "temporis",
    ("corpus", "oris"): "corporis",
    ("crus", "cruris"): "cruris",
}

def gen_sg_3(nom, hint):
    nom, hint = nom.lower(), hint.lower()
    if (nom, hint) in GEN3_FIX:
        return GEN3_FIX[(nom, hint)]
    if hint == "is":
        if nom.endswith("is"):
            return nom
        if nom.endswith("es"):
            return nom[:-2] + "is"
        if nom.endswith("e"):
            return nom[:-1] + "is"
        return nom + "is"
    # полный Gen., как в словаре: dens, dentis; pars, partis; os, ossis
    if hint.startswith(nom[:2]) and len(hint) >= len(nom):
        return hint
    if len(nom) <= 3 and hint[0] == nom[0] and len(hint) >= 4:
        return hint
    drops = ["iculus", "culus", "en", "ex", "ix", "as", "ut", "ur", "us", "um", "or", "er", "es", "is", "on", "o", "a", "e", "x", "s"]
    best, best_key = None, None
    for d in drops:
        if not nom.endswith(d):
            continue
        cand = nom[:-len(d)] + hint
        cp = cpre(nom, cand)
        if cp < 2:
            continue
        # longer nominative drop first, then prefix overlap (avoids apex→apeicis, caput→capuitis)
        key = (len(d), cp, -len(cand))
        if best_key is None or key > best_key:
            best, best_key = cand, key
    return best or (nom[:-1] + hint)

def third_gp_np(nom, gen_sg, gender):
    """Nom.Pl and Gen.Pl for 3rd decl. (пособие с. 42–44)."""
    if nom == "vas":
        return "vasa", "vasorum"  # исключение, с. 44 / форма в КР: vasorum
    stem = gen_sg[:-2] if gen_sg.endswith("is") else gen_sg
    # i-основа ср. р. на -e / -al / -ar (rete, animal, calcar): Gen. = основа+is без смены согласной
    i_stem_n = gender == "n" and (
        (nom.endswith("e") and gen_sg == nom[:-1] + "is")
        or (nom.endswith(("al", "ar")) and gen_sg == nom + "is")
    )
    two_cons = len(stem) >= 2 and stem[-1] not in VOWELS and stem[-2] not in VOWELS
    eq = syll(nom) == syll(gen_sg)
    if gender == "n":
        np = stem + ("ia" if i_stem_n else "a")
    else:
        np = stem + "es"
    if i_stem_n or two_cons or eq:
        gp = stem + "ium"
    else:
        gp = stem + "um"
    return np, gp

def parse_dict(lat):
    """'ala, ae f' / 'accessorius, a, um' / 'alaris, e' -> dict meta or None."""
    lat = re.sub(r"\s+", " ", lat.strip())
    parts = [p.strip() for p in lat.split(",")]
    if not parts:
        return None
    nom = parts[0].split()[0]
    rest = ", ".join(parts[1:])
    gm = re.search(r"\b([mfn])\s*$", rest)
    if gm:
        gender = gm.group(1)
        gen = re.sub(r"\b[mfn]\s*$", "", rest).strip()
        # 4th n: cornu, us n; 5th: facies, ei f
        decl_map = {"ae": 1, "i": 2, "us": 4, "ei": 5}
        # Greek 1st: raphe, es f
        if gen == "es":
            return {"kind": "noun", "nom": nom, "gen": gen, "g": gender, "d": 1, "dict": lat, "special": "raphe"}
        d = decl_map.get(gen, 3)
        return {"kind": "noun", "nom": nom, "gen": gen, "g": gender, "d": d, "dict": lat}
    if rest.endswith("a, um") or rest == "a, um":
        return {"kind": "adj", "nom": nom, "grp": 12, "dict": lat}
    if rest in ("e",) or rest.endswith(" e"):
        return {"kind": "adj", "nom": nom, "grp": 3, "dict": lat}
    if rest in ("ius",) or rest.endswith(" ius"):
        return {"kind": "adj", "nom": nom, "grp": 3, "cmp": True, "dict": lat}
    return None

def noun_forms(meta):
    """Return {ns, gs, np, gp} and endings."""
    nom, d, g, gen = meta["nom"].lower(), meta["d"], meta["g"], meta.get("gen", "")
    special = meta.get("special")
    if special == "raphe":
        return {"ns": nom, "gs": "raphes", "np": "raphae", "gp": "rapharum",
                "end": {"ns": "-e", "gs": "-es", "np": "-ae", "gp": "-arum"}}
    if nom == "lumbi":  # plural only, teacher list: lumbi, orum m
        return {"ns": "lumbus", "gs": "lumbi", "np": "lumbi", "gp": "lumborum",
                "end": {"ns": "-us", "gs": "-i", "np": "-i", "gp": "-orum"}, "pl_only": True}
    if d == 1:
        stem = nom[:-1] if nom.endswith("a") else nom
        return {"ns": nom, "gs": stem + "ae", "np": stem + "ae", "gp": stem + "arum",
                "end": {"ns": "-a", "gs": "-ae", "np": "-ae", "gp": "-arum"}}
    if d == 2:
        if nom.endswith("on"):
            stem = nom[:-2]
        elif nom.endswith("um"):
            stem = nom[:-2]
        elif nom.endswith("us"):
            stem = nom[:-2]
        else:
            stem = nom
        neut = g == "n" or nom.endswith("um") or nom.endswith("on")
        # ⚠ palatum marked m by teacher, n by textbook p.15
        np = stem + ("a" if neut else "i")
        return {"ns": nom, "gs": stem + "i", "np": np, "gp": stem + "orum",
                "end": {"ns": "-um, -on" if neut else "-us", "gs": "-i",
                        "np": "-a" if neut else "-i", "gp": "-orum"}}
    if d == 4:
        if g == "n" or nom in ("cornu", "genu"):
            return {"ns": nom, "gs": nom + "s", "np": nom + "a", "gp": nom + "um",
                    "end": {"ns": "-u", "gs": "-us", "np": "-ua", "gp": "-uum"}}
        stem = nom[:-2] if nom.endswith("us") else nom
        return {"ns": nom, "gs": nom, "np": nom, "gp": stem + "uum",
                "end": {"ns": "-us", "gs": "-us", "np": "-us", "gp": "-uum"}}
    if d == 5:
        stem = nom[:-2] if nom.endswith("es") else nom
        return {"ns": nom, "gs": stem + "ei", "np": nom, "gp": stem + "erum",
                "end": {"ns": "-es", "gs": "-ei", "np": "-es", "gp": "-erum"}}
    # 3
    gs = gen_sg_3(nom, gen)
    np, gp = third_gp_np(nom, gs, g)
    return {"ns": nom, "gs": gs, "np": np, "gp": gp,
            "end": {"ns": "(Nom.)", "gs": "-is", "np": "-es" if g != "n" else "-a / -ia",
                    "gp": "-um / -ium"}}

def adj_forms(meta):
    """Generous form set for matching tokens (not for teaching generation)."""
    nom = meta["nom"].lower()
    out = set()
    if meta.get("grp") == 12:
        if nom.endswith("us"):
            st = nom[:-2]
        elif nom.endswith("er"):
            # dexter / liber / asper / ruber / sacer
            if nom in ("dexter", "sinister"):
                st = nom[:-2] + "r"  # dextr, sinistr
            elif nom == "ruber":
                st = "rubr"
            elif nom == "sacer":
                st = "sacr"
            elif nom in ("liber", "asper"):
                st = nom[:-2] + "er"  # liber -> liber? actually liber, era -> liber-
                st = nom  # liber + a = libera if we use nom as? 
                # liber, era, erum → stem liber- wait: libera, liberum, liberi
                st = nom  # libera = liber + a? liber+a = libera, stem = nom = liber yes if we add endings to nom for -er that keeps e
                # asper, era, erum → asper-
                st = nom
            else:
                st = nom[:-2]
            out.add(nom)
        else:
            st = nom
        for e in ("us", "a", "um", "i", "ae", "o", "os", "orum", "arum",
                  "e", "is", "es"):
            out.add(st + e)
        out.add(nom)
        return out
    # 3rd group
    if nom.endswith("is"):
        st = nom[:-2]
        out.update([nom, st + "e", st + "is", st + "es", st + "ia", st + "ium", st + "ibus", st + "em"])
    elif nom.endswith("or"):
        out.update([nom, nom + "is", nom + "es", nom + "um", nom + "i", nom + "e", nom + "a", nom + "em"])
        # ius neuter: anterius / superius
        out.add(nom[:-2] + "ius" if nom.endswith("ior") else nom + "ius")
        if nom.endswith("ior"):
            out.add(nom[:-3] + "ius")  # anterior -> anterius
    else:
        out.add(nom)
    return out


KNOWN_CHECK = [
    # 1 (с. 12): ala — alae — alae — alarum
    ("ala, ae f", {"ns": "ala", "gs": "alae", "np": "alae", "gp": "alarum"}),
    ("costa, ae f", {"ns": "costa", "gs": "costae", "np": "costae", "gp": "costarum"}),
    ("fractura, ae f", {"ns": "fractura", "gs": "fracturae", "np": "fracturae", "gp": "fracturarum"}),
    # 2 (с. 15): nervus — nervi — nervi — nervorum; tuberculum — tuberculi — tubercula — tuberculorum
    ("nervus, i m", {"ns": "nervus", "gs": "nervi", "np": "nervi", "gp": "nervorum"}),
    ("tuberculum, i n", {"ns": "tuberculum", "gs": "tuberculi", "np": "tubercula", "gp": "tuberculorum"}),
    ("organon, i n", {"ns": "organon", "gs": "organi", "np": "organa", "gp": "organorum"}),
    ("ligamentum, i n", {"ns": "ligamentum", "gs": "ligamenti", "np": "ligamenta", "gp": "ligamentorum"}),
    ("radius, i m", {"ns": "radius", "gs": "radii", "np": "radii", "gp": "radiorum"}),
    # 3 (с. 43–44)
    ("corpus, oris n", {"ns": "corpus", "gs": "corporis", "np": "corpora", "gp": "corporum"}),
    ("caput, itis n", {"ns": "caput", "gs": "capitis", "np": "capita", "gp": "capitum"}),
    ("dens, dentis m", {"ns": "dens", "gs": "dentis", "np": "dentes", "gp": "dentium"}),
    ("os, ossis n", {"ns": "os", "gs": "ossis", "np": "ossa", "gp": "ossium"}),
    ("os, oris n", {"ns": "os", "gs": "oris", "np": "ora", "gp": "orum"}),
    ("canalis, is m", {"ns": "canalis", "gs": "canalis", "np": "canales", "gp": "canalium"}),
    ("auris, is f", {"ns": "auris", "gs": "auris", "np": "aures", "gp": "aurium"}),
    ("rete, is n", {"ns": "rete", "gs": "retis", "np": "retia", "gp": "retium"}),
    ("vas, vasis n", {"ns": "vas", "gs": "vasis", "np": "vasa", "gp": "vasorum"}),
    ("margo, inis m", {"ns": "margo", "gs": "marginis", "np": "margines", "gp": "marginum"}),
    ("regio, onis f", {"ns": "regio", "gs": "regionis", "np": "regiones", "gp": "regionum"}),
    ("pars, partis f", {"ns": "pars", "gs": "partis", "np": "partes", "gp": "partium"}),
    ("hepar, atis n", {"ns": "hepar", "gs": "hepatis", "np": "hepata", "gp": "hepatum"}),
    ("foramen, inis n", {"ns": "foramen", "gs": "foraminis", "np": "foramina", "gp": "foraminum"}),
    ("radix, icis f", {"ns": "radix", "gs": "radicis", "np": "radices", "gp": "radicum"}),
    ("cor, cordis n", {"ns": "cor", "gs": "cordis", "np": "corda", "gp": "cordium"}),
    # 4 (с. 53): ductus — ductus — ductus — ductuum; cornu — cornus — cornua — cornuum
    ("ductus, us m", {"ns": "ductus", "gs": "ductus", "np": "ductus", "gp": "ductuum"}),
    ("arcus, us m", {"ns": "arcus", "gs": "arcus", "np": "arcus", "gp": "arcuum"}),
    ("cornu, us n", {"ns": "cornu", "gs": "cornus", "np": "cornua", "gp": "cornuum"}),
    ("genu, us n", {"ns": "genu", "gs": "genus", "np": "genua", "gp": "genuum"}),
    ("manus, us f", {"ns": "manus", "gs": "manus", "np": "manus", "gp": "manuum"}),
    # 5 (с. 53): facies — faciei — facies — facierum
    ("facies, ei f", {"ns": "facies", "gs": "faciei", "np": "facies", "gp": "facierum"}),
    ("larynx, yngis m", {"ns": "larynx", "gs": "laryngis", "np": "larynges", "gp": "laryngium"}),
    ("larynx, ngis m", {"ns": "larynx", "gs": "laryngis", "np": "larynges", "gp": "laryngium"}),
    ("coccyx, ygis m", {"ns": "coccyx", "gs": "coccygis", "np": "coccyges", "gp": "coccygum"}),
    ("meninx, ngis f", {"ns": "meninx", "gs": "meningis", "np": "meninges", "gp": "meningium"}),
    ("atlas, antis m", {"ns": "atlas", "gs": "atlantis", "np": "atlantes", "gp": "atlantium"}),
    ("phalanx, ngis f", {"ns": "phalanx", "gs": "phalangis", "np": "phalanges", "gp": "phalangium"}),
    ("thorax, acis m", {"ns": "thorax", "gs": "thoracis", "np": "thoraces", "gp": "thoracum"}),
    ("cavitas, atis f", {"ns": "cavitas", "gs": "cavitatis", "np": "cavitates", "gp": "cavitatum"}),
    ("coxa, ae f", {"ns": "coxa", "gs": "coxae", "np": "coxae", "gp": "coxarum"}),
    ("ilium, i n", {"ns": "ilium", "gs": "ilii", "np": "ilia", "gp": "iliorum"}),
    ("ischium, i n", {"ns": "ischium", "gs": "ischii", "np": "ischia", "gp": "ischiorum"}),
    ("apex, icis m", {"ns": "apex", "gs": "apicis", "np": "apices", "gp": "apicum"}),
    ("index, icis m", {"ns": "index", "gs": "indicis", "np": "indices", "gp": "indicum"}),
    ("pollex, icis m", {"ns": "pollex", "gs": "pollicis", "np": "pollices", "gp": "pollicum"}),
    ("flexor, oris m", {"ns": "flexor", "gs": "flexoris", "np": "flexores", "gp": "flexorum"}),
    ("rotator, oris m", {"ns": "rotator", "gs": "rotatoris", "np": "rotatores", "gp": "rotatorum"}),
]

def self_check():
    bad = []
    for dict_, exp in KNOWN_CHECK:
        meta = parse_dict(dict_)
        f = noun_forms(meta)
        for k, v in exp.items():
            if f.get(k) != v:
                bad.append(f"{dict_} {k}: got {f.get(k)} expected {v}")
    return bad

if __name__ == "__main__":
    bad = self_check()
    if bad:
        print("FAIL")
        print("\n".join(bad))
        raise SystemExit(1)
    print("OK", len(KNOWN_CHECK), "paradigms")
