/* ---------- Словосочетания по склонениям (I–V): ① Урок → ② Тренировка → ③ Лист ---------- */
const DP_KEY = "latAnat.phDecl"; // новый ключ; latAnat.v2 / finalTest / krPrep / krLearn / lex2 не трогаем
function dpGet() { try { const d = JSON.parse(lsGet(DP_KEY) || "{}") || {}; return { l: d.l || {}, best: d.best || {} }; } catch (e) { return { l: {}, best: {} }; } }
function dpSet(d) { lsSet(DP_KEY, JSON.stringify(d)); }
function dpUnit(d) { return DP_DATA[String(d)]; }
function dpTyOk(s, val) {
  if (s.lat) return (s.alts || [s.a]).some(a => norm(a) === norm(val));
  return (s.alts || [s.a]).some(a => ruNorm(a) === ruNorm(val));
}
function dpDiagnose(s, val) {
  if (!s.lat) return "";
  const alts = s.alts || [s.a];
  if (dpTyOk(s, val)) return "";
  const got = norm(val).split(/\s+/).filter(Boolean);
  const exp = norm(alts[0]).split(/\s+/).filter(Boolean);
  const toks = s.tokens || [];
  if (!got.length) return "Напишите словосочетание целиком.";
  if (got.length !== exp.length) {
    return `Должно быть ${exp.length} ${plural(exp.length, "слово", "слова", "слов")}: первое — «что?» (Nom.), дальше — «чего?» (Gen.). Нужно: <span class="lat">${esc(alts[0])}</span>`;
  }
  const msgs = [];
  for (let i = 0; i < Math.max(got.length, toks.length, exp.length); i++) {
    const t = toks[i], g = got[i] || "", e = (t && t.form) ? norm(t.form) : (exp[i] || "");
    if (g === e || (t && t.forms && t.forms.some(x => norm(x) === g))) continue;
    if (!t) { msgs.push(`Слово ${i + 1}: нужно <b class="lat">${esc(exp[i] || alts[0])}</b>.`); continue; }
    const where = t.slot === "N" ? "главное слово, «что?»" : t.slot === "G" ? "зависимое слово, «чего?»" : "слово";
    msgs.push(`Слово ${i + 1} (${where}: ${esc(t.rus)} ← <span class="lat">${esc(t.dict)}</span>, ${t.d} скл.): нужно <b class="lat">${esc(t.form)}</b> — ${esc(t.fn)}, окончание <b>${esc(t.end)}</b>. Вы написали <span class="lat">${esc(got[i] || "—")}</span>.`);
  }
  return msgs.join(" ") || `Правильно: <span class="lat">${esc(alts[0])}</span>`;
}
function dpParseHtml(toks) {
  return (toks || []).map((t, j) => `<div>${j + 1}) <b class="lat">${esc(t.form)}</b> ← ${esc(t.dict)} (${esc(t.rus)}) — ${t.d} скл., ${t.slot === "N" ? "главное слово, «что?»" : t.slot === "G" ? "зависимое, «чего?»" : "определение"}: <b>${esc(t.fn)}</b>, окончание <b>${esc(t.end)}</b></div>`).join("");
}
function dpUnitBtns(d) {
  const U = dpUnit(d); if (!U) return "";
  const st = dpGet(), L = U.lessons, nd = L.filter(l => st.l[l.id]).length, nx = L.findIndex(l => !st.l[l.id]);
  const tr = st.l[U.id + "-tr"], br = st.best[d + "-rl"], bl = st.best[d + "-lr"];
  const sc = (x) => x ? `${x.ok}/${x.n}` : "—";
  const roman = { 1: "I", 2: "II", 3: "III", 4: "IV", 5: "V" }[d];
  return `<div class="ph-box" style="margin-top:10px">
    <div style="font-weight:650;font-size:.92rem">Словосочетания${d >= 4 ? ` · ${roman} скл.` : ""}</div>
    <div class="muted" style="font-size:.75rem;margin:2px 0 6px">${U.phrases.length} ${plural(U.phrases.length, "словосочетание", "словосочетания", "словосочетаний")}${U.warnN ? ` · ⚠ ${U.warnN}` : ""}</div>
    <div class="kl-steps" style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:6px">
      <button class="btn ghost sm" data-dp="${d},lesson">① Урок<br><small>${nd}/${L.length}${nx < 0 ? " ✓" : ""}</small></button>
      <button class="btn ghost sm" data-dp="${d},train">② Тренировка<br><small>${tr ? "×" + tr.n : "—"}</small></button>
      <button class="btn ghost sm" data-dp="${d},sheet">③ Лист<br><small>рус→лат ${sc(br)} · лат→рус ${sc(bl)}</small></button>
    </div></div>`;
}
function startDp(d, act) {
  DP_FOCUS = d;
  document.body.style.overflow = "hidden"; $("#session").classList.remove("hidden");
  if (act === "train") dpStart(d, -1);
  else if (act === "sheet") dpSheet(d, "rl");
  else dpMenu(d);
}
let DS = null, DT = null, DP_FOCUS = null;
function dpFrame(body, foot) {
  const pct = DS ? Math.min(100, DS.done / Math.max(1, DS.total) * 100) : 0;
  const focus = DS ? DS.d : (DT ? DT.d : DP_FOCUS);
  $("#session").innerHTML = `<div class="s-top"><button class="icon-btn" id="sClose" aria-label="Закрыть">${IC.x}</button>${DS ? `<div class="s-prog"><i style="width:${pct}%"></i></div>` : `<div class="ft-title">${esc((dpUnit(focus) || {}).title || "Словосочетания")}</div>`}</div><div class="s-body">${body}</div>${foot}`;
  $("#sClose").onclick = () => {
    if (DS && DS.done && !DS.fin && !confirm("Выйти из урока? Прогресс этого урока не сохранится.")) return;
    const onMenu = !DS && !DT;
    const d = DS ? DS.d : (DT ? DT.d : DP_FOCUS);
    DS = null; DT = null;
    if (onMenu || !d) { DP_FOCUS = null; closeSession(true); }
    else dpMenu(d);
  };
}
function dpMenu(d) {
  DP_FOCUS = d; DS = null; DT = null; const U = dpUnit(d), st = dpGet();
  const L = U.lessons, done = L.map(l => !!st.l[l.id]), nd = done.filter(Boolean).length, nx = done.indexOf(false), tr = st.l[U.id + "-tr"];
  const br = st.best[d + "-rl"], bl = st.best[d + "-lr"], sc = x => x ? `лучший: ${x.ok}/${x.n}` : "—";
  const cards = `<div class="card kr-card" style="padding:12px 14px;margin:10px 0"><div style="display:flex;justify-content:space-between;gap:8px;align-items:baseline"><b>① Урок</b><span class="muted" style="font-size:.8rem">${nd}/${L.length}${nx < 0 ? " ✓" : ""}</span></div>
    <div class="muted" style="font-size:.8rem">Короткие шаги: правило → разбор → задание. Ошибку игра покажет ещё раз через несколько вопросов.</div>
    <div style="margin-top:6px">${L.map((l, i) => `<button class="btn ${i === nx ? "" : "ghost"} kl-l dp-l" data-d="${d}" data-li="${i}" style="margin:3px 4px 3px 0;padding:6px 10px;font-size:.85rem">${done[i] ? "✓ " : ""}${esc(l.title)}</button>`).join("")}</div></div>
    <div class="card kr-card" style="padding:12px 14px;margin:10px 0"><b>② Тренировка</b><div class="muted" style="font-size:.8rem">Сначала рус → лат, затем лат → рус. Выбор, потом письмо; окончания строго.</div>
      <button class="btn ${nx < 0 ? "" : "ghost"}" id="dpTr" style="margin-top:8px">🔁 Тренировка${tr ? " · " + tr.n : ""}</button></div>
    <div class="card kr-card" style="padding:12px 14px;margin:10px 0"><b>③ Лист</b><div class="muted" style="font-size:.8rem">${U.phrases.length} ${plural(U.phrases.length, "словосочетание", "словосочетания", "словосочетаний")}. Заполните лист и отправьте целиком.</div>
      <div class="kl-steps" style="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:6px;margin-top:8px">
        <button class="btn ghost" id="dpRl">рус → лат<br><small>${sc(br)}</small></button>
        <button class="btn ghost" id="dpLr">лат → рус<br><small>${sc(bl)}</small></button></div></div>`;
  dpFrame(`<h2 class="ft-h">${esc(U.title)} · Словосочетания</h2><div class="hint">${U.hint}</div>${cards}`,
    `<div class="s-foot" id="foot"><div class="in"><button class="btn" id="dpHome">На главную</button></div></div>`);
  document.querySelectorAll(".dp-l").forEach(x => x.onclick = () => dpStart(+x.dataset.d, +x.dataset.li));
  $("#dpTr").onclick = () => dpStart(d, -1);
  $("#dpRl").onclick = () => dpSheet(d, "rl");
  $("#dpLr").onclick = () => dpSheet(d, "lr");
  $("#dpHome").onclick = () => { DS = null; DT = null; closeSession(true); };
}
function dpMakeTrain(d) {
  const U = dpUnit(d), ph = U.phrases.slice();
  const rl = shuffle(ph).slice(0, Math.min(8, ph.length));
  const lr = shuffle(ph).slice(0, Math.min(6, ph.length));
  const items = [];
  rl.forEach(p => items.push(dpPhItem(p, "rl", false)));
  lr.forEach(p => items.push(dpPhItem(p, "lr", false)));
  return items;
}
function dpPhItem(p, dir, full) {
  const st = [];
  if (full && dir === "rl") {
    (p.tokens || []).filter(t => t.slot === "N" || t.slot === "G").forEach(t => {
      const opts = [t.form].concat((t.distr || []).filter(x => x && x !== t.form)).slice(0, 4);
      while (opts.length < 2 && t.form) opts.push(t.form);
      st.push({ k: "ch", q: `«${esc(p.rus.split("|")[0])}» — ${t.slot === "N" ? "главное слово («что?»)" : "зависимое («чего?»)"}, ${esc(t.dict)}`, a: [t.form], o: opts, h: `${t.fn}, окончание ${t.end}`, lat: true });
    });
  }
  if (full && dir === "lr") {
    (p.tokens || []).filter(t => t.slot === "N" || t.slot === "G").slice(0, 2).forEach(t => {
      const fns = String(t.fn).split(" или ");
      st.push({ k: "ch", q: `<span class="lat">${esc(p.lat.split("|")[0])}</span> — <span class="lat">${esc(t.form)}</span>: какая форма?`, a: fns, o: fns.concat(["Nom. Sg.", "Gen. Sg.", "Nom. Pl.", "Gen. Pl."].filter(x => !fns.includes(x))).slice(0, 4), h: `${t.slot === "N" ? "Первое слово — «что?»" : "Второе слово — «чего?»"} (${t.rus})` });
    });
  }
  if (dir === "rl") st.push({ k: "ty", q: `<div class="prompt"><b style="font-size:1.35rem">${esc(p.rus.split("|")[0])}</b></div><div class="hint" style="text-align:center">Переведите на латынь</div>`, a: p.lat.split("|")[0], alts: p.lat.split("|"), lat: true, h: p.warn || "", tokens: p.tokens });
  else st.push({ k: "ty", q: `<div class="prompt"><span class="lat big">${esc(p.lat.split("|")[0])}</span></div><div class="hint" style="text-align:center">Переведите на русский</div>`, a: p.rus.split("|")[0], alts: p.rus.split("|"), lat: false, h: "" });
  return { id: p.id + "-" + dir, ans: dir === "rl" ? `${esc(p.rus.split("|")[0])} — <span class="lat">${esc(p.lat.split("|")[0])}</span>` : `<span class="lat">${esc(p.lat.split("|")[0])}</span> — ${esc(p.rus.split("|")[0])}`, parse: dpParseHtml(p.tokens), st };
}
function dpStart(d, li) {
  const U = dpUnit(d), train = li < 0, src = train ? dpMakeTrain(d) : U.lessons[li].items;
  const items = src.map(x => ({ x, st: x.th ? [{ k: "in" }] : x.st, i: 0, ready: 0, miss: 0 }));
  DS = { d, li, train, lid: train ? U.id + "-tr" : U.lessons[li].id, title: `${U.title} · ${train ? "тренировка" : U.lessons[li].title}`, items, step: -1, last: null, mist: 0, ans: 0, first: 0, done: 0, wrong: new Set(), t0: Date.now(), fin: false };
  DS.total = items.reduce((a, it) => a + it.st.length, 0);
  $("#session").classList.remove("hidden"); document.body.style.overflow = "hidden";
  dpNext();
}
function dpPick() {
  const open = DS.items.filter(it => !it.done); if (!open.length) return null;
  const notLast = open.filter(it => it !== DS.last);
  const th = open.find(it => it.x.th); if (th) return th;
  const ready = notLast.filter(it => it.i > 0 && it.ready <= DS.step).sort((a, b) => a.ready - b.ready); if (ready.length) return ready[0];
  const fresh = notLast.filter(it => it.i === 0); if (fresh.length) return fresh[0];
  return notLast.sort((a, b) => a.ready - b.ready)[0] || open[0];
}
function dpNext() {
  if (!DS) return; DS.step++;
  const it = dpPick(); if (!it) return dpFinish();
  DS.cur = it; DS.last = it;
  const s = it.st[it.i], x = it.x, lbl = it.retry ? "Ещё раз" : DS.train ? "Тренировка" : "Урок";
  const adv = () => { it.i++; it.ready = DS.step + 1; DS.done++; if (it.i >= it.st.length) it.done = true; dpNext(); };
  if (s.k === "in") {
    dpFrame(`<div class="q-kind">Урок</div><div class="card intro kl-intro">${x.intro}</div>`, `<div class="s-foot" id="foot"><div class="in"><button class="btn" id="contBtn">Понятно</button></div></div>`);
    $("#contBtn").onclick = adv; return;
  }
  if (s.k === "ch") {
    const opts = shuffle(s.o.slice());
    dpFrame(`<div class="q-kind">${lbl}</div><h2 class="q-title">${s.q}</h2><div class="opts two" id="opts">${opts.map((o, i) => `<button class="opt ${s.lat ? "lat-opt" : ""}" data-i="${i}"><span class="k">${i + 1}</span><span>${esc(o)}</span></button>`).join("")}</div>`,
      `<div class="s-foot" id="foot"><div class="in">${s.h ? `<button class="btn ghost" id="hintBtn">💡 Подсказка</button><div class="hint" id="hintTxt" style="display:none;text-align:center">${s.h}</div>` : `<div class="hint" style="text-align:center">Выберите вариант</div>`}</div></div>`);
    const hb = $("#hintBtn"); if (hb) hb.onclick = () => { hb.style.display = "none"; $("#hintTxt").style.display = ""; };
    const box = $("#opts");
    box.querySelectorAll(".opt").forEach(b => b.onclick = () => {
      if (box.classList.contains("locked")) return; box.classList.add("locked");
      const ok = s.a.includes(opts[+b.dataset.i]);
      box.querySelectorAll(".opt").forEach((y, i) => { if (s.a.includes(opts[i])) y.classList.add("right"); else if (y === b) y.classList.add("wrong"); else y.classList.add("dim"); });
      dpFeedback(ok, `<b>${esc(s.a[0])}</b>${s.h ? `<div class="hint">${s.h}</div>` : ""}`);
    });
    return;
  }
  dpFrame(`<div class="q-kind">${lbl} · письмо</div><h2 class="q-title">Напишите ответ</h2>${s.q}<div class="type-wrap"><input class="type-in" id="tin" type="text" ${s.lat ? 'lang="la"' : 'lang="ru"'} autocomplete="off" autocorrect="off" autocapitalize="off" spellcheck="false" enterkeyhint="done">${s.h ? `<div class="hint">${s.h}</div>` : ""}</div>`, footCheck());
  const inp = $("#tin"), cb = $("#checkBtn"); setTimeout(() => inp.focus(), 60);
  inp.oninput = () => cb.disabled = !inp.value.trim();
  const check = skip => { if (inp.readOnly) return; inp.readOnly = true; const ok = !skip && dpTyOk(s, inp.value); inp.classList.add(ok ? "right" : "wrong"); inp.blur();
    dpFeedback(ok, `<b class="${s.lat ? "lat" : ""}">${esc(s.a)}</b>${!ok && s.lat ? `<div class="hint">${dpDiagnose(s, inp.value)}</div>` : ""}${x.parse && !ok ? `<div class="kl-parse" style="margin-top:6px">${x.parse}</div>` : ""}`); };
  cb.onclick = () => check(false); $("#skipBtn").onclick = () => check(true);
  inp.onkeydown = e => { if (e.key === "Enter" && inp.value.trim()) { e.preventDefault(); e.stopPropagation(); check(false); } };
}
function dpFeedback(ok, html) {
  const it = DS.cur; DS.ans++;
  if (ok) { DS.done++; if (!it.retry) DS.first++; it.i++; it.retry = false; it.ready = DS.step + 2; if (it.i >= it.st.length) it.done = true; }
  else { DS.mist++; it.miss++; it.retry = true; it.ready = DS.step + 3; DS.total++; DS.wrong.add(it.x); }
  const foot = $("#foot"); foot.className = "s-foot " + (ok ? "ok" : "bad");
  foot.innerHTML = `<div class="in"><div class="fb"><div class="ic">${ok ? IC.check : IC.x}</div><div><b>${ok ? sample(["Верно", "Отлично", "Правильно"], 1)[0] : "Неверно"}</b><div class="ans">${html}</div></div></div>
    <button class="btn ${ok ? "" : "bad"}" id="contBtn">Дальше</button></div>`;
  const c = $("#contBtn"); c.onclick = dpNext; c.focus({ preventScroll: true });
}
function dpFinish() {
  DS.fin = true; const d = dpGet(), o = d.l[DS.lid]; d.l[DS.lid] = { n: (o ? o.n : 0) + 1, at: Date.now() }; dpSet(d);
  const U = dpUnit(DS.d), nx = DS.train ? -1 : U.lessons.findIndex(l => !d.l[l.id]);
  const acc = DS.ans ? Math.round(DS.first / DS.ans * 100) : 100, wrong = [...DS.wrong], decl = DS.d;
  dpFrame(`<div class="done"><div class="seal">${IC.check}</div><h2>${DS.train ? "Тренировка завершена" : "Урок пройден"}</h2><p>${esc(DS.title)}</p>
    <div class="done-stats"><div class="card stat"><b>${acc}%</b><span>с первого раза</span></div><div class="card stat"><b>${DS.mist}</b><span>ошибок</span></div></div>
    ${wrong.length ? `<div class="card" style="width:100%;max-width:520px;text-align:left;padding:10px 14px"><div class="hint">Было трудно — повторите:</div>${wrong.map(x => `<div style="margin:4px 0">${x.ans || ""}</div>`).join("")}</div>` : ""}</div>`,
    `<div class="s-foot" id="foot"><div class="in"><div class="row2"><button class="btn ghost" id="dpMenuB">К разделу</button>${nx >= 0 ? `<button class="btn" id="dpNx">Следующий урок</button>` : `<button class="btn" id="dpTr2">Тренировка</button>`}</div></div></div>`);
  $("#dpMenuB").onclick = () => { DS = null; dpMenu(decl); };
  const n = $("#dpNx"); if (n) n.onclick = () => dpStart(decl, nx);
  const t = $("#dpTr2"); if (t) t.onclick = () => dpStart(decl, -1);
}
function dpSheet(d, kind, rows) {
  const U = dpUnit(d);
  if (!rows) rows = U.phrases.slice();
  DT = { d, kind, rows, retry: !!(DT && DT.d === d && DT.kind === kind && rows === DT.wrong), checked: false };
  const rl = kind === "rl";
  const html = rows.map((p, i) => `<div class="ft-row" id="dpr${i}"><div class="ft-q ${rl ? "" : "lat"}">${esc(rl ? p.rus.split("|")[0] : p.lat.split("|")[0])}${p.warn ? `<div class="muted" style="font-size:.75rem;font-weight:400">⚠ ${esc(p.warn)}</div>` : ""}</div>
    <div class="ft-a"><input class="ft-in" data-i="${i}" type="text" ${rl ? 'lang="la"' : 'lang="ru"'} autocomplete="off" autocorrect="off" autocapitalize="off" spellcheck="false" aria-label="Ответ ${i + 1}"><div class="ft-fix"></div></div></div>`).join("");
  DS = null;
  dpFrame(`<h2 class="ft-h">${esc(U.title)} · лист · ${rl ? "русский → латынь" : "латынь → русский"}${DT.retry ? " · ошибки" : ""}</h2>
    <div class="hint">${rows.length} ${plural(rows.length, "строка", "строки", "строк")}. Окончания проверяются строго. Заполните лист и отправьте целиком.</div><div class="card ft-sheet">${html}</div>`,
    `<div class="s-foot" id="foot"><div class="in"><div class="row2"><button class="btn ghost" id="dpBack">К разделу</button><button class="btn" id="dpSend">Отправить на проверку</button></div></div></div>`);
  const ins = [...document.querySelectorAll("#session input.ft-in")];
  ins.forEach((inp, i) => inp.onkeydown = e => { if (e.key === "Enter") { e.preventDefault(); e.stopPropagation(); if (ins[i + 1]) ins[i + 1].focus(); else inp.blur(); } });
  $("#dpBack").onclick = () => { if (ins.some(i => i.value.trim()) && !DT.checked && !confirm("Вернуться? Ответы не сохранятся.")) return; dpMenu(d); };
  $("#dpSend").onclick = () => { const empty = ins.filter(i => !i.value.trim()).length; if (empty && !confirm(`Незаполненных строк: ${empty}. Всё равно отправить?`)) return; dpCheckSheet(ins); };
}
function dpCheckSheet(ins) {
  const rl = DT.kind === "rl", wrong = []; let ok = 0;
  ins.forEach((inp, i) => {
    const p = DT.rows[i], good = rl ? p.lat.split("|").some(a => norm(a) === norm(inp.value)) : p.rus.split("|").some(a => ruNorm(a) === ruNorm(inp.value));
    const row = $("#dpr" + i); row.classList.add(good ? "ok" : "bad"); inp.readOnly = true;
    if (good) ok++; else {
      wrong.push(p);
      const msg = rl ? dpDiagnose({ lat: true, a: p.lat.split("|")[0], alts: p.lat.split("|"), tokens: p.tokens }, inp.value) : "";
      row.querySelector(".ft-fix").innerHTML = `${IC.x} <b class="${rl ? "lat" : ""}">${esc(rl ? p.lat.split("|").join(" / ") : p.rus.split("|").join(" / "))}</b>${msg ? `<div class="hint">${msg}</div>` : ""}`;
    }
  });
  DT.checked = true; DT.wrong = wrong; const n = DT.rows.length, key = DT.d + "-" + DT.kind;
  if (!DT.retry) { const d = dpGet(), o = d.best[key]; if (!o || ok / n > o.ok / o.n) d.best[key] = { ok, n }; const k = "sheet-" + key, c = d.l[k]; d.l[k] = { n: (c ? c.n : 0) + 1, at: Date.now() }; dpSet(d); }
  const best = dpGet().best[key];
  $("#session .ft-h").insertAdjacentHTML("afterend", `<div class="card ft-score ${ok === n ? "ok" : ""}"><b>${ok} / ${n}</b><span>${ok === n ? "Без ошибок!" : `ошибок: ${n - ok}`}${best ? ` · лучший результат: ${best.ok}/${best.n}` : ""}</span></div>`);
  const decl = DT.d, kind = DT.kind;
  $("#foot .in").innerHTML = `<div class="row2">${wrong.length ? `<button class="btn ghost" id="dpRetry">${IC.repeat} Повторить ошибки</button>` : ""}
    ${kind === "rl" ? `<button class="btn" id="dpNextSh">Дальше: латынь → русский</button>` : `<button class="btn" id="dpDoneSh">Готово</button>`}</div>`;
  $("#session .s-body").scrollTop = 0;
  const rr = $("#dpRetry"); if (rr) rr.onclick = () => dpSheet(decl, kind, DT.wrong);
  const nx = $("#dpNextSh"); if (nx) nx.onclick = () => { DT = null; dpSheet(decl, "lr"); };
  const dn = $("#dpDoneSh"); if (dn) dn.onclick = () => { DT = null; dpMenu(decl); };
}

(function dpHydrate() {
  if (!window.DP_DATA || DP_DATA._hydrated) return;
  const pool = window.DP_POOL || (DP_DATA.pool || {});
  const sec = DP_DATA.sec || DP_DATA;
  if (DP_DATA.sec) {
    window.DP_POOL = pool;
    Object.keys(sec).forEach(k => { DP_DATA[k] = sec[k]; });
  }
  Object.keys(DP_DATA).forEach(d => {
    if (d === "pool" || d === "sec" || d === "_hydrated") return;
    const U = DP_DATA[d];
    if (!U || typeof U !== "object") return;
    if (U.pids && !Array.isArray(U.phrases)) U.phrases = U.pids.map(id => (window.DP_POOL || {})[id]).filter(Boolean);
    if (Array.isArray(U.lessons)) {
      U.lessons = U.lessons.map(les => ({
        id: les.id, title: les.title,
        items: (les.items || []).map(it => it && it.p ? dpPhItem((window.DP_POOL || {})[it.p], it.dir || "rl", !!it.full) : it).filter(Boolean)
      }));
    }
  });
  DP_DATA._hydrated = true;
})();
