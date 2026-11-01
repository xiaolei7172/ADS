# -*- coding: utf-8 -*-
"""
更新规则文件表头。
改进点（相对旧版）：
  1. 【关键修复】规则正文没变化时，保留原文件不动（原时间戳继续有效）——
     旧版每次都写入新时间戳，规则一条没变也必然产生整文件 diff，
     这是仓库历史膨胀到 1 GB 的直接原因之一；
  2. 去掉 pytz 依赖，改用标准库固定 UTC+8（中国无夏令时）；
  3. 表头 Title/Description 区块下方附「规则来源统计」——
     打开规则页面第一屏就能看到每个上游贡献了多少条规则。
"""
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from common import count_valid_lines, beijing_now

if "GITHUB_WORKSPACE" in os.environ:
    REPO_ROOT = os.environ["GITHUB_WORKSPACE"]
else:
    REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../.."))

rules_dir = os.path.join(REPO_ROOT, "data", "rules")

file_config = {
    "adblock.txt": {
        "title": "天影规则聚合 · 广告拦截规则",
        "desc": "屏蔽全网广告、弹窗、跟踪、恶意域名",
        "comment": "!"
    },
    "dns.txt": {
        "title": "天影规则聚合 · DNS 拦截规则",
        "desc": "DNS级广告域名屏蔽，支持AdGuard Home / OpenWrt",
        "comment": "!"
    },
    "allow.txt": {
        "title": "天影规则聚合 · 白名单规则",
        "desc": "误杀网址放行，保证正常网站正常访问",
        "comment": "!"
    }
}

# 表头/统计块本身改动后，正文条数未变也需要重写表头 → python title.py --force
FORCE = "--force" in sys.argv


HEADER_MARKER = "[TianYing Adblock Project]"
# 表头固定含 3 条 ===== 分隔线：标记后第 3 条分隔线即表头结束
HEADER_SEPARATORS = 3

# 来源分区标记（merge.py 写拦截/白名单分区，两种写法都兼容）：
#   ! 📋 规则来源：xxx   /   ! 📋 白名单来源：xxx
SECTION_PAT = re.compile(r"^!\s*(?:📋\s*)?(?:规则来源|白名单来源)：(.+?)\s*$")


def strip_header(content, comment="!"):
    """去掉本脚本上次生成的旧表头，只留正文。

    只认自己写的表头（首行标记，到第 HEADER_SEPARATORS 条 ===== 分隔线为止）；
    其余开头注释（如 adblock/dns 的来源分区头）一律保留，绝不误删。
    """
    lines = content.splitlines()
    if lines and lines[0].strip() == HEADER_MARKER:
        sep_pat = re.compile(rf"^{re.escape(comment)}\s*=+\s*$")
        seen = 0
        for i, line in enumerate(lines):
            if sep_pat.match(line.strip()):
                seen += 1
                if seen == HEADER_SEPARATORS:
                    lines = lines[i + 1:]
                    break
        else:
            # 结构异常时保守处理：只跳标记行，避免误删正文
            lines = lines[1:]
    while lines and lines[0].strip() == "":
        lines.pop(0)
    return "\n".join(lines).strip()


def parse_source_stats(clean_content):
    """解析正文里的来源分区，返回 [(来源名, 条数), ...]（按出现顺序，0 条的省略）。

    合计与 count_valid_lines 完全一致（同一套"非 !/#/[ 且非空"判定），
    已实测三个文件分区合计 == 文件总条数，差值 0。
    """
    counts, order = {}, []
    for line in clean_content.splitlines():
        s = line.strip()
        m = SECTION_PAT.match(s)
        if m:
            name = m.group(1)
            if name not in counts:
                counts[name] = 0
                order.append(name)
            continue
        if s and not s.startswith(("!", "#", "[")):
            if order:
                counts[order[-1]] += 1
    return [(name, counts[name]) for name in order if counts[name] > 0]


def render_stats_block(stats, comment):
    """渲染「规则来源统计」表头块（条数降序，千分位）。

    图标用 ☑（U+2611 基本区字符）：📈 等部分 emoji 在常见文本编辑器里
    会显示为破损占位框，☑ 在等宽/比例字体、彩色/黑白 emoji 环境下都能稳定渲染。
    数字列宽 8（右对齐千分位），行首仅留 1 空格，统计数字贴近行首更整齐。
    """
    if not stats:
        return ""
    rows = sorted(stats, key=lambda x: -x[1])
    lines = [
        f"{comment} ────────────────── ☑ 规则来源统计 ──────────────────",
    ]
    for name, n in rows:
        lines.append(f"{comment} {n:>8,} 条  {name}")
    lines.append(f"{comment} ────────────────────────────────────────────────")
    return "\n".join(lines) + "\n"


def extract_old_stats(content, comment="!"):
    """从旧表头里解析出上次写入的来源统计，用于检测统计块是否变化。

    只扫表头范围（标记行到第 HEADER_SEPARATORS 条分隔线），
    避免把 dns.txt 正文里 filter-dns 的「来源汇总」块误算进来。
    """
    lines = content.splitlines()
    if not lines or lines[0].strip() != HEADER_MARKER:
        return None
    # 注意：不能用 f-string 写 \s{2}（{2} 会被当成格式字段），这里用 \s\s
    pat = re.compile(rf"^{re.escape(comment)}\s+(\d[\d,]*) 条\s\s(.+)$")
    sep_pat = re.compile(rf"^{re.escape(comment)}\s*=+\s*$")
    result = []
    seen = 0
    for line in lines[1:]:
        if sep_pat.match(line.strip()):
            seen += 1
            if seen == HEADER_SEPARATORS:
                break
            continue
        m = pat.match(line)
        if m:
            result.append((m.group(2), int(m.group(1).replace(",", ""))))
    return result or None


def dns_effective_note(clean_content):
    """统计白名单里有多少条能在 DNS 层生效。

    上游白名单（尤其 AdGuard 官方那两个）大量使用路径级规则
    （`@@||x.com/tag/js$domain=y.com`）和正则，这些只在浏览器版 AdGuard
    里有效；DNS 层没有路径和来源页概念，只有 `@@||domain^` 与通配能用。
    不标出来，用户会以为 6767 条全在保护自己。
    """
    plain = wildcard = other = 0
    for line in clean_content.splitlines():
        s = line.strip()
        if not s or s.startswith(("!", "#", "[")):
            continue
        if re.fullmatch(r"@@\|\|[^/^$*]+\^", s):
            plain += 1
        elif s.startswith("@@||") and s.endswith("^"):
            wildcard += 1
        else:
            other += 1
    return plain, wildcard, other


changed = 0
for filename, cfg in file_config.items():
    file_path = os.path.join(rules_dir, filename)

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except OSError:
        content = ""

    clean_content = strip_header(content, cfg["comment"])
    line_count = count_valid_lines(clean_content, is_path=False)
    stats = parse_source_stats(clean_content)

    c = cfg["comment"]
    # 白名单额外提示 DNS 层实际生效口径（其余为浏览器版专用规则）
    note_block = ""
    if filename == "allow.txt":
        plain, wildcard, other = dns_effective_note(clean_content)
        note_block = (f"{c} 🧮 DNS 层可直接生效：{plain + wildcard:,} 条"
                      f"（纯域名 {plain:,} + 通配 {wildcard:,}）；"
                      f"另有 {other:,} 条为路径级 / $domain= / 正则，仅浏览器版 AdGuard 有效\n")

    # 正文是否变化：旧表头记录的条数 + 来源统计 + 白名单口径行都与本次一致
    # → 正文未变，不重写、保留原时间戳（避免无意义 diff 撑大仓库历史）。
    old_count = None
    for line in content.splitlines()[:15]:
        m = re.search(r"有效规则：(\d+) 条", line)
        if m:
            old_count = int(m.group(1))
            break
    body_unchanged = (old_count == line_count
                      and (not note_block or note_block.strip() in content)
                      and extract_old_stats(content, c) is not None
                      and sorted(extract_old_stats(content, c)) == sorted(stats))
    if body_unchanged and not FORCE:
        print(f"⏭️  {filename} | 正文无变化，保留原表头和时间戳")
        continue

    beijing_time = beijing_now()
    stats_block = render_stats_block(stats, c)

    # 统计块放在第 3 条 ===== 分隔线之前（表头内部），
    # 这样 strip_header 数到第 3 条分隔线即表头结束，新旧格式通用。
    header = f"""[TianYing Adblock Project]
{c} ======================================================================
{c} 📌 规则名称：{cfg['title']}
{c} 📝 规则说明：{cfg['desc']}
{c} 🌐 项目地址：https://github.com/xiaolei7172/ADS
{c} ⏰ 更新时间：{beijing_time}（北京时间）
{c} 📊 有效规则：{line_count} 条
{c} 🔄 更新频率：每日自动更新（北京时间 08:00）
{c} ======================================================================
{c} Title: 📌 {cfg['title']} 📌
{c} Description: ⏰ 更新时间 {beijing_time} | ✅ 有效规则 {line_count} 条
{note_block}""" + stats_block + f"""{c} ======================================================================
"""

    final = header + clean_content + "\n"

    try:
        with open(file_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(final)
        changed += 1
        print(f"✅ {filename} | 规则：{line_count} 条 | 来源分区：{len(stats)} 个")
    except OSError:
        print(f"❌ 写入失败：{filename}")

print(f"\n🎉 表头更新完成！本次实际更新 {changed}/3 个文件")
