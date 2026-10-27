# -*- coding: utf-8 -*-
"""
生成纯域名黑名单（ad-domain.txt）。
改进点：复用统一域名校验（通配符/端口/路径/非法字符不入列）+ 输出统计。
"""
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from common import RULES_DIR, block_domain

input_file_path = os.path.join(RULES_DIR, "dns.txt")
output_file_path = os.path.join(RULES_DIR, "ad-domain.txt")

print("正在提取域名列表...")

kept, skipped = 0, 0
with open(input_file_path, "r", encoding="utf-8", errors="ignore") as fin, \
     open(output_file_path, "w", encoding="utf-8", newline="\n") as fout:
    fout.write("[Host]\n")
    fout.write("# 天影 纯净域名黑名单\n")
    fout.write("# Github: https://github.com/xiaolei7172/ADS\n")
    fout.write("# 自动提取：只保留纯域名，适配 AdGuard Home / 路由器\n\n")
    for line in fin:
        line = line.strip()
        if not line or line.startswith(("!", "#", "[")):
            continue
        d = block_domain(line)
        if d is None:
            skipped += 1
            continue
        fout.write(f"{d}\n")
        kept += 1

print(f"✅ 提取完成！共提取 {kept} 个有效域名（跳过非法 {skipped} 条）")
print(f"📁 输出路径：{output_file_path}")
