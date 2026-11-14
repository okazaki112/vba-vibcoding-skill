/* ════════════════════════════════════════════════════════════
   存储层 —— 本文件日常不用修改。
   职责：localStorage 活数据 + data.js 种子自动合并 + CRUD +
        序列化回写 提示词库.data.js（FSA 直写，失败降级下载）+ JSON 备份/恢复
   ════════════════════════════════════════════════════════════ */
window.PL = (function () {
  function clone(o) { return JSON.parse(JSON.stringify(o)); }
  var D = window.DATA || {};
  var bootErr = [];
  if (!D.site || !Array.isArray(D.prompts)) {
    bootErr.push("未读取到 提示词库.data.js —— 请确认五个模板文件在同一文件夹内。");
    D = { site: { name: "提示词库（数据未加载）", sub: "", categories: [] }, overview: null, prompts: [] };
  }
  var SITE = D.site, OVERVIEW = D.overview || null;
  var SEED = D.prompts.map(clone);

  /* ---- 活数据：localStorage 优先，文件新条目自动并入 ---- */
  /* 键名按站名派生：同一浏览器打开多个 Skill 的提示词库不会串数据 */
  var KEY = "prompt-lib-live-v1:" + encodeURIComponent(SITE.name || "untitled");
  var live = null, mergedFromSeed = 0;
  try { var s = JSON.parse(localStorage.getItem(KEY) || "null"); if (s && Array.isArray(s.prompts)) live = s.prompts.map(clone); } catch (e) {}
  if (!live) { live = SEED.map(clone); }
  else {
    var codes = {}; live.forEach(function (p) { codes[p.code] = 1; });
    SEED.forEach(function (p) { if (!codes[p.code]) { live.push(clone(p)); mergedFromSeed++; } });
  }
  function persist() { try { localStorage.setItem(KEY, JSON.stringify({ t: Date.now(), prompts: live })); return true; } catch (e) { return false; } }
  persist();

  /* ---- 分类列派生（数据驱动，CRUD 后重建）---- */
  var CATLIST = [], CATS = {};
  function rebuildCats() {
    var PALETTE = SITE.palette || ["#ff5b3a", "#a78bfa", "#35e0c8", "#f0b35c", "#79c0ff", "#e06c9f", "#8ed081", "#ff8f6b"];
    live.forEach(function (it) { if (!it.cat) it.cat = "_none"; });
    CATLIST = (SITE.categories || []).map(function (c) { return Object.assign({}, c); });
    CATLIST.forEach(function (c) { if (!c.name) c.name = c.key; });
    live.forEach(function (it) {
      if (!CATLIST.some(function (c) { return c.key === it.cat; })) CATLIST.push({ key: it.cat, name: it.cat === "_none" ? "未分类" : it.cat });
    });
    var pi = 0;
    CATLIST.forEach(function (c, i) {
      if (!c.color) c.color = PALETTE[pi++ % PALETTE.length];
      if (!c.num) c.num = ("0" + (i + 1)).slice(-2);
    });
    CATS = {}; CATLIST.forEach(function (c) { CATS[c.key] = c; });
  }
  rebuildCats();

  /* ---- CRUD ---- */
  function indexOfCode(code) { for (var i = 0; i < live.length; i++) if (live[i].code === code) return i; return -1; }
  function upsert(item, oldCode) {
    oldCode = oldCode || item.code;
    if (!item.code) return { err: "编号 code 不能为空" };
    var i = indexOfCode(oldCode);
    if (item.code !== oldCode && indexOfCode(item.code) >= 0) return { err: "编号 " + item.code + " 已存在，换一个" };
    var copy = clone(item); if (!copy.cat) copy.cat = "misc";
    if (i >= 0) live[i] = copy; else { if (indexOfCode(copy.code) >= 0) return { err: "编号 " + copy.code + " 已存在" }; live.push(copy); }
    persist(); rebuildCats();
    return { ok: true, code: copy.code };
  }
  function remove(code) {
    var i = indexOfCode(code); if (i < 0) return { err: "找不到条目 " + code };
    var name = live[i].title || code; live.splice(i, 1); persist(); rebuildCats();
    return { ok: true, name: name };
  }
  function resetToSeed() { live = SEED.map(clone); persist(); rebuildCats(); return { ok: true }; }

  /* ---- 序列化为完整 提示词库.data.js ---- */
  function serStr(s) { return JSON.stringify(s == null ? "" : String(s)); }
  function serPrompt(s) { return "`" + String(s == null ? "" : s).replace(/\\/g, "\\\\").replace(/`/g, "\\`").replace(/\$\{/g, "\\${") + "`"; }
  function serializeFile() {
    var items = live.map(function (it) {
      return "    {\n      code: " + serStr(it.code) + ", cat: " + serStr(it.cat) + ", title: " + serStr(it.title) + ",\n      tags: [" + (it.tags || []).map(serStr).join(", ") + "],\n      scene: " + serStr(it.scene) + ",\n      prompt: " + serPrompt(it.prompt) + "\n    }";
    }).join(",\n");
    return "/* 由提示词库页面生成于 " + new Date().toLocaleString("zh-CN") + "（页面管理数据快照，格式与手写一致） */\nwindow.DATA = {\n  site: " + JSON.stringify(SITE, null, 4) + ",\n\n  overview: " + (OVERVIEW ? JSON.stringify(OVERVIEW, null, 4) : "null") + ",\n\n  prompts: [\n" + items + "\n  ]\n};\n";
  }
  function downloadText(name, text, mime) {
    var a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([text], { type: mime || "text/javascript;charset=utf-8" }));
    a.download = name; document.body.appendChild(a); a.click();
    setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 400);
  }
  /* 回写文件：FSA 可用则直接写盘（http/新标签环境），file:// 下自动降级为下载 */
  function saveToDataFile(cb) {
    var text = serializeFile();
    if (window.showSaveFilePicker) {
      window.showSaveFilePicker({ suggestedName: "提示词库.data.js" }).then(function (h) {
        return h.createWritable().then(function (w) { return w.write(new Blob([text], { type: "text/javascript" })).then(function () { return w.close(); }); });
      }).then(function () { cb && cb("saved"); }, function (e) {
        if (e && e.name === "AbortError") { cb && cb("cancel"); return; }
        downloadText("提示词库.data.js", text); cb && cb("downloaded");
      });
    } else { downloadText("提示词库.data.js", text); cb && cb("downloaded"); }
  }
  function backupJson(cb) { downloadText("提示词库备份-" + new Date().toISOString().slice(0, 10) + ".json", JSON.stringify({ app: "prompt-lib", v: 3, prompts: live }, null, 2), "application/json"); cb && cb("ok"); }
  function restoreJson(file, cb) {
    var r = new FileReader();
    r.onload = function () {
      try {
        var o = JSON.parse(r.result);
        var arr = Array.isArray(o) ? o : o.prompts;
        if (!Array.isArray(arr) || !arr.length || !arr[0].code) return cb({ err: "备份文件格式不对：需要含 code 的 prompts 数组" });
        live = arr.map(clone); persist(); rebuildCats(); cb({ ok: true, n: live.length });
      } catch (e) { cb({ err: "JSON 解析失败：" + e.message }); }
    };
    r.onerror = function () { cb({ err: "文件读取失败" }); };
    r.readAsText(file, "utf-8");
  }

  return {
    SITE: SITE, OVERVIEW: OVERVIEW, bootErr: bootErr,
    live: function () { return live; },
    cats: function () { return { CATLIST: CATLIST, CATS: CATS }; },
    mergedFromSeed: function () { return mergedFromSeed; },
    upsert: upsert, remove: remove, resetToSeed: resetToSeed,
    serializeFile: serializeFile, saveToDataFile: saveToDataFile,
    backupJson: backupJson, restoreJson: restoreJson
  };
})();
