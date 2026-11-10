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
import json
from collections import OrderedDict

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from common import RULES_DIR, MOD_DIR, block_domain, hosts_target, build_allow_domains, is_allowed, beijing_now

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
dup = 0

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
            dup += 1
            continue
        seen.add(d)

        sec_name = current or DEFAULT_SECTION
        if current is None and not pending_comments:
            pending_comments = []
        sec = ensure_section(sec_name, pending_comments)
        pending_comments = []
        sec["domains"].append(d)

# ==========================================
# 第二遍：白名单过滤（本地自定义域豁免）
# ==========================================
kept, by_white = 0, 0
filtered_sections = OrderedDict()  # 来源名 -> 白名单过滤后的域名列表

for name, sec in SECTIONS.items():
    kept_here = []
    for d in sec["domains"]:
        if is_allowed(d, allow_set) and d not in local_block:
            by_white += 1
            continue
        kept_here.append(d)
    if kept_here:
        filtered_sections[name] = kept_here
        kept += len(kept_here)

# ==========================================
# 第三遍：父子域语义去重（拆父域清单豁免）
# ||parent^ 在 AdGuard/hosts 语义下覆盖全部子域，
# 若父域本身已保留，其子域规则即冗余，剔除。
# 注意必须在白名单过滤之后：若父域被白名单放行而子域没有，
# 子域必须保留。本地自定义域（用户明确意图）始终保留原文。
# ==========================================
# 拆父域：data/mod/split-parents.txt 收录「被本地白名单点名放行功能子域」的父域。
# 这类父域一旦整域进产物，单文件格式（dnsmasq/qx/surge/mihomo）无法表达
# 「拦父域但放行某个子域」，白名单子域即被架空（check-quality 第 6 关会熔断）。
# 处理：产物中不输出父域本身，其全部已收录子域照常保留（白名单子域已被
# 第二遍剔除），拦截粒度从整域细化到子域。hosts.txt 走精确匹配不受影响。
SPLIT_PATH = os.path.join(MOD_DIR, "split-parents.txt")
split_parents = set()
if os.path.exists(SPLIT_PATH):
    with open(SPLIT_PATH, "r", encoding="utf-8", errors="ignore") as f:
        for raw in f:
            s = raw.split("!")[0].strip().lower()
            if s:
                split_parents.add(s)
if split_parents:
    print(f"🪓 拆父域清单：{len(split_parents)} 个（data/mod/split-parents.txt），"
          f"产物中以子域替代整域")

kept_all = set()
for doms in filtered_sections.values():
    kept_all.update(doms)

# 折叠前的完整域名集（已白名单过滤 + 跨来源去重）留给 hosts.py：
# hosts 只能精确匹配，若跟着 dns.txt 一起折叠，被折叠掉的子域就永远拦不到了。
# 写 data/tmp 而非 data/rules，避免多一份对外发布的产物。
UNFOLDED_PATH = os.path.join(os.path.dirname(RULES_DIR), "tmp", "dns-unfolded.txt")
UNFOLDED_META = os.path.join(os.path.dirname(RULES_DIR), "tmp", "dns-unfolded.meta.json")
try:
    os.makedirs(os.path.dirname(UNFOLDED_PATH), exist_ok=True)
    with open(UNFOLDED_PATH, "w", encoding="utf-8", newline="\n") as f:
        for doms in filtered_sections.values():
            for d in doms:
                f.write(f"||{d}^\n")
    # 契约文件：hosts.py 靠它确认「折叠前域名集确实由本次管线生成」。
    # 旧实现是隐式契约——dl.py 开头 rmtree(tmp)，hosts.py 找不到就静默退回折叠版，
    # 于是发布一份子域覆盖不完整的 hosts.txt 而没人发现。
    with open(UNFOLDED_META, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"count": len(kept_all), "generated": beijing_now()}, f, ensure_ascii=False)
    print(f"📦 折叠前域名集已落盘：{UNFOLDED_PATH}（{len(kept_all)} 条，供 hosts.txt 覆盖子域）")
except OSError as e:
    print(f"⚠️ 折叠前域名集写入失败：{e}")

def has_ancestor(d, pool):
    parts = d.split(".")
    for i in range(1, len(parts) - 1):
        if ".".join(parts[i:]) in pool:
            return True
    return False

collapsed = 0
split_out = 0
per_source_kept = OrderedDict()
chunks = []          # 分区正文先攒在内存里：5 MB 文字，换掉「写完读回再重写」的两轮 IO

HEAD_LINES = (
    "! 本文件由 filter-dns.py 从 adblock.txt 提取（项目：天影规则聚合）",
    "! 已应用：白名单父子域过滤 + 父子域语义去重",
    "! 各来源分区见下（与 adblock.txt 的来源标注一致）",
)

for name, doms in filtered_sections.items():
    final_doms = []
    # 拆父域的父域不参与折叠判定：其子域不再视为被覆盖，照常保留到各自来源分区
    collapse_pool = kept_all - split_parents
    for d in doms:
        if d not in local_block and has_ancestor(d, collapse_pool):
            collapsed += 1
            continue
        if d in split_parents:
            split_out += 1
            continue
        final_doms.append(d)
    if not final_doms:
        continue  # 该来源规则全部冗余/被放行，不输出空分区
    per_source_kept[name] = len(final_doms)

    buf = ["\n! ==============================================\n"]
    for c in SECTIONS[name]["comments"]:
        buf.append(f"{c}\n")
    buf.append(f"! 📊 本区规则：{len(final_doms)} 条\n")
    buf.append("! ==============================================\n")
    for d in final_doms:
        buf.append(f"||{d}^\n")
    chunks.append("".join(buf))

# 来源汇总（各区条数在第一遍循环里就已知，不必回读文件）
summary_text = ""
if per_source_kept:
    summary_text = "\n! ────────────── 来源汇总 ──────────────\n"
    for name, n in per_source_kept.items():
        summary_text += f"!   {n:>7} 条  {name}\n"
    summary_text += "! ────────────────────────────────────────\n\n"

body = "".join(chunks)
# 与旧版切分点对齐：旧实现把第一个分区的前导空行算进头部，这里显式补回
head_text = "".join(f"{line}\n" for line in HEAD_LINES)
out = head_text + "\n" + summary_text + (body[1:] if body else "")
with open(output_path, "w", encoding="utf-8", newline="\n") as f:
    f.write(out)

kept_final = sum(per_source_kept.values())
print(f"✅ DNS 规则提取完成！已生成 → {output_path}")
print(f"📊 最终保留 {kept_final} 条（{len(per_source_kept)} 个来源）| 白名单放行 {by_white} 条 | 跨来源重复 {dup} 条 | 父子域冗余剔除 {collapsed} 条 | 拆父域移除 {split_out} 条 | 非法/跳过 {invalid} 条")
for name, n in per_source_kept.items():
    print(f"   · {n:>7} 条  {name}")
