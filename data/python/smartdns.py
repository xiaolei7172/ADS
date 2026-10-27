# -*- coding: utf-8 -*-
"""
生成 SmartDNS 拦截规则（smartdns.conf）。
改进点：dns.txt 已在 filter-dns.py 校验过，这里复用同一校验兜底，
杜绝 address /xx/yy.html/# 这种路径/端口规则导致整份配置加载失败。
"""
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from common import RULES_DIR, block_domain

input_file_path = os.path.join(RULES_DIR, "dns.txt")
output_file_path = os.path.join(RULES_DIR, "smartdns.conf")

kept, skipped = 0, 0
try:
    fin = open(input_file_path, "r", encoding="utf-8", errors="ignore")
except OSError:
    print(f"❌ 无法读取文件：{input_file_path}")
    sys.exit(1)

with fin, open(output_file_path, "w", encoding="utf-8", newline="\n") as fout:
    fout.write("# SmartDNS rules for 天影\n")
    fout.write("# Homepage: https://github.com/xiaolei7172/ADS\n")
    fout.write("# Format: address /domain/#\n\n")
    for line in fin:
        line = line.strip()
        if not line or line.startswith(("!", "#", "[")):
            continue
        d = block_domain(line)
        if d is None:
            skipped += 1
            continue
        fout.write(f"address /{d}/#\n")
        kept += 1

print(f"✅ 生成完成！共 {kept} 条 SmartDNS 规则（跳过非法 {skipped} 条）")
