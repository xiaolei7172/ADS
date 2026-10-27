# -*- coding: utf-8 -*-
"""
发布前质量自检闸门：验证去重与文件结构的真实性，不合格 exit 1。
检查项：
  1. adblock.txt / allow.txt：0 精确重复（大小写不敏感）；
  2. dns.txt / qx.list / smartdns.conf / ad-domain.txt / hosts.txt：
     0 精确重复、0 父子域冗余（本地自定义域豁免，与 filter-dns.py 口径一致）；
  3. dns.txt 分区自洽：每个 "! 📊 本区规则：N 条" 与该分区实际行数一致，
     分区总和 = 总行数；
  4. 规则量下限：dns.txt 不得低于 50000 条（防上游大面积故障后带病发布）。
任何一项失败 → exit 1 拦截 git push，问题不会流到线上。
"""
import os
import sys
from collections import Counter

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from common import RULES_DIR, MOD_DIR, block_domain

DNS_FLOOR = 50000
DOMAIN_FILES = ["dns.txt", "qx.list", "smartdns.conf", "ad-domain.txt", "hosts.txt"]
RAW_FILES = ["adblock.txt", "allow.txt"]

errors = []

# 本地自定义拦截域：父子域检查豁免（与 filter-dns.py 同口径）
local_block = set()
local_path = os.path.join(MOD_DIR, "adblock.txt")
if os.path.exists(local_path):
    with open(local_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            d = block_domain(line)
            if d:
                local_block.add(d)


def rule_lines(path):
    """返回文件中的规则行（跳过注释/空行），hosts 文件取目标域"""
    out = []
    is_hosts = os.path.basename(path) == "hosts.txt"
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith(("!", "#", "[")):
                continue
            if is_hosts:
                parts = line.split()
                out.append(parts[1].lower() if len(parts) == 2 and parts[0] == "0.0.0.0" else None)
            else:
                out.append(line.lower())
    return [l for l in out if l]


# ---- 1/2. 精确重复 + 父子域冗余 ----
for name in RAW_FILES + DOMAIN_FILES:
    path = os.path.join(RULES_DIR, name)
    if not os.path.exists(path):
        errors.append(f"{name}: 文件不存在")
        continue
    lines = rule_lines(path)
    if not lines:
        errors.append(f"{name}: 0 条规则，异常")
        continue

    dup = [k for k, v in Counter(lines).items() if v > 1]
    if dup:
        errors.append(f"{name}: {len(dup)} 条精确重复，如 {dup[:3]}")

    if name in DOMAIN_FILES:
        s = set(lines)
        redundant = []
        for d in lines:
            if d in local_block:
                continue  # 本地自定义域豁免
            parts = d.split(".")
            if any(".".join(parts[i:]) in s for i in range(1, len(parts) - 1)):
                redundant.append(d)
        if redundant:
            errors.append(f"{name}: {len(redundant)} 条父子域冗余，如 {redundant[:3]}")

# ---- 3. dns.txt 分区自洽 ----
dns_path = os.path.join(RULES_DIR, "dns.txt")
with open(dns_path, "r", encoding="utf-8", errors="ignore") as f:
    dns_lines = [l.rstrip("\n") for l in f]

declared_total, actual_total, section_declared, section_actual = 0, 0, None, 0
for line in dns_lines:
    line = line.strip()
    if line.startswith("! 📊 本区规则："):
        if section_declared is not None and section_declared != section_actual:
            errors.append(f"dns.txt: 某分区标注 {section_declared} 条，实际 {section_actual} 条")
        try:
            section_declared = int(line.replace("! 📊 本区规则：", "").strip().split()[0])
        except ValueError:
            errors.append(f"dns.txt: 分区计数行解析失败 → {line!r}")
            section_declared = None
        section_actual = 0
        declared_total += section_declared or 0
    elif line.startswith("||") and line.endswith("^"):
        actual_total += 1
        section_actual += 1
if section_declared is not None and section_declared != section_actual:
    errors.append(f"dns.txt: 末分区标注 {section_declared} 条，实际 {section_actual} 条")
if declared_total != actual_total:
    errors.append(f"dns.txt: 分区计数总和 {declared_total} != 实际规则行 {actual_total}")

# ---- 4. 规则量下限 ----
if actual_total < DNS_FLOOR:
    errors.append(f"dns.txt: 仅 {actual_total} 条，低于绝对下限 {DNS_FLOOR}")

# ---- 结果 ----
if errors:
    print("🚫 质量自检未通过：")
    for e in errors:
        print(f"   ❌ {e}")
    sys.exit(1)

print(f"✅ 质量自检通过：全部文件 0 重复、0 父子域冗余，dns.txt {actual_total} 条，分区计数自洽")
