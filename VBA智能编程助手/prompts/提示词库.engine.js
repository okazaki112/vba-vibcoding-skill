/* ════════════════════════════════════════════════════════════
   引擎 —— 渲染与交互，本文件日常不用修改。
   数据层在 提示词库.store.js：页面增删改 → localStorage；「存为文件」落盘。
   ════════════════════════════════════════════════════════════ */
(function () {
  var PL = window.PL;
  var $ = function (id) { return document.getElementById(id); };
  var esc = function (s) { var d = document.createElement("div"); d.textContent = s == null ? "" : String(s); return d.innerHTML; };
  if (!PL) { $("dataWarn").textContent = "缺少 提示词库.store.js —— 请确认五个模板文件在同一文件夹。"; $("dataWarn").classList.remove("hidden"); return; }

  var SITE = PL.SITE, OVERVIEW = PL.OVERVIEW;
  var P = function () { return PL.live(); };
  var CATS = function () { return PL.cats().CATS; };
  var CATLIST = function () { return PL.cats().CATLIST; };
  var catColor = function (k) { return CATS()[k] ? CATS()[k].color : "var(--accent)"; };
  var catName = function (k) { return CATS()[k] ? CATS()[k].name : k; };
  var catNum = function (k) { return CATS()[k] ? CATS()[k].num : "--"; };
  var state = { view: "overview", filter: "all", q: "", code: null };

  /* ---- toast ---- */
  var toastTimer = null;
  function toast(msg, bad) {
    var t = $("toast");
    if (!t) { t = document.createElement("div"); t.id = "toast"; t.className = "toast"; document.body.appendChild(t); }
    t.textContent = msg; t.classList.toggle("bad", !!bad); t.classList.add("show");
    clearTimeout(toastTimer); toastTimer = setTimeout(function () { t.classList.remove("show"); }, 2800);
  }

  /* ---- 内容红线引擎（词面 \u 转义拆写，防自指命中；定义源 prompt_library.md §4）---- */
  var LB2 = "{" + "{", RB2 = "}" + "}";
  var SLOT_L = "\u3010", SLOT_R = "\u3011";
  var SLOT_RE = new RegExp("[" + SLOT_L + "][^" + SLOT_R + "]{1,12}[" + SLOT_R + "]");
  var MARKER = "\u9aa8" + "\u67b6\u5f85\u751f\u6210";              /* 骨架未定制标记（槽位扫描豁免，单独拦） */
  var BANNED = [LB2, RB2,
    "\u586b" + "\u7a7a",                                            /* 禁词 A */
    "\u6b64" + "\u5904\u586b\u5199",                              /* 禁词 B */
    "\u865a" + "\u6784",                                            /* 禁词 C */
    "\u5360" + "\u4f4d\u6f14\u793a",                              /* 禁词 D */
    "\u5047" + "\u97f3\u6548\u96c6",                              /* 禁词 E */
    "\u5047" + "\u6570\u636e\u96c6",                              /* 禁词 F */
    "\u5047" + "\u6570\u636e",                                     /* 禁词 G */
    "\u6a21" + "\u62df\u6570\u636e",                              /* 禁词 H */
    "\u6a21" + "\u62df\u5185\u5bb9",                              /* 禁词 I */
    "\u793a" + "\u4f8b"];                                           /* 禁词 J */
  var PROMPT_HEAD = /^使用「[^「」\r\n]+」skill[。.]?$/;
  var PROMPT_FIELDS = ["任务", "要求", "输出"];
  var PROMPT_LENGTH_WARNING = 300;
  function bannedHit(s, exemptMarker) {
    for (var bi = 0; bi < BANNED.length; bi++) { if (s.indexOf(BANNED[bi]) >= 0) return BANNED[bi]; }
    var mm = s.match(SLOT_RE);
    if (mm && exemptMarker && mm[0].indexOf(MARKER) === 1) return "";
    return mm ? mm[0] : "";
  }

  /* ---- 自检 ---- */
  function validate() {
    var errs = PL.bootErr.slice(), notes = [], seen = {};
    if (!P().length) errs.push("库里没有条目了：点「＋ 新增」添加，或「重置」从文件恢复");
    P().forEach(function (it, i) {
      var tag = "#" + i + " (" + (it.code || "?") + ")";
      ["code", "title", "scene", "prompt"].forEach(function (f) { if (!it[f]) errs.push(tag + " 缺字段 " + f); });
      if (!Array.isArray(it.tags)) errs.push(tag + " tags 必须是数组");
      if (seen[it.code]) errs.push(tag + " code 与条目 #" + seen[it.code] + " 重复"); else seen[it.code] = i;
      var s5 = String(it.code || "") + it.cat + it.title + it.scene + it.prompt;
      var hit5 = bannedHit(s5, true);
      if (hit5) errs.push(tag + " 命中内容红线词面「" + hit5 + "」（槽位/禁锚点）");
      var prm = String(it.prompt || "");
      if (prm.indexOf(MARKER) >= 0) errs.push(tag + " 条目未定制：消除全角括号标记、代入真实正文后才可分发");
      if (prm) {
        if (!PROMPT_HEAD.test(prm.trim().split(/\r?\n/)[0])) errs.push(tag + " 首行应为短调用句：使用「本 Skill 名」skill。");
        PROMPT_FIELDS.forEach(function (field) {
          if (!new RegExp("^" + field + "[：:][^\\S\\r\\n]*\\S[^\\r\\n]*$", "m").test(prm)) errs.push(tag + " 缺少或未填写结构项：" + field);
        });
        var length = Array.from(prm.trim()).length;
        if (length > PROMPT_LENGTH_WARNING) notes.push(tag + " 超过 " + PROMPT_LENGTH_WARNING + " 字符（" + length + "），建议精简重复说明，保留必要约束");
      }
    });
    var box = $("dataWarn");
    if (errs.length || notes.length) {
      box.textContent = (errs.length ? "数据自检未通过（" + errs.length + " 处）" : "提示词精简建议") + "：\n" + errs.concat(notes).slice(0, 20).join("\n");
      box.classList.remove("hidden");
    } else box.classList.add("hidden");
  }

  /* ---- 视图 ---- */
  function goLib() { state.view = "lib"; $("view-overview").classList.add("hidden"); $("view-lib").classList.remove("hidden"); document.body.classList.add("lib-mode"); syncTabs(); }
  function goOverview() { state.view = "overview"; $("view-lib").classList.add("hidden"); $("view-overview").classList.remove("hidden"); document.body.classList.remove("lib-mode"); syncTabs(); }
  function syncTabs() {
    var mk = function (id, label, count) {
      var active = id === "method" ? state.view === "overview" : state.view === "lib" && state.filter === id;
      return '<button class="tab' + (active ? " active" : "") + '" data-tab="' + id + '"><span>' + esc(label) + "</span>" + (count != null ? '<span class="toc-count">' + count + "</span>" : "") + "</button>";
    };
    var nonEmpty = function (c) { return P().some(function (p) { return p.cat === c.key; }); };
    $("tabs").innerHTML = (OVERVIEW ? mk("method", "00 概览", null) : "") + mk("all", "全部", P().length) +
      CATLIST().filter(nonEmpty).map(function (c) { return mk(c.key, c.num + " " + c.name, P().filter(function (p) { return p.cat === c.key; }).length); }).join("");
  }
  function visibleItems() {
    var q = state.q.trim().toLowerCase();
    if (q) return P().filter(function (it) { return [it.code, it.title, (it.tags || []).join(" "), it.scene, it.prompt].join("\n").toLowerCase().indexOf(q) !== -1; });
    if (state.filter === "all") return P().slice();
    return P().filter(function (it) { return it.cat === state.filter; });
  }
  function renderList() {
    var items = visibleItems(), q = state.q.trim();
    var html = '<div class="li-title-row">' + (q ? "搜索命中 " + items.length + " 条" : (state.filter === "all" ? "全部" : catName(state.filter)) + " · " + items.length + " 条") + "</div>";
    if (!items.length) html += '<div class="li-empty">没有命中，换个关键词或新增一条</div>';
    html += items.map(function (it) {
      return '<button class="li-item' + (it.code === state.code ? " active" : "") + '" style="--c:' + catColor(it.cat) + '" data-code="' + esc(it.code) + '" role="option">' +
        '<span class="li-code">' + esc(it.code) + '</span><span class="li-name">' + esc(it.title) + '</span><span class="li-chapter">' + esc(catName(it.cat)) + "</span></button>";
    }).join("");
    $("libList").innerHTML = html;
    return items;
  }
  function renderDetail(items) {
    var it = items.filter(function (i) { return i.code === state.code; })[0] || items[0];
    if (!it) { $("libDetail").innerHTML = '<div class="detail-empty">← 从左侧列表选择一条，或点左下「＋ 新增」</div>'; return; }
    state.code = it.code;
    var idx = items.indexOf(it), prev = items[idx - 1], next = items[idx + 1];
    $("libDetail").innerHTML = '<div class="detail" style="--c:' + catColor(it.cat) + '">' +
      '<div class="detail-head"><div class="dh-line1"><span class="pc-code">' + esc(it.code) + '</span><span class="li-chapter">' + catNum(it.cat) + " " + esc(catName(it.cat)) + "</span>" +
      '<span class="pc-tags">' + (it.tags || []).map(function (t) { return '<span class="tag">' + esc(t) + "</span>"; }).join("") + "</span></div>" +
      '<h3 class="detail-title">' + esc(it.title) + "</h3>" +
      '<div class="dh-actions"><button class="copy-btn big" data-code="' + esc(it.code) + '"><svg viewBox="0 0 24 24" fill="none"><rect x="9" y="9" width="11" height="11" rx="2.5" stroke="currentColor" stroke-width="1.8"/><path d="M5 15V6a2 2 0 012-2h9" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg><span>复制这条提示词</span></button>' +
      '<button class="btn edit" data-edit="' + esc(it.code) + '">✎ 编辑</button><button class="btn del" data-del="' + esc(it.code) + '">删除</button>' +
      '<span class="detail-nav">' + (prev ? '<button class="nav-btn" data-nav="' + esc(prev.code) + '">← ' + esc(prev.code) + "</button>" : "") +
      (next ? '<button class="nav-btn" data-nav="' + esc(next.code) + '">' + esc(next.code) + " →</button>" : "") + "</span></div></div>" +
      '<p class="pc-scene"><b>用法 · </b>' + esc(it.scene) + "</p>" +
      '<pre class="detail-pre">' + esc(it.prompt) + "</pre>" +
      '<p class="pc-note">改动保存在浏览器本地；点左下「存为文件」可写回 提示词库.data.js 落盘。</p></div>';
    $("libDetail").scrollTop = 0;
  }
  function select(code, syncHash) {
    state.code = code;
    var items = visibleItems();
    if (!items.some(function (i) { return i.code === code; })) { state.q = ""; state.filter = "all"; $("searchInput").value = ""; items = visibleItems(); }
    renderList(); renderDetail(items);
    if (syncHash !== false) { try { history.replaceState(null, "", "#" + code); } catch (e) {} }
    var el = document.querySelector('.li-item[data-code="' + code + '"]');
    if (el) el.scrollIntoView({ block: "nearest" });
    if (window.innerWidth <= 960 && $("libDetail")) $("libDetail").scrollIntoView({ behavior: "auto", block: "start" });
  }
  function renderAll() { validate(); syncTabs(); renderList(); renderDetail(visibleItems()); renderOverview(); }

  /* ---- 列表/详情事件 ---- */
  $("libList").addEventListener("click", function (ev) { var li = ev.target.closest(".li-item"); if (li) select(li.dataset.code); });
  $("libDetail").addEventListener("click", function (ev) {
    var n = ev.target.closest(".nav-btn"); if (n) { select(n.dataset.nav); return; }
    var e2 = ev.target.closest("[data-edit]"); if (e2) { var it = P().filter(function (x) { return x.code === e2.dataset.edit; })[0]; if (it) openModal(it, "edit"); return; }
    var d2 = ev.target.closest("[data-del]");
    if (d2) {
      var target = d2.dataset.del;
      if (!confirm("确定删除「" + target + "」？（删的是本地库数据，可用「重置」从文件恢复）")) return;
      var r = PL.remove(target);
      if (r.err) toast(r.err, true); else { toast("已删除 " + r.name); if (state.code === target) state.code = null; renderAll(); }
      return;
    }
    var b = ev.target.closest(".copy-btn");
    if (b) { var cp = P().filter(function (i) { return i.code === b.dataset.code; })[0]; if (cp) copyText(cp.prompt, b, "复制这条提示词"); }
  });
  $("tabs").addEventListener("click", function (ev) {
    var btn = ev.target.closest(".tab"); if (!btn) return;
    var id = btn.dataset.tab;
    if (id === "method") { goOverview(); return; }
    state.filter = id; goLib();
    var items = visibleItems();
    if (!items.some(function (i) { return i.code === state.code; })) state.code = items.length ? items[0].code : null;
    renderList(); renderDetail(items); syncTabs();
  });

  /* ---- 复制 ---- */
  function legacyCopy(text, cb) {
    var ta = document.createElement("textarea"); ta.value = text; ta.style.position = "fixed"; ta.style.opacity = "0";
    document.body.appendChild(ta); ta.select();
    try { document.execCommand("copy"); cb(true); } catch (e) { cb(false); }
    document.body.removeChild(ta);
  }
  function copyText(text, btn, label) {
    var done = function (ok) {
      var sp = btn.querySelector("span");
      btn.classList.toggle("ok", ok);
      if (sp) sp.textContent = ok ? "已复制 ✓" : "复制失败"; else btn.textContent = ok ? "已复制 ✓" : "复制失败";
      setTimeout(function () { btn.classList.remove("ok"); if (sp) sp.textContent = label; else btn.textContent = label; }, 1800);
    };
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(text).then(function () { done(true); }, function () { legacyCopy(text, done); });
    else legacyCopy(text, done);
  }

  /* ---- 搜索 + 键盘 ---- */
  $("searchInput").addEventListener("input", function () {
    state.q = this.value; goLib();
    var items = visibleItems();
    if (!items.some(function (i) { return i.code === state.code; })) state.code = items.length ? items[0].code : null;
    renderList(); renderDetail(items);
  });
  document.addEventListener("keydown", function (ev) {
    if (ev.key === "Escape" && !$("modalVeil").classList.contains("hidden")) { closeModal(); return; }
    if (document.activeElement && document.activeElement.closest && document.activeElement.closest(".modal")) return;
    if (ev.key === "/" && document.activeElement !== $("searchInput")) { ev.preventDefault(); $("searchInput").focus(); return; }
    if (document.activeElement === $("searchInput")) return;
    if (state.view !== "lib" || (ev.key !== "ArrowDown" && ev.key !== "ArrowUp")) return;
    ev.preventDefault();
    var items = visibleItems(); if (!items.length) return;
    var idx = items.map(function (i) { return i.code; }).indexOf(state.code);
    var ni = ev.key === "ArrowDown" ? Math.min(items.length - 1, idx + 1) : Math.max(0, idx - 1);
    if (items[ni]) select(items[ni].code);
  });

  /* ---- 弹窗（新增/编辑/草稿/备份）---- */
  var DRAFT_KEY = "prompt-lib-drafts-v1:" + encodeURIComponent(SITE.name || "untitled");
  var loadDrafts = function () { try { return JSON.parse(localStorage.getItem(DRAFT_KEY) || "[]"); } catch (e) { return []; } };
  var saveDrafts = function (a) { try { localStorage.setItem(DRAFT_KEY, JSON.stringify(a)); } catch (e) {} };
  var F = function (id) { return $(id); };
  var mode = "add", oldCode = null;
  function formItem() {
    return { code: F("fCode").value.trim(), cat: F("fCat").value.trim(), title: F("fTitle").value.trim(),
      tags: F("fTags").value.split(/[,，]/).map(function (s) { return s.trim(); }).filter(Boolean),
      scene: F("fScene").value.trim(), prompt: F("fPrompt").value };
  }
  var jstr = function (s) { return JSON.stringify(s == null ? "" : String(s)); };
  function genCode(it) {
    var body = String(it.prompt || "").replace(/\\/g, "\\\\").replace(/`/g, "\\`").replace(/\$\{/g, "\\${");
    return "  {\n    code: " + jstr(it.code) + ", cat: " + jstr(it.cat || "misc") + ", title: " + jstr(it.title) + ",\n    tags: [" + (it.tags || []).map(jstr).join(", ") + "],\n    scene: " + jstr(it.scene) + ",\n    prompt: `" + body + "`\n  },";
  }
  function refreshGen() {
    var it = formItem();
    F("genPre").textContent = (it.title || it.prompt) ? genCode(it) : "填表后这里实时生成…";
  }
  function renderDrafts() {
    var ds = loadDrafts();
    F("draftCount").textContent = ds.length ? "(" + ds.length + ")" : "";
    var badge = F("draftBadge");
    badge.textContent = ds.length; badge.classList.toggle("hidden", !ds.length);
    F("draftList").innerHTML = ds.length ? ds.map(function (d, i) {
      return '<div class="draft-item"><span class="d-code">' + esc(d.item.code || "—") + '</span><span class="d-title">' + esc(d.item.title || "(无标题)") + "</span>" +
        '<button data-di="' + i + '" data-da="load">载入</button><button data-di="' + i + '" data-da="copy">复制代码</button><button class="del" data-di="' + i + '" data-da="del">删</button></div>';
    }).join("") : '<div class="draft-empty">暂无草稿。没填完可「存草稿」，下次打开继续。</div>';
    var dl = F("catList");
    if (dl) dl.innerHTML = CATLIST().map(function (c) { return '<option value="' + esc(c.key) + '">'; }).join("");
  }
  function fillForm(it) {
    F("fCode").value = it.code || ""; F("fCat").value = it.cat && it.cat !== "_none" ? it.cat : ""; F("fTitle").value = it.title || "";
    F("fTags").value = (it.tags || []).join(", "); F("fScene").value = it.scene || ""; F("fPrompt").value = it.prompt || "";
    refreshGen();
  }
  function openModal(item, m) {
    mode = m || "add"; oldCode = item ? item.code : null;
    F("mTitle").textContent = mode === "edit" ? "✎ 编辑 " + item.code : "＋ 新增提示词";
    F("mSave").textContent = mode === "edit" ? "保存修改" : "保存到库";
    fillForm(item || { tags: [], prompt: "" });
    $("modalVeil").classList.remove("hidden"); renderDrafts(); F("fCode").focus();
  }
  function closeModal() { $("modalVeil").classList.add("hidden"); }
  ["fCode", "fCat", "fTitle", "fTags", "fScene", "fPrompt"].forEach(function (id) { F(id).addEventListener("input", refreshGen); });
  F("addBtn").addEventListener("click", function () { openModal(null, "add"); });
  F("mClose").addEventListener("click", closeModal);
  $("modalVeil").addEventListener("click", function (ev) { if (ev.target === $("modalVeil")) closeModal(); });
  F("mSave").addEventListener("click", function () {
    var it = formItem();
    if (!it.title && !it.prompt) { toast("至少填写标题和全文", true); return; }
    var r = PL.upsert(it, oldCode);
    if (r.err) { toast(r.err, true); return; }
    closeModal(); renderAll(); select(r.code);
    toast(mode === "edit" ? "已保存修改：" + r.code : "已入库：" + r.code + "（想写回文件请点「存为文件」）");
  });
  F("mDraft").addEventListener("click", function () {
    var it = formItem(); if (!it.title && !it.prompt) return;
    var ds = loadDrafts(); ds.unshift({ t: Date.now(), item: it }); saveDrafts(ds.slice(0, 30)); renderDrafts(); toast("草稿已存");
  });
  F("mClear").addEventListener("click", function () { fillForm({ tags: [], prompt: "" }); });
  F("mCopy").addEventListener("click", function () {
    var it = formItem();
    if (!it.title && !it.prompt) { F("genPre").textContent = "请先至少填写 标题 与 全文，再复制。"; return; }
    copyText(genCode(it), F("mCopy"), "复制这段代码");
  });
  F("draftList").addEventListener("click", function (ev) {
    var b = ev.target.closest("button"); if (!b) return;
    var ds = loadDrafts(), i = +b.dataset.di; if (!ds[i]) return;
    if (b.dataset.da === "load") fillForm(ds[i].item);
    else if (b.dataset.da === "copy") copyText(genCode(ds[i].item), b, "复制代码");
    else { ds.splice(i, 1); saveDrafts(ds); renderDrafts(); }
  });
  F("mBackup").addEventListener("click", function () { PL.backupJson(); toast("备份 JSON 已下载"); });
  F("mRestore").addEventListener("click", function () { F("mRestoreFile").click(); });
  F("mRestoreFile").addEventListener("change", function () {
    var f = this.files && this.files[0]; if (!f) return;
    PL.restoreJson(f, function (res) {
      if (res.err) toast(res.err, true);
      else { renderAll(); closeModal(); toast("已恢复 " + res.n + " 条（记得点「存为文件」落盘）"); }
    });
    this.value = "";
  });

  /* ---- 侧栏：存为文件 / 重置 ---- */
  F("saveFileBtn").addEventListener("click", function () {
    PL.saveToDataFile(function (r) {
      if (r === "saved") toast("已写回 提示词库.data.js ✓");
      else if (r === "downloaded") toast("浏览器禁止页面直写文件：已下载新版 提示词库.data.js，替换同名旧文件即完成落盘");
    });
  });
  F("resetBtn").addEventListener("click", function () {
    if (!confirm("重置 = 丢弃页面上的全部增删改，恢复为 提示词库.data.js 文件内容。确定？")) return;
    PL.resetToSeed(); state.code = null; renderAll(); toast("已重置为文件数据");
  });

  /* ---- 概览页 ---- */
  function renderOverview() {
    $("brandName").textContent = SITE.name; $("brandSub").textContent = SITE.sub || "";
    document.title = SITE.name;
    $("hero").innerHTML = (SITE.kicker ? '<div class="hero-kicker">' + esc(SITE.kicker) + "</div>" : "") +
      "<h1>" + (SITE.title || esc(SITE.name)) + "</h1>" +
      (SITE.lede ? '<p class="hero-sub">' + SITE.lede + "</p>" : "") +
      '<div class="hero-stats"><span class="stat-chip"><b>' + P().length + "</b>条提示词</span>" +
      CATLIST().filter(function (c) { return P().some(function (p) { return p.cat === c.key; }); }).map(function (c) {
        return '<span class="stat-chip" style="--c:' + c.color + '"><b>' + P().filter(function (p) { return p.cat === c.key; }).length + "</b>" + esc(c.name) + "</span>";
      }).join("") + "</div>" +
      (SITE.note ? '<div class="hero-note">' + esc(SITE.note) + "</div>" : "");
    var html = "";
    ((OVERVIEW || {}).sections || []).forEach(function (sec) {
      html += '<h3 class="sub-h">' + esc(sec.h) + "</h3>";
      if (sec.type === "cards") html += '<div class="grid-2">' + sec.items.map(function (x, i) {
        return '<div class="mini-card"><h4><span class="idx">' + ("0" + (i + 1)).slice(-2) + "</span>" + esc(x.t) + "</h4><p>" + esc(x.d) + "</p></div>";
      }).join("") + "</div>";
      else if (sec.type === "steps") html += '<div class="anatomy-list">' + sec.items.map(function (x, i) {
        return '<div class="anatomy-item"><span class="a-name">' + ("0" + (i + 1)).slice(-2) + " " + esc(x.name) + '</span><span class="a-tip">' + esc(x.tip) + "</span></div>";
      }).join("") + "</div>";
      else if (sec.type === "table") html += '<table class="ov-table"><tr><th>翻车写法</th><th>修正写法</th></tr>' + sec.items.map(function (x) {
        return "<tr><td>" + esc(x.a) + "</td><td>" + esc(x.b) + "</td></tr>";
      }).join("") + "</table>";
    });
    $("ovBody").innerHTML = html;
    var f = SITE.footer || {};
    $("pageFooter").innerHTML = (f.refs && f.refs.length ? "<h3>参考</h3><ol>" + f.refs.map(function (r) { return "<li>" + esc(r) + "</li>"; }).join("") + "</ol>" : "") +
      (f.memo ? "<h3>备忘</h3><p>" + esc(f.memo) + "</p>" : "") +
      '<p class="footer-line">提示词库 · 五文件模板 · 页面直接增删改（本地自动保存）·「存为文件」写回 提示词库.data.js · 零外部依赖</p>';
  }

  /* ---- 深链 ---- */
  function applyHash() {
    var h = decodeURIComponent((location.hash || "").replace("#", ""));
    var it = P().filter(function (i) { return i.code.toUpperCase() === h.toUpperCase(); })[0];
    if (it) { state.filter = "all"; goLib(); select(it.code, false); return true; }
    if (CATS()[h]) { state.filter = h; goLib(); var items = visibleItems(); state.code = items.length ? items[0].code : null; renderList(); renderDetail(items); return true; }
    return false;
  }
  window.addEventListener("hashchange", applyHash);

  /* ---- 装配 ---- */
  renderOverview();
  var items0 = visibleItems();
  state.code = items0.length ? items0[0].code : null;
  renderAll();
  if (OVERVIEW) goOverview(); else goLib();
  applyHash();
  if (PL.mergedFromSeed()) toast("已从 提示词库.data.js 并入 " + PL.mergedFromSeed() + " 条新种子数据");
  renderDrafts();
  validate();

  /* ---- 主题 ---- */
  var KEY = "prompt-lib-template-theme", root = document.documentElement, saved = null;
  try { saved = localStorage.getItem(KEY); } catch (e) {}
  function applyTheme(t) { root.setAttribute("data-theme", t); $("themeLabel").textContent = t === "dark" ? "浅色" : "深色"; }
  applyTheme(saved === "light" ? "light" : "dark");
  $("themeToggle").addEventListener("click", function () {
    var t = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
    applyTheme(t); try { localStorage.setItem(KEY, t); } catch (e) {}
  });
})();
