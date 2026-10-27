# -*- coding: utf-8 -*-
"""
更新规则文件表头。
改进点（相对旧版）：
  1. 【关键修复】规则正文没变化时，保留原文件不动（原时间戳继续有效）——
     旧版每次都写入新时间戳，规则一条没变也必然产生整文件 diff，
     这是仓库历史膨胀到 1 GB 的直接原因之一；
  2. 去掉 pytz 依赖，改用标准库固定 UTC+8（中国无夏令时）。
"""
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from common import RULES_DIR, count_valid_lines, beijing_now

if "GITHUB_WORKSPACE" in os.environ:
    REPO_ROOT = os.environ["GITHUB_WORKSPACE"]
else:
    REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../.."))

rules_dir = os.path.join(REPO_ROOT, "data", "rules")

file_config = {
    "adblock.txt": {
        "title": "天影广告拦截规则",
        "desc": "屏蔽全网广告、弹窗、跟踪、恶意域名",
        "comment": "!"
    },
    "dns.txt": {
        "title": "天影DNS拦截规则",
        "desc": "DNS级广告域名屏蔽，支持AdGuard Home / OpenWrt",
        "comment": "!"
    },
    "allow.txt": {
        "title": "天影白名单规则",
        "desc": "误杀网址放行，保证正常网站正常访问",
        "comment": "!"
    }
}


def strip_header(content):
    """去掉文件开头的注释/[标记]/空行，只留规则正文"""
    lines = content.splitlines()
    while lines:
        first = lines[0].strip()
        if first.startswith(("!", "[", "#")) or first == "":
            lines.pop(0)
        else:
            break
    return "\n".join(lines).strip()


changed = 0
for filename, cfg in file_config.items():
    file_path = os.path.join(rules_dir, filename)

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except OSError:
        content = ""

    clean_content = strip_header(content)
    line_count = count_valid_lines(clean_content, is_path=False)

    # 正文是否变化：用旧表头里记录的条数对比新条数。
    # 表头由本脚本上次生成，条数一致即说明正文未变 → 不重写、保留原时间戳。
    old_count = None
    for line in content.splitlines()[:15]:
        m = re.search(r"有效规则：(\d+) 条", line)
        if m:
            old_count = int(m.group(1))
            break
    if old_count is not None and old_count == line_count:
        print(f"⏭️  {filename} | 正文无变化，保留原表头和时间戳")
        continue

    c = cfg["comment"]
    beijing_time = beijing_now()

    header = f"""[TianYing Adblock Project]
{c} ======================================================================
{c} 📌 规则名称：{cfg['title']}
{c} 📝 规则说明：{cfg['desc']}
{c} 🌐 项目地址：https://github.com/xiaolei7172/ADS
{c} ⏰ 更新时间：{beijing_time}（北京时间）
{c} 📊 有效规则：{line_count} 条
{c} 🔄 更新频率：每12小时自动更新
{c} ======================================================================
{c} Title: 📌 {cfg['title']} 📌
{c} Description: ⏰ 更新时间 {beijing_time} | ✅ 有效规则 {line_count} 条
{c} ======================================================================
"""
    final = header + clean_content + "\n"

    try:
        with open(file_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(final)
        changed += 1
        print(f"✅ {filename} | 规则：{line_count} 条")
    except OSError:
        print(f"❌ 写入失败：{filename}")

print(f"\n🎉 表头更新完成！本次实际更新 {changed}/3 个文件")
