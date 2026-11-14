#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验收用例校验：references/acceptance.md 必须是 1-3 条可判定用例。

用法：
    python -X utf8 scripts/validate_acceptance.py <skill目录>
"""
import re
import sys
from pathlib import Path


def check_acceptance(skill_dir):
    root = Path(skill_dir)
    path = root / "references/acceptance.md"
    errors, warnings = [], []
    if not path.is_file():
        return ["缺少 references/acceptance.md"], warnings

    text = path.read_text(encoding="utf-8", errors="ignore")
    DOC_MARK = chr(0x3010) + "\u5f85\u586b" + chr(0x3011)
    if DOC_MARK in text:
        errors.append("acceptance.md 仍含文档流程标记（未定制）")

    marks = list(re.finditer(r"^##\s*用例\s*(\d+)[^\n]*$", text, re.M))
    if not marks:
        return errors + ["acceptance.md 没有「## 用例 N」"], warnings
    if len(marks) > 3:
        warnings.append(f"验收用例 {len(marks)} 条，建议 1-3 条")

    for i, mark in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        block = text[mark.start():end]
        case = mark.group(1)
        for heading in ("### 输入", "### 期望输出", "### 判定点"):
            pos = block.find(heading)
            if pos < 0:
                errors.append(f"用例 {case} 缺少 {heading}")
                continue
            body = block[pos + len(heading):]
            body = re.split(r"^### |^## ", body, maxsplit=1, flags=re.M)[0]
            if not body.strip():
                errors.append(f"用例 {case} 的 {heading} 为空")
        point_pos = block.find("### 判定点")
        if point_pos >= 0:
            point_body = re.split(r"^### |^## ", block[point_pos + len("### 判定点"):], maxsplit=1, flags=re.M)[0]
            if not re.search(r"-\s*\[[ xX]\]", point_body):
                errors.append(f"用例 {case} 的判定点没有勾选项")
    return errors, warnings


def main():
    skill_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    errors, warnings = check_acceptance(skill_dir)
    for warning in warnings:
        print(f"WARN {warning}")
    for error in errors:
        print(f"ERR {error}")
    if errors:
        print(f"ERR 验收用例校验失败：{len(errors)} 个问题")
        return 1
    text = (Path(skill_dir) / "references/acceptance.md").read_text(encoding="utf-8", errors="ignore")
    count = len(re.findall(r"^##\s*用例\s*\d+", text, re.M))
    print(f"OK 验收用例通过（{count} 条）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
