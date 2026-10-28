# -*- coding: utf-8 -*-
"""
生成 Quantumult X 规则（qx.list）。
改进点（相对旧版）：
  1. 删除旧的子串匹配白名单删除逻辑——`any(dom in line)` 会把
     t.co 白名单误伤所有 *.t.com 域名（ad.tencent.com 就是这样消失的）；
     dns.txt 在 filter-dns.py 已按父子域过滤白名单，这里只需转换格式；
  2. 跳过通配符域名：QX 的 DOMAIN 类型不支持 *，写进去是无效规则。
"""
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from common import RULES_DIR, block_domain

input_file_path = os.path.join(RULES_DIR, "dns.txt")
output_file_path = os.path.join(RULES_DIR, "qx.list")

kept, skipped = 0, 0
with open(input_file_path, "r", encoding="utf-8", errors="ignore") as fin, \
     open(output_file_path, "w", encoding="utf-8", newline="\n") as fout:
    fout.write("# 天影规则聚合 · Quantumult X 拦截规则\n")
    fout.write("# Github: https://github.com/xiaolei7172/ADS\n")
    fout.write("# Format: DOMAIN,domain,reject\n\n")
    for line in fin:
        line = line.strip()
        if not line or line.startswith(("!", "#", "[")):
            continue
        d = block_domain(line)  # 通配符/端口/路径在这里统一被拒
        if d is None:
            skipped += 1
            continue
        fout.write(f"DOMAIN,{d},reject\n")
        kept += 1

print(f"✅ Quantumult X 规则生成完成：qx.list（{kept} 条，跳过非法 {skipped} 条）")
