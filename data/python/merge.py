import os
import glob
import re

# ==========================================
# 目录配置（完全对齐你的脚本）
# ==========================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../.."))
TMP_DIR = os.path.join(REPO_ROOT, "data", "tmp")
MOD_DIR = os.path.join(REPO_ROOT, "data", "mod")
TARGET_DIR = os.path.join(REPO_ROOT, "data", "rules")

os.makedirs(TMP_DIR, exist_ok=True)
os.makedirs(TARGET_DIR, exist_ok=True)

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
            lines = f.readlines()
            for line in lines[:80]:
                line = line.strip()
                if line.startswith("! Title:"):
                    title = line.replace("! Title:", "").strip()
                if line.startswith("! Description:"):
                    desc = line.replace("! Description:", "").strip()
                if line.startswith("! 📋 规则来源："):
                    source_name = line.replace("! 📋 规则来源：", "").strip()
                if line.startswith("! 🔗 原始地址："):
                    source_url = line.replace("! 🔗 原始地址：", "").strip()
    except:
        pass

    if not desc.strip():
        desc = "广告拦截规则"
    final_name = f"{source_name} [{title}]" if title.strip() else source_name
    return final_name, desc, source_url

# ==========================================
# 工具：从白名单提取域名
# ==========================================
def extract_allow_domains(allow_rules_list):
    allow_domains = set()
    domain_pat = re.compile(r"@@\|\|([a-zA-Z0-9.-]+)\^")
    for rule in allow_rules_list:
        m = domain_pat.search(rule)
        if m:
            allow_domains.add(m.group(1))
    return allow_domains

# ==========================================
# 1. 收集所有白名单（内置 + 远程 + 本地）
# ==========================================
print("🚀 收集全部白名单（内置+远程+本地）")
all_white_raw = set()
ad_files = sorted(glob.glob(os.path.join(TMP_DIR, "adblock_*.txt")))
allow_files = sorted(glob.glob(os.path.join(TMP_DIR, "allow_*.txt")))
local_white_path = os.path.join(MOD_DIR, "whitelist.txt")
local_black_path = os.path.join(MOD_DIR, "adblock.txt")

# 1. 广告规则内置白名单
for file in ad_files:
    with open(file, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if line.startswith("@@"):
                all_white_raw.add(line)

# 2. 远程下载白名单
for file in allow_files:
    with open(file, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if line.startswith("@@"):
                all_white_raw.add(line)

# 3. 本地自定义白名单
if os.path.exists(local_white_path):
    with open(local_white_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if line.startswith("@@"):
                all_white_raw.add(line)
    print("✅ 已加载本地白名单：data/mod/whitelist.txt")

allow_domain_set = extract_allow_domains(all_white_raw)

# ==========================================
# 2. 合并黑名单（自动过滤 + 写入本地自定义）
# ==========================================
print("🚀 合并黑名单并过滤冲突")
black_output = []
black_set = set()

# 远程黑名单
for file in ad_files:
    final_name, desc, url = get_rule_meta(file)
    black_output.extend([
        "! ==============================================",
        f"! 📋 规则来源：{final_name}",
        f"! 📝 规则说明：{desc}",
        f"! 🔗 原始地址：{url}",
        "! ==============================================",
    ])

    with open(file, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith(("!", "#", "[", "@@")):
                continue

            domain_match = re.fullmatch(r"\|\|([a-zA-Z0-9.-]+)\^", line)
            if domain_match:
                block_domain = domain_match.group(1)
                if block_domain in allow_domain_set:
                    continue

            if line not in black_set:
                black_set.add(line)
                black_output.append(line)

# ======================
# 【你要的功能】本地黑名单 写入完整注释
# ======================
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
            
            domain_match = re.fullmatch(r"\|\|([a-zA-Z0-9.-]+)\^", line)
            if domain_match:
                block_domain = domain_match.group(1)
                if block_domain in allow_domain_set:
                    continue

            if line not in black_set:
                black_set.add(line)
                black_output.append(line)

with open(os.path.join(TARGET_DIR, "adblock.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(black_output) + "\n")

# ==========================================
# 3. 合并完整白名单（含本地自定义）
# ==========================================
print("🚀 合并完整白名单（含本地自定义）")
white_output = []

# 白名单1：广告规则内置
for file in ad_files:
    final_name, desc, url = get_rule_meta(file)
    tmp = []
    with open(file, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if line.startswith("@@") and line in all_white_raw:
                tmp.append(line)
    if tmp:
        white_output.extend([
            "! ==============================================",
            f"! 📋 白名单来源：{final_name}（规则内置）",
            "! ==============================================",
        ])
        white_output.extend(tmp)

# 白名单2：远程下载
for file in allow_files:
    final_name, desc, url = get_rule_meta(file)
    tmp = []
    with open(file, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if line.startswith("@@") and line in all_white_raw:
                tmp.append(line)
    if tmp:
        white_output.extend([
            "! ==============================================",
            f"! 📋 白名单来源：{final_name}（远程白名单）",
            "! ==============================================",
        ])
        white_output.extend(tmp)

# 白名单3：本地自定义
if os.path.exists(local_white_path):
    tmp = []
    with open(local_white_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if line.startswith("@@") and line in all_white_raw:
                tmp.append(line)
    if tmp:
        white_output.extend([
            "! ==============================================",
            "! 📋 白名单来源：本地自定义规则（data/mod/whitelist.txt）",
            "! ⚠️ 优先级：最高",
            "! ==============================================",
        ])
        white_output.extend(tmp)

final_white = list(dict.fromkeys(white_output))
with open(os.path.join(TARGET_DIR, "allow.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(final_white) + "\n")

# ==========================================
# 4. DNS 域名（过滤白名单）
# ==========================================
print("🚀 生成 DNS 域名列表")
dns_output = []
dns_set = set()

for file in ad_files:
    final_name, desc, url = get_rule_meta(file)
    tmp_domains = set()
    with open(file, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            m = re.fullmatch(r"\|\|([a-zA-Z0-9.-]+)\^", line)
            if m:
                domain = m.group(1)
                if domain not in allow_domain_set and domain not in dns_set:
                    tmp_domains.add(domain)
    if tmp_domains:
        dns_output.extend([
            "! ==============================================",
            f"! 📋 规则来源：{final_name}",
            "! ==============================================",
        ])
        for d in sorted(tmp_domains):
            dns_output.append(d)
            dns_set.add(d)

# 本地黑名单 DNS 域名
if os.path.exists(local_black_path):
    tmp_domains = set()
    with open(local_black_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            m = re.fullmatch(r"\|\|([a-zA-Z0-9.-]+)\^", line)
            if m:
                domain = m.group(1)
                if domain not in allow_domain_set and domain not in dns_set:
                    tmp_domains.add(domain)
    if tmp_domains:
        dns_output.extend([
            "! ==============================================",
            "! 📋 规则来源：本地自定义规则（data/mod/adblock.txt）",
            "! ⚠️ 优先级：最高",
            "! ==============================================",
        ])
        for d in sorted(tmp_domains):
            dns_output.append(d)
            dns_set.add(d)

with open(os.path.join(TARGET_DIR, "dns.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(dns_output) + "\n")

# ==========================================
# 完成
# ==========================================
print("\n✅ 全部合并完成！本地黑白名单均已完整写入！")
print(f"📊 黑名单：{len(black_set)} 条")
print(f"📊 白名单：{len(all_white_raw)} 条")
print(f"📊 DNS域名：{len(dns_set)} 个")
