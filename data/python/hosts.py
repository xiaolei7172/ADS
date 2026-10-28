# -*- coding: utf-8 -*-
"""
从 dns.txt 生成 HOSTS 格式规则（hosts.txt）。
背景：README 曾列出 hosts_merged.txt / hosts_adblock.txt / hosts_dns.txt 三个文件，
由已停用的 hosts_merge.py 生成（workflow 中该步骤被注释），三个链接全部 404。
现改为从**已去重的** dns.txt 单一来源生成一份 hosts.txt：
  - 数据与 dns.txt 完全一致（0 精确重复 + 0 父子域冗余）；
  - 0.0.0.0 格式，适用于 AdGuard Home / OpenWrt / 安卓无 root 等场景；
  - 旧的三个文件与死代码 hosts_merge.py 一并淘汰。
"""
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from common import RULES_DIR, block_domain, beijing_now

input_path = os.path.join(RULES_DIR, "dns.txt")
output_path = os.path.join(RULES_DIR, "hosts.txt")

domains = []
with open(input_path, "r", encoding="utf-8", errors="ignore") as f:
    for raw in f:
        line = raw.strip()
        if not line or line.startswith(("!", "#", "[")):
            continue
        d = block_domain(line)
        if d:
            domains.append(d)

# 保险起见再做一次精确去重（正常情况下 dns.txt 已保证 0 重复）
seen = set()
uniq = []
for d in domains:
    if d not in seen:
        seen.add(d)
        uniq.append(d)

header = f"""# 天影规则聚合 · HOSTS 版
# 由 dns.txt（已去重）自动转换，规则与 dns.txt 完全一致
# 📌 项目地址：https://github.com/xiaolei7172/ADS
# ⏰ 更新时间：{beijing_now()}（北京时间） | 📊 有效规则：{len(uniq)} 条
# 🔄 更新频率：每12小时自动更新
"""
with open(output_path, "w", encoding="utf-8", newline="\n") as f:
    f.write(header)
    for d in uniq:
        f.write(f"0.0.0.0 {d}\n")

print(f"✅ HOSTS 规则生成完成：{output_path}（{len(uniq)} 条，重复输入 {len(domains) - len(uniq)} 条）")
