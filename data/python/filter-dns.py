# -*- coding: utf-8 -*-
"""
从 adblock.txt 提取 DNS 拦截域名，生成 dns.txt。
改进点（相对旧版）：
  1. 【关键修复】旧版直接照抄所有 ||domain^，白名单在这里完全没生效——
     现在按父子域过滤白名单（@@||a.com^ 放行 a.com 及全部子域）；
  2. 域名合法性校验：通配符、端口、路径、非法字符一律不进 dns.txt；
  3. 全局去重（跨来源），并输出统计。
"""
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from common import RULES_DIR, MOD_DIR, block_domain, hosts_target, build_allow_domains, is_allowed

os.makedirs(RULES_DIR, exist_ok=True)

input_path = os.path.join(RULES_DIR, "adblock.txt")
output_path = os.path.join(RULES_DIR, "dns.txt")

print("正在从 adblock.txt 提取 DNS 规则（含白名单过滤）...")

allow_set = build_allow_domains()
print(f"📊 白名单域名：{len(allow_set)} 个")

# 本地自定义规则豁免白名单过滤（用户明确意图，优先级最高）
local_block = set()
local_path = os.path.join(MOD_DIR, "adblock.txt")
if os.path.exists(local_path):
    with open(local_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            d = block_domain(line)
            if d:
                local_block.add(d)
print(f"📌 本地自定义拦截域（豁免白名单）：{len(local_block)} 个")

seen = set()
kept, dup, by_white, invalid = [], 0, 0, 0

with open(input_path, "r", encoding="utf-8", errors="ignore") as fin, \
     open(output_path, "w", encoding="utf-8", newline="\n") as fout:
    fout.write("! 天影DNS拦截规则\n")
    fout.write("! 由 filter-dns.py 从 adblock.txt 提取，已应用白名单父子域过滤\n\n")
    for line in fin:
        line = line.strip()
        if not line or line.startswith(("!", "#", "[")):
            continue
        d = block_domain(line)
        if d is None:
            # hosts 格式（0.0.0.0 domain）同样转为域名，不白白丢掉
            d = hosts_target(line)
        if d is None:
            invalid += 1
            continue
        if d in seen:
            dup += 1
            continue
        seen.add(d)
        if is_allowed(d, allow_set) and d not in local_block:
            by_white += 1
            continue
        fout.write(f"||{d}^\n")
        kept.append(d)

print(f"✅ DNS 规则提取完成！已生成 → {output_path}")
print(f"📊 保留 {len(kept)} 条 | 白名单放行 {by_white} 条 | 重复 {dup} 条 | 非法/跳过 {invalid} 条")
