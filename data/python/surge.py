# -*- coding: utf-8 -*-
"""
从 dns.txt 生成 Surge 规则集（surge.list，RULE-SET 格式）。
使用方式（Surge/Loon/Stash 等）：
  [Rule]
  RULE-SET,https://testingcf.jsdelivr.net/gh/xiaolei7172/ADS@master/data/rules/surge.list,REJECT
"""
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from common import RULES_DIR, block_domain

input_path = os.path.join(RULES_DIR, "dns.txt")
output_path = os.path.join(RULES_DIR, "surge.list")

domains = []
with open(input_path, "r", encoding="utf-8", errors="ignore") as f:
    for raw in f:
        line = raw.strip()
        if not line or line.startswith(("!", "#", "[")):
            continue
        d = block_domain(line)
        if d:
            domains.append(d)

seen = set()
uniq = []
for d in domains:
    if d not in seen:
        seen.add(d)
        uniq.append(d)

with open(output_path, "w", encoding="utf-8", newline="\n") as f:
    f.write("# 天影广告拦截规则（Surge RULE-SET）\n")
    f.write("# 由 dns.txt（已去重）自动转换 | https://github.com/xiaolei7172/ADS | 每12小时自动更新\n")
    for d in uniq:
        f.write(f"DOMAIN-SUFFIX,{d}\n")

print(f"✅ Surge 规则集生成完成：{output_path}（{len(uniq)} 条，重复输入 {len(domains) - len(uniq)} 条）")
