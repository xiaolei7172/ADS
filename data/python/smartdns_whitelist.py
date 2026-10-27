# -*- coding: utf-8 -*-
"""
生成 SmartDNS 白名单规则（smartdns-whitelist.conf）。
改进点：
  1. 复用统一域名校验，跳过带空格等非法白名单行；
  2. 去重 + 父域去重：白名单里有 a.com 时，x.a.com 不再重复输出。
"""
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from common import RULES_DIR, allow_domain

input_file_path = os.path.join(RULES_DIR, "allow.txt")
output_file_path = os.path.join(RULES_DIR, "smartdns-whitelist.conf")

try:
    fin = open(input_file_path, "r", encoding="utf-8", errors="ignore")
except OSError:
    print(f"❌ 无法读取白名单文件：{input_file_path}")
    sys.exit(1)

domains = set()
not_domain = 0  # 合法的 @@ 规则，但带通配符/正则/路径，无法转成纯域名白名单
with fin:
    for line in fin:
        d = allow_domain(line)
        if d:
            domains.add(d)
        elif line.strip() and line.strip().startswith("@@"):
            not_domain += 1

# 父域去重：父域已在集合中时跳过子域
kept = []
for d in sorted(domains):
    parts = d.split(".")
    covered = any(".".join(parts[i:]) in domains for i in range(1, len(parts)))
    if not covered:
        kept.append(d)

with open(output_file_path, "w", encoding="utf-8", newline="\n") as fout:
    fout.write("# SmartDNS whitelist rules for 天影\n")
    fout.write("# Homepage: https://github.com/xiaolei7172/ADS\n")
    fout.write("# Format: address /domain/-\n\n")
    for d in kept:
        fout.write(f"address /{d}/-\n")

print(f"✅ 生成完成！共 {len(kept)} 条 SmartDNS 白名单规则"
      f"（去重前 {len(domains)} 条，父域去重 {len(domains) - len(kept)} 条，"
      f"非纯域名规则 {not_domain} 条不适用）")
