# -*- coding: utf-8 -*-
"""Inject DP_DATA + engine into index.html and bump sw.js."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
html_path = ROOT / "index.html"
html = html_path.read_text(encoding="utf-8")
bundle = json.loads(Path("/tmp/dp_data.json").read_text(encoding="utf-8"))
engine = (ROOT / "tools" / "ph_engine.js").read_text(encoding="utf-8")

TARGET_SW = "v12-phdecl-userlist-2026-11-10"

def write_sw():
    sw = ROOT / "sw.js"
    st = sw.read_text(encoding="utf-8")
    import re
    st2, n = re.subn(r'const VERSION = "[^"]+";', f'const VERSION = "{TARGET_SW}";', st, count=1)
    if n != 1:
        raise SystemExit("could not bump sw.js VERSION")
    sw.write_text(st2, encoding="utf-8")
    print("sw.js bumped to", TARGET_SW)

if "const DP_POOL =" in html:
    payload = (
        "const DP_POOL = "
        + json.dumps(bundle["pool"], ensure_ascii=False, separators=(",", ":"))
        + ";\nconst DP_DATA = "
        + json.dumps(bundle["sec"], ensure_ascii=False, separators=(",", ":"))
        + ";\n"
    )
    a = html.find("const DP_POOL = ")
    b = html.find("/* ---------- Словосочетания по склонениям", a)
    if a < 0 or b < 0:
        raise SystemExit("could not locate DP_POOL/engine markers")
    html2 = html[:a] + payload + html[b:]
    for k in ("latAnat.v2", "latAnat.finalTest", "latAnat.krPrep", "latAnat.krLearn", "latAnat.lex2", "latAnat.phDecl"):
        if k not in html2:
            raise SystemExit("missing key " + k)
    html_path.write_text(html2, encoding="utf-8")
    print("index.html updated in place", html_path.stat().st_size)
    write_sw()
    raise SystemExit(0)

def one(old, new, label):
    global html
    n = html.count(old)
    if n != 1:
        raise SystemExit(f"patch {label}: expected 1 occurrence, got {n}\n---\n{old[:200]}")
    html = html.replace(old, new, 1)
    print("ok", label)

one(
    'SYNC_KEYS = ["latAnat.v2", "latAnat.finalTest", "latAnat.krPrep", "latAnat.krLearn", "latAnat.lex2"];',
    'SYNC_KEYS = ["latAnat.v2", "latAnat.finalTest", "latAnat.krPrep", "latAnat.krLearn", "latAnat.lex2", "latAnat.phDecl"];',
    "sync-keys",
)
one(
    'if (k === "latAnat.lex2") {',
    'if (k === "latAnat.lex2" || k === "latAnat.phDecl") {',
    "merge-phdecl",
)
one(
    ".kr-card .kl-l{width:auto;display:inline-flex}",
    ".kr-card .kl-l{width:auto;display:inline-flex}.ph-box{margin-top:10px;padding:10px 12px;border-radius:12px;background:var(--accent-soft,#eef6ff)}",
    "css",
)
one(
    '''    h += `</div><button class="btn ghost sm ft-btn" data-ft="${u.idx}">✍ Итоговый тест · ${u.list.length} ${plural(u.list.length, "слово", "слова", "слов")}${fb.lr || fb.rl ? ` <span class="muted">(лат→рус ${sc("lr")}, рус→лат ${sc("rl")})</span>` : ""}</button></div>`;''',
    '''    h += `</div><button class="btn ghost sm ft-btn" data-ft="${u.idx}">✍ Итоговый тест · ${u.list.length} ${plural(u.list.length, "слово", "слова", "слов")}${fb.lr || fb.rl ? ` <span class="muted">(лат→рус ${sc("lr")}, рус→лат ${sc("rl")})</span>` : ""}</button>`;
    if (u.id === "u1") h += dpUnitBtns(1);
    else if (u.id === "u2") h += dpUnitBtns(2);
    else if (u.id === "u3") h += dpUnitBtns(3);
    else if (u.id === "u4") h += dpUnitBtns(4) + dpUnitBtns(5);
    h += `</div>`;''',
    "unit-btns",
)
one(
    '''  $("#tab-learn").querySelectorAll("[data-l]").forEach(b => b.onclick = () => { const [a, c] = b.dataset.l.split(",").map(Number); startLesson(a, c); });
}''',
    '''  $("#tab-learn").querySelectorAll("[data-l]").forEach(b => b.onclick = () => { const [a, c] = b.dataset.l.split(",").map(Number); startLesson(a, c); });
  $("#tab-learn").querySelectorAll("[data-dp]").forEach(b => b.onclick = () => { const [d, act] = b.dataset.dp.split(","); startDp(+d, act); });
}''',
    "bind-dp",
)
one(
    '  if (!SES || $("#session").classList.contains("hidden")) return;',
    '  if ($("#session").classList.contains("hidden")) return;\n  if (!SES && !KS && !LS && !DS && !DT) return;',
    "keydown",
)
one(
    """load(); applyTheme(); render();
try { const w = window.Telegram && window.Telegram.WebApp; if (w && w.ready) w.ready(); } catch (e) {}""",
    """load(); applyTheme(); render();
try {
  const ph = parseInt(new URLSearchParams(location.search).get("ph") || "", 10);
  if (ph >= 1 && ph <= 5) startDp(ph, "lesson");
} catch (e) {}
try { const w = window.Telegram && window.Telegram.WebApp; if (w && w.ready) w.ready(); } catch (e) {}""",
    "deeplink",
)

payload = (
    "const DP_POOL = "
    + json.dumps(bundle["pool"], ensure_ascii=False, separators=(",", ":"))
    + ";\nconst DP_DATA = "
    + json.dumps(bundle["sec"], ensure_ascii=False, separators=(",", ":"))
    + ";\n"
    + engine
    + "\n"
)
marker = "/* ---------- keyboard (tablets with keyboards, desktops) ---------- */"
one(marker, payload + marker, "inject-engine")

# safety: old progress keys still present
for k in ("latAnat.v2", "latAnat.finalTest", "latAnat.krPrep", "latAnat.krLearn", "latAnat.lex2", "latAnat.phDecl"):
    if k not in html:
        raise SystemExit("missing key " + k)

html_path.write_text(html, encoding="utf-8")
print("index.html", html_path.stat().st_size)

sw = ROOT / "sw.js"
st = sw.read_text(encoding="utf-8")
write_sw()
