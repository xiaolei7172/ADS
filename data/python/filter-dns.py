# -*- coding: utf-8 -*-
"""
从 adblock.txt 提取 DNS 拦截域名，生成 dns.txt。
改进点（相对旧版）：
  1. 【关键修复】旧版直接照抄所有 ||domain^，白名单在这里完全没生效——
     现在按父子域过滤白名单（@@||a.com^ 放行 a.com 及全部子域）；
  2. 域名合法性校验：通配符、端口、路径、非法字符一律不进 dns.txt；
  3. 全局去重（跨来源，先到先得），并输出统计；
  4. 【新增】dns.txt 按 adblock.txt 的来源分区输出：
     每个来源一个 "! 📋 规则来源：" 注释块，并在文件头部汇总各来源条数，
     与 adblock.txt 的来源标注保持一致，方便排查某条规则出自哪里。
"""
import os
import sys
from collections import OrderedDict

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from common import RULES_DIR, MOD_DIR, block_domain, hosts_target, build_allow_domains, is_allowed

os.makedirs(RULES_DIR, exist_ok=True)

input_path = os.path.join(RULES_DIR, "adblock.txt")
output_path = os.path.join(RULES_DIR, "dns.txt")

print("正在从 adblock.txt 提取 DNS 规则（含白名单过滤 + 来源分区）...")

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

# ==========================================
# 第一遍：按来源分区提取域名
# ==========================================
# adblock.txt 的来源注释块形如：
#   ! ==============================================
#   ! 📋 规则来源：xxx
#   ! 📝 规则说明：yyy
#   ! 🔗 原始地址：zzz
#   ! ==============================================
# 遇到 "! 📋 规则来源：" 即开启新分区；其后到下一条规则之间的
# "! 📝/! 🔗/! ⚠️" 注释行并入该分区的头部注释。
SECTIONS = OrderedDict()   # 来源名 -> {"comments": [...], "domains": [...]}
current = None             # 当前分区名
pending_comments = []      # 当前分区的注释行（随第一条规则落位）

DEFAULT_SECTION = "（未标注来源的规则）"

seen = set()
invalid = 0

def ensure_section(name, comments):
    if name not in SECTIONS:
        SECTIONS[name] = {"comments": comments, "domains": []}
    return SECTIONS[name]

with open(input_path, "r", encoding="utf-8", errors="ignore") as fin:
    for raw in fin:
        line = raw.strip()
        if not line:
            continue
        if line.startswith(("!", "#", "[")):
            if line.startswith("! 📋 规则来源："):
                name = line.replace("! 📋 规则来源：", "").strip() or DEFAULT_SECTION
                current = name
                pending_comments = [line]
            elif current is not None and pending_comments:
                # 来源块内后续说明行（📝 说明 / 🔗 地址 / ⚠️ 优先级等）
                pending_comments.append(line)
            continue

        d = block_domain(line)
        if d is None:
            # hosts 格式（0.0.0.0 domain）同样转为域名，不白白丢掉
            d = hosts_target(line)
        if d is None:
            invalid += 1
            continue
        if d in seen:
            continue
        seen.add(d)

        sec_name = current or DEFAULT_SECTION
        if current is None and not pending_comments:
            pending_comments = []
        sec = ensure_section(sec_name, pending_comments)
        pending_comments = []
        sec["domains"].append(d)

# ==========================================
# 第二遍：白名单过滤（本地自定义域豁免）+ 写出
# ==========================================
kept, by_white = 0, 0
per_source_kept = OrderedDict()

with open(output_path, "w", encoding="utf-8", newline="\n") as fout:
    fout.write("! 天影DNS拦截规则\n")
    fout.write("! 由 filter-dns.py 从 adblock.txt 提取，已应用白名单父子域过滤\n")
    fout.write("! 各来源分区见下（与 adblock.txt 的来源标注一致）\n")

    for name, sec in SECTIONS.items():
        kept_here = []
        for d in sec["domains"]:
            if is_allowed(d, allow_set) and d not in local_block:
                by_white += 1
                continue
            kept_here.append(d)
        if not kept_here:
            continue  # 该来源全部被放行，不输出空分区
        kept += len(kept_here)
        per_source_kept[name] = len(kept_here)

        fout.write("\n! ==============================================\n")
        for c in sec["comments"]:
            fout.write(f"{c}\n")
        fout.write(f"! 📊 本区规则：{len(kept_here)} 条\n")
        fout.write("! ==============================================\n")
        for d in kept_here:
            fout.write(f"||{d}^\n")

# 来源汇总插入头部：读回文件重写（规则量大时仍是秒级）
with open(output_path, "r", encoding="utf-8", newline="") as f:
    content = f.read()
head_end = content.index("\n\n") + 2  # 头部注释之后
summary_text = ""
if per_source_kept:
    summary_text = "\n! ────────────── 来源汇总 ──────────────\n"
    for name, n in per_source_kept.items():
        summary_text += f"!   {n:>7} 条  {name}\n"
    summary_text += "! ────────────────────────────────────────\n\n"
with open(output_path, "w", encoding="utf-8", newline="\n") as f:
    f.write(content[:head_end] + summary_text + content[head_end:])

print(f"✅ DNS 规则提取完成！已生成 → {output_path}")
print(f"📊 保留 {kept} 条（{len(per_source_kept)} 个来源）| 白名单放行 {by_white} 条 | 非法/跳过 {invalid} 条")
for name, n in per_source_kept.items():
    print(f"   · {n:>7} 条  {name}")
