# -*- coding: utf-8 -*-
"""
从 git 提交历史自动生成 README 的「📜 更新历史」章节。

为什么要自动生成而不是手写：
  仓库每天由 CI 提交一次规则更新，手工维护的更新日志必然过期；
  这里只收录**功能性变更**（跳过 `✅ 规则自动更新` 的例行提交），
  每次 CI 跑完自动刷新，无需人工介入。

实现要点：
  1. 提交时间统一换算成北京时间（CI 运行在 UTC，直接取 %ad 会错 8 小时）；
  2. 只取非合并提交，按日期倒序分组；最新一天展开，历史日期折叠进 <details>；
  3. 内容与上次生成完全一致时不写文件（避免无意义 diff）；
  4. README 里没有标记时自动插入到「拦截效果在线测试」之前。
"""
import os
import re
import subprocess
from datetime import datetime, timedelta, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../.."))
README_PATH = os.path.join(REPO_ROOT, "README.md")

REPO_URL = "https://github.com/xiaolei7172/ADS"
MARK_S, MARK_E = "<!-- CHANGELOG:START -->", "<!-- CHANGELOG:END -->"
# 没有标记时插到这一章之前
INSERT_BEFORE = "## 🧪 拦截效果在线测试"

MAX_COMMITS = 200      # 最多扫这么多条提交，防历史过长
BEIJING = timezone(timedelta(hours=8))

# 提交主题的 emoji → 类型标签；未命中的归入「其他」
TYPE_MAP = {
    "✨": "新增", "➕": "新增源", "🪄": "新机制", "🔬": "新机制",
    "🐛": "修复", "🔧": "修复", "🩹": "修复", "🩺": "修复", "🔍": "修复", "🎬": "修复",
    "💄": "优化", "🔗": "优化", "🌐": "格式", "📊": "功能", "🔕": "变更",
    "🎯": "规则调优", "🛑": "规则调优", "🧹": "清理", "🧽": "清理",
    "📖": "文档", "📋": "文档", "🧪": "测试", "🤖": "CI", "⏪": "回滚",
}
# 这些是 CI 例行提交，不写进更新历史
SKIP_PATTERNS = (r"^✅\s*规则自动更新", r"^Update\s+\S+$", r"^Merge ")
EMOJI_RE = re.compile(r"^([\U0001F300-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF]+)\s*")

# Conventional Commits 前缀 → 类型标签，用于没带 emoji 的提交。
# 以前没有 emoji 就一律归「其他」，于是 feat/fix 这类规范提交和真正的杂项
# 混在一栏里分不出来。两种写法仓库里都存在，这里让它们都能正确归类，
# 不必为了美观去改写已推送的提交信息。
CONVENTIONAL_MAP = {
    "feat": "✨", "fix": "🐛", "docs": "📖", "perf": "💄",
    "refactor": "🧹", "style": "💄", "test": "🧪",
    "build": "🤖", "ci": "🤖", "chore": "🧹", "revert": "⏪",
}
CONVENTIONAL_RE = re.compile(r"^([A-Za-z]+)(?:\([^)]*\))?!?:\s*")


def git(*args):
    r = subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True,
                       text=True, encoding="utf-8", errors="ignore", timeout=120)
    return r.stdout if r.returncode == 0 else ""


def read_commits():
    """返回 [(date_str, hash, subject)]，时间已换算为北京时间。"""
    raw = git("log", "--no-merges", "--date=iso-strict",
              "--pretty=format:%h%x1f%ad%x1f%s", "-n", str(MAX_COMMITS))
    out = []
    for line in raw.splitlines():
        parts = line.split("\x1f")
        if len(parts) < 3:
            continue
        h, iso, subj = parts[0].strip(), parts[1].strip(), parts[2].strip()
        subj = subj.replace("|", "\\|")
        if any(re.search(p, subj) for p in SKIP_PATTERNS):
            continue
        try:
            dt = datetime.fromisoformat(iso).astimezone(BEIJING)
            day = dt.strftime("%Y-%m-%d")
        except ValueError:
            day = iso[:10]
        out.append((day, h, subj))
    return out


def split_subject(subj):
    """把 '🎯 修复三处过宽规则' 拆成 ('🎯', '规则调优', '修复三处过宽规则')。

    没带 emoji 时再试 Conventional Commits 前缀（feat/fix/docs…），
    仍认不出才归「其他」。
    """
    m = EMOJI_RE.match(subj)
    if m:
        emoji = m.group(1)[0]
        label = TYPE_MAP.get(emoji, "其他")
        body = subj[m.end():].strip() or subj
    else:
        cm = CONVENTIONAL_RE.match(subj)
        emoji = CONVENTIONAL_MAP.get(cm.group(1).lower()) if cm else None
        if not emoji:
            return "🔹", "其他", subj
        label = TYPE_MAP.get(emoji, "其他")
        body = subj[cm.end():].strip() or subj
    # 去掉残留的变体选择符（U+FE0F）。如 '♻️ P1 重构' 会被 EMOJI_RE 在 '♻'
    # 处截断，剩下的 '️ P1' 带一个不可见字符，表格里看起来像多了个空格。
    body = body.lstrip("\ufe0f\u200d ").strip() or body
    if len(body) > 90:
        body = body[:88].rstrip() + "…"
    return emoji, label, body


def render():
    commits = read_commits()
    if not commits:
        return None

    groups, order = {}, []
    for day, h, subj in commits:
        if day not in groups:
            groups[day] = []
            order.append(day)
        groups[day].append((h, subj))

    lines = [
        MARK_S,
        "## 📜 更新历史",
        "",
        f"> 仅收录**功能性变更**；CI 每日的例行规则更新（`✅ 规则自动更新` 提交）不列出。"
        f"完整记录见 [Commits]({REPO_URL}/commits/master)。",
        "",
    ]
    for i, day in enumerate(order):
        items = groups[day]
        rows = []
        for h, subj in items:
            emoji, label, body = split_subject(subj)
            link = f"[`{h}`]({REPO_URL}/commit/{h})"
            rows.append(f"| {emoji} {label} | {body} | {link} |")
        table = ["| 类型 | 变更内容 | 提交 |", "| :--- | :--- | :--- |", *rows]

        if i == 0:
            lines.append(f"### 📅 {day}")
            lines.append("")
            lines.extend(table)
            lines.append("")
        else:
            lines.append("<details>")
            lines.append(f"<summary><b>📅 {day}</b> · {len(items)} 项变更</summary>")
            lines.append("")
            lines.extend(table)
            lines.append("")
            lines.append("</details>")
            lines.append("")
    lines.append(MARK_E)
    return "\n".join(lines)


def main():
    if not os.path.exists(README_PATH):
        print("⚠️ 未找到 README.md")
        return
    block = render()
    if not block:
        print("⚠️ 无 git 历史可读（浅克隆？），跳过更新历史")
        return

    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    if MARK_S in content and MARK_E in content:
        old = re.search(re.escape(MARK_S) + r".*?" + re.escape(MARK_E), content, re.S).group(0)
        if old == block:
            print("⏭️  更新历史无变化，不写入")
            return
        new = content.replace(old, block)
    elif INSERT_BEFORE in content:
        new = content.replace(INSERT_BEFORE, block + "\n\n" + INSERT_BEFORE, 1)
    else:
        new = content.rstrip() + "\n\n" + block + "\n"

    with open(README_PATH, "w", encoding="utf-8", newline="\n") as f:
        f.write(new)
    n_days = block.count("📅 ")
    n_items = block.count("](https://github.com/xiaolei7172/ADS/commit/")
    print(f"✅ 更新历史已写入 README：{n_days} 个日期分组 / {n_items} 条功能性提交")


if __name__ == "__main__":
    main()
