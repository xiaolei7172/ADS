# -*- coding: utf-8 -*-
"""
合并黑名单与白名单。
改进点（相对旧版）：
  1. 白名单过滤改为父子域匹配：@@||a.com^ 会放行 a.com 及其全部子域
     （旧版只做全等匹配，子域会被误拦）；
  2. 非法白名单行（如带空格的 @@||download- *.com^）不再进入匹配集合；
  3. 过滤混入的回环地址行（127.0.0.1 localhost 等）；
  4. 删除原第 4 段 dns.txt 生成——它会被 filter-dns.py 用 w 模式
     整个覆盖，属于死代码；dns.txt 统一由 filter-dns.py 生成。
"""
import os
import glob
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from common import (
    RULES_DIR, TMP_DIR, MOD_DIR, REPO_ROOT,
    allow_domain, block_domain, is_allowed, is_junk_hosts_line, count_valid_lines,
)

os.makedirs(TMP_DIR, exist_ok=True)
os.makedirs(RULES_DIR, exist_ok=True)

# ==========================================
# 智能提取头部信息
# ==========================================
def get_rule_meta(file_path):
    title = ""
    desc = ""
    source_name = "未知来源"
    source_url = "未知地址"

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f.readlines()[:80]:
                line = line.strip()
                if line.startswith("! Title:"):
                    title = line.replace("! Title:", "").strip()
                if line.startswith("! Description:"):
                    desc = line.replace("! Description:", "").strip()
                if line.startswith("! 📋 规则来源："):
                    source_name = line.replace("! 📋 规则来源：", "").strip()
                if line.startswith("! 🔗 原始地址："):
                    source_url = line.replace("! 🔗 原始地址：", "").strip()
    except OSError:
        pass

    if not desc.strip():
        desc = "广告拦截规则"
    final_name = f"{source_name} [{title}]" if title.strip() else source_name
    return final_name, desc, source_url

# ==========================================
# 1. 收集所有白名单（内置 + 远程 + 本地）
# ==========================================
print("🚀 收集全部白名单（内置+远程+本地）")
all_white_raw = set()
ad_files = sorted(glob.glob(os.path.join(TMP_DIR, "adblock_*.txt")))
allow_files = sorted(glob.glob(os.path.join(TMP_DIR, "allow_*.txt")))
local_white_path = os.path.join(MOD_DIR, "whitelist.txt")
local_black_path = os.path.join(MOD_DIR, "adblock.txt")

def collect_white(path):
    n = 0
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if line.startswith("@@"):
                all_white_raw.add(line)
                n += 1
    return n

for file in ad_files:
    collect_white(file)
for file in allow_files:
    collect_white(file)
if os.path.exists(local_white_path):
    n = collect_white(local_white_path)
    print(f"✅ 已加载本地白名单：data/mod/whitelist.txt（{n} 条）")

# 白名单域名集合：只收合法行，跳过带空格等非法行
allow_domain_set = set()
for rule in all_white_raw:
    d = allow_domain(rule)
    if d:
        allow_domain_set.add(d)
print(f"📊 合法白名单域名：{len(allow_domain_set)} 个"
      f"（丢弃非法白名单行 {len(all_white_raw) - len([r for r in all_white_raw if allow_domain(r)])} 条）")

# ==========================================
# 2. 合并黑名单（自动过滤 + 写入本地自定义）
# ==========================================
print("🚀 合并黑名单并过滤冲突")
black_output = []
black_set = set()
blocked_by_white = 0
junk_skipped = 0

def append_black(path):
    global blocked_by_white, junk_skipped
    final_name, desc, url = get_rule_meta(path)
    black_output.extend([
        "! ==============================================",
        f"! 📋 规则来源：{final_name}",
        f"! 📝 规则说明：{desc}",
        f"! 🔗 原始地址：{url}",
        "! ==============================================",
    ])
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith(("!", "#", "[", "@@")):
                continue
            # 回环地址行（127.0.0.1 localhost 之类）直接丢弃
            if is_junk_hosts_line(line):
                junk_skipped += 1
                continue
            if line not in black_set:
                black_set.add(line)
                black_output.append(line)

for file in ad_files:
    append_black(file)

# 本地黑名单（优先级最高）
local_rule_lines = set()  # 本地自定义规则：豁免白名单过滤（用户明确意图）
if os.path.exists(local_black_path):
    print("✅ 已加载本地黑名单：data/mod/adblock.txt")
    black_output.extend([
        "! ==============================================",
        "! 📋 规则来源：本地自定义规则（data/mod/adblock.txt）",
        "! ⚠️ 优先级：最高",
        "! ==============================================",
    ])
    with open(local_black_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith(("!", "#", "[", "@@")):
                continue
            local_rule_lines.add(line)
            if line not in black_set:
                black_set.add(line)
                black_output.append(line)

# 白名单过滤统一放最后：黑名单里逐行判断代价高，改为
# 先收集 ||domain^ 行，再按父子域过滤。
# 本地自定义规则（data/mod/adblock.txt）豁免过滤——用户明确要拦的域，
# 即使被远程白名单放行也照样拦（「优先级：最高」落到代码上）。
final_black = []
exempt = 0
for line in black_output:
    if line in local_rule_lines:
        final_black.append(line)
        continue
    if line.startswith("||") and line.endswith("^"):
        dom = line[2:-1].lower()
        if is_allowed(dom, allow_domain_set):
            blocked_by_white += 1
            continue
    final_black.append(line)

with open(os.path.join(RULES_DIR, "adblock.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(final_black) + "\n")

# ==========================================
# 3. 合并完整白名单（含本地自定义）
# ==========================================
print("🚀 合并完整白名单（含本地自定义）")
white_output = []

def append_white(path, tag):
    final_name, _, _ = get_rule_meta(path)
    tmp = []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if line.startswith("@@") and line in all_white_raw:
                tmp.append(line)
    if tmp:
        white_output.extend([
            "! ==============================================",
            f"! 📋 白名单来源：{final_name}（{tag}）",
            "! ==============================================",
        ])
        white_output.extend(tmp)

for file in ad_files:
    append_white(file, "规则内置")
for file in allow_files:
    append_white(file, "远程白名单")
if os.path.exists(local_white_path):
    final_name, _, _ = get_rule_meta(local_white_path)
    tmp = []
    with open(local_white_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if line.startswith("@@") and line in all_white_raw:
                tmp.append(line)
    if tmp:
        white_output.extend([
            "! ==============================================",
            f"! 📋 白名单来源：本地自定义规则（data/mod/whitelist.txt）",
            "! ⚠️ 优先级：最高",
            "! ==============================================",
        ])
        white_output.extend(tmp)

final_white = list(dict.fromkeys(white_output))

# 本地自定义拦截域（data/mod/adblock.txt）覆盖的 @@ 行必须从白名单成品剔除：
# AdGuard 中 @@ 放行优先于拦截，不剔除会让本地规则对双规则订阅用户失效。
local_block_domains = set()
if os.path.exists(local_black_path):
    with open(local_black_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            d = block_domain(line)
            if d:
                local_block_domains.add(d)
if local_block_domains:
    before = len(final_white)
    final_white = [l for l in final_white
                   if not (l.startswith("@@") and is_allowed(allow_domain(l) or "", local_block_domains))]
    print(f"✂️  因本地自定义拦截域，从白名单剔除 {before - len(final_white)} 条放行规则")

with open(os.path.join(RULES_DIR, "allow.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(final_white) + "\n")

# ==========================================
# 完成
# ==========================================
print("\n✅ 全部合并完成！本地黑白名单均已完整写入！")
print(f"📊 黑名单：{count_valid_lines(os.path.join(RULES_DIR, 'adblock.txt'))} 条")
print(f"📊 白名单：{len(all_white_raw)} 条")
print(f"🚫 因白名单（父子域）放行而移除的拦截规则：{blocked_by_white} 条（本地自定义规则豁免）")
print(f"🧹 丢弃回环/垃圾行：{junk_skipped} 条")
print("ℹ️  dns.txt 由 filter-dns.py 统一生成（原第 4 段会被它覆盖，已移除）")
