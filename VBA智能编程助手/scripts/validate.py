#!/usr/bin/env python3
# ============================================
# Skill Structure Validator
# ============================================

import sys
import re
import json
import shutil
import subprocess
from pathlib import Path

# Color functions
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    YELLOW = '\033[93m'
    GRAY = '\033[90m'
    RESET = '\033[0m'

def print_success(message): print(f"{Colors.GREEN}OK {message}{Colors.RESET}")
def print_error(message): print(f"{Colors.RED}ERR {message}{Colors.RESET}")
def print_info(message): print(f"{Colors.BLUE}INFO {message}{Colors.RESET}")
def print_warning(message): print(f"{Colors.YELLOW}WARN {message}{Colors.RESET}")

errors = 0
warnings = 0

# Check file
def check_file(skill_dir, file, desc, required=True):
    global errors, warnings
    path = Path(skill_dir) / file
    if path.exists():
        print_success(f"{desc} : {file}"); return True
    if required: print_error(f"Missing {desc} : {file}"); errors += 1
    else: print_warning(f"Suggested: {desc} : {file}"); warnings += 1
    return False

# Check directory
def check_dir(skill_dir, dir_name, desc, required=True):
    global errors, warnings
    path = Path(skill_dir) / dir_name
    if path.exists() and path.is_dir():
        print_success(f"{desc} : {dir_name}/"); return True
    if required: print_error(f"Missing {desc} : {dir_name}/"); errors += 1
    else: print_warning(f"Suggested: {desc} : {dir_name}/"); warnings += 1
    return False

CJK_RE = re.compile(r'[\u4e00-\u9fff]')

# Check YAML header
def check_yaml_header(skill_dir, file):
    global errors
    path = Path(skill_dir) / file

    if path.exists():
        content = path.read_text(encoding='utf-8')

        if re.search(r'^---\s*\n', content):
            m = re.search(r'name:\s*(\S+)', content)
            if m:
                print_success("YAML header has name field")
                # B1: Skill 名称必须中文
                if not CJK_RE.search(m.group(1)):
                    print_error(f"SKILL.md frontmatter name should be Chinese (B1): {m.group(1)}")
                    errors += 1
            else: print_error("YAML header missing name field"); errors += 1

            if re.search(r'description:\s*.+', content):
                print_success("YAML header has description field")
            else: print_error("YAML header missing description field"); errors += 1
        else: print_error("SKILL.md missing YAML header"); errors += 1

# Check required sections (A1: 中英双轨，中文模板不再永久 MISS)
def check_sections(skill_dir, file):
    global errors, warnings
    path = Path(skill_dir) / file
    if path.exists():
        content = path.read_text(encoding='utf-8')
        patterns = [("这个 Skill 做什么 / What This Skill Does", r"这个\s*Skill\s*做什么|What This Skill Does"), ("为什么需要 / Why.*Matters", r"为什么需要|Why.*Matters"),
                    ("核心原则 / Core Principles", r"核心原则|Core Principles"), ("最佳实践 / Best Practices", r"最佳实践|Best Practices"), ("总结 / Summary", r"总结|Summary")]

        for pattern_name, pattern in patterns:
            if re.search(pattern, content): print_success(f"Has section matching: {pattern_name}")
            else: print_warning(f"Suggested section: {pattern_name}"); warnings += 1
        if re.search(DOC_TOKEN_RE, content): print_error("SKILL.md 仍含文档流程标记（待填骨架），补齐后交付"); errors += 1
        lines = content.splitlines()
        idx = next((i for i, l in enumerate(lines) if re.match(r"^##\s*执行工作流", l)), None)
        if idx is None:
            print_error("Missing required section: 执行工作流"); errors += 1
        else:
            end = next((j for j in range(idx + 1, len(lines)) if lines[j].startswith("## ")), len(lines))
            body = chr(10).join(lines[idx + 1:end])
            marks = list(re.finditer(r"^\s*(\d+)\.\s+(.+)$", body, re.M))
            if len(marks) < 3: print_error(f"执行工作流步骤不足: {len(marks)}，至少 3 步"); errors += 1
            elif len(marks) > 6: print_warning(f"执行工作流步骤过多: {len(marks)}，建议 3-6 步"); warnings += 1
            groups = (("输入", ("输入",)), ("动作", ("动作", "操作")), ("产出", ("产出", "输出")), ("门禁", ("门禁", "验收", "证据")))
            for k, m in enumerate(marks):
                block = body[m.start():marks[k + 1].start() if k + 1 < len(marks) else len(body)]
                miss = [name for name, keys in groups if not any(x in block for x in keys)]
                if miss: print_error(f"执行工作流第 {m.group(1)} 步缺少: {'/'.join(miss)}"); errors += 1

# ============================================
# prompts/ 五文件 HTML 提示词库校验
# ============================================
BUNDLE_FILES = ["提示词库.html", "提示词库.style.css", "提示词库.store.js", "提示词库.engine.js", "提示词库.data.js"]
JS_FILES = ("提示词库.store.js", "提示词库.engine.js", "提示词库.data.js")
BASE_CATS = {"sys": "系统", "gen": "通用"}
SCENE_EXCLUDED = ("sys", "gen")
LB2 = chr(123) * 2          # 连续左双花括弧
RB2 = chr(125) * 2          # 连续右双花括弧
# 内容红线黑名单：词面一律 \u 转义拆写构造（防门禁自指命中）；定义源 references/prompt_library.md §4
BLACKLIST = [
    LB2, RB2,
    "\u586b" "\u7a7a",
    "\u6b64" "\u5904\u586b\u5199",
    "\u865a" "\u6784",
    "\u5360" "\u4f4d\u6f14\u793a",
    "\u5047" "\u97f3\u6548\u96c6",
    "\u5047" "\u6570\u636e\u96c6",
    "\u5047" "\u6570\u636e",
    "\u6a21" "\u62df\u6570\u636e",
    "\u6a21" "\u62df\u5185\u5bb9",
    "\u793a" "\u4f8b",
]
SLOT_L = chr(0x3010)
SLOT_R = chr(0x3011)
FULL_SLOT = re.compile(SLOT_L + "[^" + SLOT_R + "]{1,12}" + SLOT_R)
MARKER = "\u9aa8" "\u67b6\u5f85\u751f\u6210"          # 骨架未定制标记（槽位豁免、单独拦）
DOC_TOKEN_RE = SLOT_L + "待填" + SLOT_R        # SKILL.md/acceptance.md 文档流程标记（单独拦）
PROMPT_HEAD = re.compile(r"使用「[^「」\r\n]+」skill[。.]?")
PROMPT_FIELDS = ("任务", "要求", "输出")
PROMPT_LENGTH_WARNING = 300

def banned_hit(s):
    for w in BLACKLIST:
        if w in s:
            return w
    m = FULL_SLOT.search(s)
    if m and MARKER in m.group(0):
        return ""
    return m.group(0) if m else ""

def _unquote(s):
    try: return json.loads('"' + s + '"')
    except Exception: return s

def _skip_js_literal(src, i):
    q, i = src[i], i + 1
    while i < len(src):
        if src[i] == "\\":
            i += 2
            continue
        if src[i] == q:
            return i + 1
        i += 1
    return i

def _skip_comment(src, i):
    if src.startswith("//", i):
        j = src.find("\n", i)
        return len(src) if j < 0 else j + 1
    j = src.find("*/", i)
    return len(src) if j < 0 else j + 2

def _js_object_block(src, key):
    k = r'(?:' + re.escape(key) + r'|"' + re.escape(key) + r'")'
    m = re.search(k + r'\s*:\s*\{', src)
    if not m:
        return ""
    i, depth = m.end() - 1, 0
    while i < len(src):
        if src.startswith("//", i) or src.startswith("/*", i):
            i = _skip_comment(src, i)
            continue
        c = src[i]
        if c in "\"'`":
            i = _skip_js_literal(src, i)
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return src[m.end() - 1:i + 1]
        i += 1
    return src[m.end() - 1:]

def _js_prompt_entries(src):
    m = re.search(r'(?:prompts|"prompts")\s*:\s*\[', src)
    if not m:
        return []
    i, depth, start, blocks = m.end(), 1, None, []
    while i < len(src):
        if src.startswith("//", i) or src.startswith("/*", i):
            i = _skip_comment(src, i)
            continue
        c = src[i]
        if c in "\"'`":
            i = _skip_js_literal(src, i)
            continue
        if c in "[{":
            depth += 1
            if c == "{" and depth == 2:
                start = i
        elif c in "]}":
            depth -= 1
            if c == "}" and depth == 1 and start is not None:
                blocks.append(src[start:i + 1])
                start = None
            elif c == "]" and depth == 0:
                break
        i += 1
    return blocks

def _key_pat(key):
    """裸键与页面快照的引号键都识别：name: 与 "name": 等价"""
    return r'(?:' + re.escape(key) + r'|"' + re.escape(key) + r'")\s*:'

def _field_str(block, field):
    m = re.search(_key_pat(field) + r'\s*"((?:[^"\\]|\\.)*)"', block)
    return _unquote(m.group(1)) if m else None

def _field_tags(block):
    m = re.search(_key_pat('tags') + r'\s*\[([^\]]*)\]', block)
    return [_unquote(x) for x in re.findall(r'"((?:[^"\\]|\\.)*)"', m.group(1))] if m else None

def _field_prompt(block):
    m = re.search(_key_pat('prompt') + r'\s*`', block)
    if not m:
        return None
    i, out = m.end(), []
    while i < len(block):
        c = block[i]
        if c == "\\" and i + 1 < len(block):
            out.append(block[i + 1])
            i += 2
            continue
        if c == "`":
            return "".join(out)
        out.append(c)
        i += 1
    return None

def check_prompts(skill_dir):
    global errors, warnings
    prompts = Path(skill_dir) / "prompts"
    if not prompts.is_dir():
        print_error("Missing prompts directory : prompts/"); errors += 1; return
    missing = [f for f in BUNDLE_FILES if not (prompts / f).is_file()]
    for f in BUNDLE_FILES:
        if f not in missing:
            print_success(f"Prompt bundle : prompts/{f}")
        else:
            print_error(f"Missing prompt bundle file : prompts/{f}")
            errors += 1
    if missing:
        print_error("prompts/ 必须是五文件 HTML 提示词库（先从 Prompts模版/ 原样复制）"); return

    html = (prompts / BUNDLE_FILES[0]).read_text(encoding="utf-8", errors="ignore")
    refs = re.findall(r'(?:src|href)="([^"]+)"', html)
    for ref in refs:
        if re.match(r'^[a-zA-Z]+:', ref) or ref.startswith("#"):
            continue
        if not (prompts / ref.split("?")[0]).is_file():
            print_error(f"提示词库.html 引用的文件不存在 : {ref}"); errors += 1
    for f in BUNDLE_FILES[1:]:
        if f not in refs:
            print_error(f"提示词库.html 未引用配套文件 : {f}"); errors += 1

    node = shutil.which("node")
    if node:
        for f in JS_FILES:
            try:
                r = subprocess.run([node, "--check", str(prompts / f)], capture_output=True, text=True, timeout=30)
            except Exception as e:
                print_warning(f"跳过 JS 语法自检 {f}: {e}"); warnings += 1; continue
            if r.returncode != 0:
                print_error(f"JS 语法错误 : {f} -> {(r.stderr or '').strip().splitlines()[:1]}"); errors += 1
    else:
        print_warning("未检测到 node，跳过 JS 语法自检（建议安装 Node 后复跑）")
        warnings += 1

    src = (prompts / "提示词库.data.js").read_text(encoding="utf-8", errors="ignore")
    if "window.DATA" not in src:
        print_error("提示词库.data.js 缺少 window.DATA 赋值"); errors += 1; return
    blocks = _js_prompt_entries(src)
    if not blocks:
        print_error("无法解析 提示词库.data.js 的 prompts 数组"); errors += 1; return
    mo = re.search(r'(?:overview|"overview")\s*:', src)
    head_seg = src[:mo.start()] if mo else ""
    ov_seg = ""
    if mo:
        mp = re.search(r'(?:^prompts:|"prompts"\s*:)', src[mo.end():], re.M)
        ov_seg = src[mo.end():mo.end() + mp.start()] if mp else src[mo.end():]
    for label, seg in (("site", head_seg), ("overview", ov_seg)):
        hit_so = banned_hit(seg)
        if hit_so:
            print_error(f"提示词库.data.js 的 {label} 块命中内容红线词面「{hit_so}」"); errors += 1

    entries, seen = [], {}
    for i, b in enumerate(blocks):
        it = {f: _field_str(b, f) for f in ("code", "cat", "title", "scene")}
        it["tags"], it["prompt"] = _field_tags(b), _field_prompt(b)
        tag = f"prompts[{i}] ({it['code'] or '?'})"
        for f in ("code", "cat", "title", "scene", "prompt"):
            if not (it[f] or "").strip():
                print_error(f"{tag} 缺字段或为空 : {f}")
                errors += 1
        if not isinstance(it["tags"], list):
            print_error(f"{tag} tags 必须是数组"); errors += 1
        for f in ("code", "cat", "title", "scene", "prompt"):
            hit = banned_hit(it[f] or "")
            if hit:
                print_error(f"{tag} 字段 {f} 命中内容红线词面「{hit}」（槽位/禁锚点，见 prompt_library.md §4）"); errors += 1
        prm = it["prompt"] or ""
        if prm:
            if MARKER in prm:
                print_error(f"{tag} 条目未定制：消除全角括号标记、代入真实正文后才可分发"); errors += 1
            lines = prm.strip().splitlines()
            if not lines or not PROMPT_HEAD.fullmatch(lines[0]):
                print_error(f"{tag} prompt 首行应为短调用句：使用「本 Skill 名」skill。"); errors += 1
            for field in PROMPT_FIELDS:
                if not re.search(r"^" + field + r"[：:][^\S\r\n]*\S[^\r\n]*\r?$", prm, re.M):
                    print_error(f"{tag} prompt 缺少或未填写结构项：{field}"); errors += 1
            if len(prm.strip()) > PROMPT_LENGTH_WARNING:
                print_warning(f"{tag} prompt 超过 {PROMPT_LENGTH_WARNING} 字符（{len(prm.strip())}），建议精简重复说明，保留必要约束"); warnings += 1
        if it["code"] and it["code"] in seen:
            print_error(f"{tag} code 与 prompts[{seen[it['code']]}] 重复"); errors += 1
        elif it["code"]:
            seen[it["code"]] = i
        entries.append(it)

    skill_md = Path(skill_dir) / "SKILL.md"
    if skill_md.is_file():
        text = skill_md.read_text(encoding="utf-8-sig")
        text = re.sub(r"(?ms)^(`{3,}|~{3,})[^\n]*\n.*?^\1[ \t]*$", "", text)
        linked_codes = re.findall(r"\]\(prompts/提示词库\.html#([^\s)]+)\)", text)
        for code in dict.fromkeys(linked_codes):
            if code not in seen:
                print_error(f"SKILL.md 场景索引指向不存在的提示词 : {code}"); errors += 1
        if linked_codes and all(code in seen for code in linked_codes):
            print_success(f"场景索引链接有效 : {len(linked_codes)} 项（语义覆盖仍需反向查漏）")

    site = _js_object_block(src, "site")
    site_name = _field_str(site, "name")
    dir_name = Path(skill_dir).resolve().name
    if not site_name:
        print_error("提示词库.data.js 的 site.name 为空（应与 Skill 名称一致）"); errors += 1
    elif site_name != dir_name:
        print_error(f"site.name「{site_name}」与 Skill 目录名「{dir_name}」不一致（站名契约）"); errors += 1

    cat_block = re.search(r'(?:categories|"categories")\s*:\s*\[(.*?)\]', site, re.S)
    declared = [_unquote(x) for x in re.findall(r'(?:key|"key")\s*:\s*"((?:[^"\\]|\\.)*)"', cat_block.group(1))] if cat_block else []
    if not declared:
        print_error("site.categories 未声明分类（至少 sys/gen 两类）"); errors += 1
    else:
        for k, label in BASE_CATS.items():
            if k not in declared:
                print_error(f"site.categories 缺少分类声明 : {k}（{label}）"); errors += 1
        for it in entries:
            if it["cat"] and it["cat"] not in declared:
                print_error(f"{it['code']} 的 cat「{it['cat']}」未在 site.categories 中声明"); errors += 1

    counts = {}
    for it in entries:
        counts[it["cat"]] = counts.get(it["cat"], 0) + 1
    scene_n = sum(v for k, v in counts.items() if k not in SCENE_EXCLUDED)
    if scene_n < 2:
        print_error(f"场景类条目不足（sys/gen 之外的分类）: 当前 {scene_n} 条，至少 2 条"); errors += 1
    for k, label in BASE_CATS.items():
        if counts.get(k, 0) < 1:
            print_error(f"缺少{label}条目 : cat={k} 至少 1 条"); errors += 1
    if re.search(r'(?:overview|"overview")\s*:\s*null', src):
        print_warning("overview 为 null：建议补充使用说明与常见翻车清单")
        warnings += 1
    stray = [p for p in prompts.rglob("*.md") if p.name != "README.md"]
    if stray:
        print_error(f"prompts/ 下不应再有 .md 提示词文件（内容统一进 data.js）: {stray[0].name}"); errors += 1
    print_info("提示词库分布: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
def check_layered(skill_dir):
    global errors, warnings
    root = Path(skill_dir)
    index, exp = root / "index.md", root / "expertise"
    if not index.is_file():
        if exp.is_dir():
            print_error("expertise/ 存在但缺少 index.md：分层结构必须有导航索引")
            errors += 1
        return
    print_success("Layered index : index.md")
    for sub in ("by_task", "by_category", "quick_reference"):
        d = exp / sub
        if not (d.is_dir() and any(d.iterdir())):
            print_error(f"分层结构目录缺失或为空 : expertise/{sub}/")
            errors += 1
    for link in re.findall(r'\]\(([^)#]+)', index.read_text(encoding="utf-8", errors="ignore")):
        if re.match(r'^[a-zA-Z]+:', link) or link.startswith("#"):
            continue
        if not (root / link).exists():
            print_error(f"index.md 链接目标不存在 : {link}")
            errors += 1

# Evolution ledger (mechanism 6): schema check when present; missing file stays a suggestion
EV_STATES = ("已提案", "已采纳", "已驳回", "已回滚")

def check_evolution(skill_dir):
    global errors, warnings
    path = Path(skill_dir) / "evolution.md"
    if not path.is_file():
        print_warning("建议加装自行进化台账 evolution.md（触发/提案/落版闭环）")
        warnings += 1
        return
    print_success("Evolution ledger : evolution.md")
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    starts = [i for i, l in enumerate(lines) if re.match(r"^## EV-", l)]
    pending = 0
    for s in starts:
        end = next((j for j in range(s + 1, len(lines)) if lines[j].startswith("## ")), len(lines))
        block, head = "\n".join(lines[s:end]), lines[s]
        tag = head[:46]
        state = next((w for w in EV_STATES if w in head), None)
        if not state:
            print_error(f"evolution.md 条目缺状态枚举（已提案/已采纳/已驳回/已回滚）: {tag}")
            errors += 1
        if not re.search(r"E[1-5]", head):
            print_error(f"evolution.md 条目缺类别 E1-E5: {tag}")
            errors += 1
        for field in ("触发", "证据", "提案"):
            if not re.search(r"^-\s*" + field + r"\s*[：:]\s*\S", block, re.M):
                print_error(f"evolution.md 条目缺 {field} 字段: {tag}")
                errors += 1
        if state == "已提案":
            pending += 1
        if state == "已采纳":
            m = re.search(r"^-\s*落点\s*[：:]\s*(.*)$", block, re.M)
            if not m or not m.group(1).strip() or "未实施" in m.group(1):
                print_error(f"evolution.md 已采纳条目必须带落点（git 哈希或 未入库:原因）: {tag}")
                errors += 1
    if pending:
        print_warning(f"evolution.md 有 {pending} 条已提案未决：下个任务开工时向用户复述，经批准再落版")
        warnings += 1

# Main flow
def main():
    global errors, warnings

    skill_dir = sys.argv[1] if len(sys.argv) > 1 else "."

    print("")
    print(f"{Colors.BLUE}================================================{Colors.RESET}")
    print(f"{Colors.BLUE}           Skill Structure Validator            {Colors.RESET}")
    print(f"{Colors.BLUE}================================================{Colors.RESET}")
    print("")

    print_info(f"Validating: {skill_dir}")
    print("")

    # Required files
    print(f"{Colors.CYAN}=== Required Files ==={Colors.RESET}")
    check_file(skill_dir, "SKILL.md", "Core document", True)
    check_file(skill_dir, "scripts/validate.py", "Validator", True)
    check_file(skill_dir, "scripts/validate_acceptance.py", "Acceptance validator", True)
    # Validate entry scripts (scaffold-generated; warn-only so pre-entry skills stay valid)
    if not any((Path(skill_dir) / f).is_file() for f in ("check.cmd", "check.sh")):
        print_warning("Suggested: 验证入口 check.cmd / check.sh（脚手架已自动生成于 skill 根）"); warnings += 1

    # Recommended directories
    print(f"{chr(10)}{Colors.CYAN}=== Recommended Directories ==={Colors.RESET}")
    check_dir(skill_dir, "references", "References", False)
    check_dir(skill_dir, "scripts", "Scripts", False)

    # YAML header check
    print(f"{chr(10)}{Colors.CYAN}=== YAML Header ==={Colors.RESET}")
    check_yaml_header(skill_dir, "SKILL.md")

    # Content sections check
    print(f"{chr(10)}{Colors.CYAN}=== Content Sections ==={Colors.RESET}")
    check_sections(skill_dir, "SKILL.md")

    # Reference files check
    print(f"{chr(10)}{Colors.CYAN}=== Reference Files ==={Colors.RESET}")
    check_file(skill_dir, "references/core_concepts.md", "Core concepts", False)
    check_file(skill_dir, "references/patterns.md", "Patterns", False)
    check_file(skill_dir, "references/best_practices.md", "Best practices", False)
    check_file(skill_dir, "references/examples.md", "Examples", False)

    # Prompts check (five-file HTML prompt library)
    print(f"{chr(10)}{Colors.CYAN}=== Prompts (五文件 HTML 提示词库) ==={Colors.RESET}")
    check_prompts(skill_dir)

    # Layered structure (optional)
    check_layered(skill_dir)

    # Evolution ledger (mechanism 6; optional for legacy skills)
    check_evolution(skill_dir)

    # Result
    print("")
    print(f"{Colors.GRAY}================================================{Colors.RESET}")

    if errors == 0 and warnings == 0:
        print(f"{Colors.GREEN}OK Validation passed! Skill structure is complete.{Colors.RESET}")
        sys.exit(0)
    elif errors == 0:
        print(f"{Colors.YELLOW}OK Validation passed with {warnings} suggestions.{Colors.RESET}")
        sys.exit(0)
    else:
        print(f"{Colors.RED}ERR Found {errors} errors, {warnings} suggestions.{Colors.RESET}")
        sys.exit(1)

if __name__ == "__main__":
    main()
