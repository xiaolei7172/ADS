# -*- coding: utf-8 -*-
"""
生成 HOSTS 格式规则（hosts.txt）。
背景：README 曾列出 hosts_merged.txt / hosts_adblock.txt / hosts_dns.txt 三个文件，
由已停用的 hosts_merge.py 生成（workflow 中该步骤被注释），三个链接全部 404。
现改为从 filter-dns.py 落盘的**折叠前**域名集生成：
  - hosts 只能精确匹配，`0.0.0.0 a.b.com` 拦不到 `x.a.b.com`。
    dns.txt 为 AdGuard 语义做过父子域折叠（父域存在即删子域），
    若 hosts 跟着折叠，被删掉的那批子域就永远拦不到——实测约 1.58 万个；
  - 所以优先读 data/tmp/dns-unfolded.txt（折叠前，已过白名单 + 跨源去重），
    该文件不存在时（单独跑 hosts.py 的场景）退回 dns.txt；
  - 0.0.0.0 格式，适用于 AdGuard Home / OpenWrt / 安卓无 root 等场景。
"""
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from common import RULES_DIR, block_domain, beijing_now

# 兜底：万一上游给了裸域名（无 ||...^ 包裹），也认
BARE_DOMAIN = re.compile(
    r"^[a-z0-9](?:[a-z0-9_-]*[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9_-]*[a-z0-9])?)+$")


def parse_domain(line):
    d = block_domain(line)
    if d:
        return d
    s = line.strip().lower()
    return s if BARE_DOMAIN.match(s) else None

UNFOLDED_PATH = os.path.join(os.path.dirname(RULES_DIR), "tmp", "dns-unfolded.txt")
FALLBACK_PATH = os.path.join(RULES_DIR, "dns.txt")
output_path = os.path.join(RULES_DIR, "hosts.txt")

if os.path.exists(UNFOLDED_PATH):
    input_path = UNFOLDED_PATH
    desc = "由 dns.txt 折叠前的完整域名集转换，含全部子域，覆盖与 AdGuard 语义对齐"
else:
    input_path = FALLBACK_PATH
    desc = "由 dns.txt（已去重）自动转换；未找到折叠前域名集，子域覆盖不完整"
    print(f"⚠️ 未找到 {UNFOLDED_PATH}，退回折叠后的 dns.txt（子域覆盖会不完整）")

domains = []
with open(input_path, "r", encoding="utf-8", errors="ignore") as f:
    for raw in f:
        line = raw.strip()
        if not line or line.startswith(("!", "#", "[")):
            continue
        d = parse_domain(line)
        if d:
            domains.append(d)

# 保险起见再做一次精确去重（上游文件可能含重复）
seen = set()
uniq = []
for d in domains:
    if d not in seen:
        seen.add(d)
        uniq.append(d)

header = f"""# 天影规则聚合 · HOSTS 版
# {desc}
# ⚠️ hosts 只能精确匹配，拦不到未列出的子域；需要完整子域覆盖请用 dns.txt / smartdns.conf / surge.list
# 📌 项目地址：https://github.com/xiaolei7172/ADS
# ⏰ 更新时间：{beijing_now()}（北京时间） | 📊 有效规则：{len(uniq)} 条
# 🔄 更新频率：每日自动更新（北京时间 08:00）
"""
with open(output_path, "w", encoding="utf-8", newline="\n") as f:
    f.write(header)
    for d in uniq:
        f.write(f"0.0.0.0 {d}\n")

print(f"✅ HOSTS 规则生成完成：{output_path}（{len(uniq)} 条，重复输入 {len(domains) - len(uniq)} 条）")
