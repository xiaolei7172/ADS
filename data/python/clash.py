# -*- coding: utf-8 -*-
"""
从 dns.txt 生成 Clash/Mihomo rule-provider 域名集（mihomo.yaml）。
payload 中 '+.domain' 为后缀匹配（等价 AdGuard 的 ||domain^）。
使用方式：
  rule-providers:
    tianying-ad:
      type: http
      behavior: domain
      url: "https://testingcf.jsdelivr.net/gh/xiaolei7172/ADS@master/data/rules/mihomo.yaml"
      path: ./rules/tianying-ad.yaml
      interval: 43200
  rules:
    - RULE-SET,tianying-ad,REJECT
"""
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from common import RULES_DIR, block_domain

input_path = os.path.join(RULES_DIR, "dns.txt")
output_path = os.path.join(RULES_DIR, "mihomo.yaml")

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
    f.write("# 天影规则聚合 · Clash/Mihomo 域名集\n")
    f.write("# 由 dns.txt（已去重）自动转换；behavior: domain\n")
    f.write("# 📌 https://github.com/xiaolei7172/ADS | 🔄 每12小时自动更新\n")
    f.write("payload:\n")
    for d in uniq:
        f.write(f"  - '+.{d}'\n")

print(f"✅ Mihomo 域名集生成完成：{output_path}（{len(uniq)} 条，重复输入 {len(domains) - len(uniq)} 条）")
