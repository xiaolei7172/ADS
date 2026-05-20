import os
import glob
import re

# ==========================================
# 目录配置（和下载脚本完全对齐）
# ==========================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../.."))
TMP_DIR = os.path.join(REPO_ROOT, "data", "tmp")
TARGET_DIR = os.path.join(REPO_ROOT, "data", "rules")

os.makedirs(TMP_DIR, exist_ok=True)
os.makedirs(TARGET_DIR, exist_ok=True)

# ==========================================
# 智能提取头部元信息
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
# 工具：从@@白名单提取放行域名
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
# 1. 先收集所有白名单（内置+独立）
# ==========================================
print("🚀 收集全部白名单规则")
all_white_raw = set()
ad_files = sorted(glob.glob(os.path.join(TMP_DIR, "adblock_*.txt")))
allow_files = sorted(glob.glob(os.path.join(TMP_DIR, "allow_*.txt")))

# 提取广告规则内自带白名单
for file in ad_files:
    with open(file, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if line.startswith("@@") and line not in all_white_raw:
                all_white_raw.add(line)

# 提取独立下载白名单
for file in allow_files:
    with open(file, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if line.startswith("@@") and line not in all_white_raw:
                all_white_raw.add(line)

# 解析放行域名，用于黑名单冲突过滤
allow_domain_set = extract_allow_domains(all_white_raw)

# ==========================================
# 2. 合并黑名单 + 过滤白名单冲突规则
# ==========================================
print("🚀 合并黑名单并剔除白名单冲突规则")
black_output = []
black_set = set()

for file in ad_files:
    final_name, desc, url = get_rule_meta(file)
    black_output.extend([
        "! ==============================================",
        f"! 📋 以下规则来源：{final_name}",
        f"! 📝 规则说明：{desc}",
        f"! 🔗 原始地址：{url}",
        "! ==============================================",
    ])

    with open(file, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            # 跳过注释、空行、白名单
            if not line or line.startswith(("!", "#", "[", "@@")):
                continue
            # 匹配域名拦截规则，判断是否被放行
            domain_match = re.fullmatch(r"\|\|([a-zA-Z0-9.-]+)\^", line)
            if domain_match:
                block_domain = domain_match.group(1)
                # 域名在放行列表则直接跳过
                if block_domain in allow_domain_set:
                    continue
            # 无冲突且未重复才加入
            if line not in black_set:
                black_set.add(line)
                black_output.append(line)

# 写入最终纯净黑名单
with open(os.path.join(TARGET_DIR, "adblock.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(black_output) + "\n")

# ==========================================
# 3. 整合输出完整白名单（内置+独立）
# ==========================================
print("🚀 整合全部白名单规则")
white_output = []

# 写入规则内置白名单
for file in ad_files:
    final_name, desc, url = get_rule_meta(file)
    temp_white = []
    with open(file, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if line.startswith("@@") and line in all_white_raw:
                temp_white.append(line)
    if temp_white:
        white_output.extend([
            "! ==============================================",
            f"! 📋 白名单来源：{final_name}（规则内置）",
            f"! 📝 规则说明：{desc}",
            f"! 🔗 原始地址：{url}",
            "! ==============================================",
        ])
        white_output.extend(temp_white)

# 写入独立外部白名单
for file in allow_files:
    final_name, desc, url = get_rule_meta(file)
    temp_white = []
    with open(file, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if line.startswith("@@") and line in all_white_raw:
                temp_white.append(line)
    if temp_white:
        white_output.extend([
            "! ==============================================",
            f"! 📋 白名单来源：{final_name}（独立白名单）",
            f"! 📝 规则说明：{desc}",
            f"! 🔗 原始地址：{url}",
            "! ==============================================",
        ])
        white_output.extend(temp_white)

# 去重后写入
final_white_list = list(dict.fromkeys(white_output))
with open(os.path.join(TARGET_DIR, "allow.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(final_white_list) + "\n")

# ==========================================
# 4. 生成DNS域名列表（同样过滤放行域名）
# ==========================================
print("🚀 生成过滤后DNS拦截域名")
dns_output = []
dns_set = set()

for file in ad_files:
    final_name, desc, url = get_rule_meta(file)
    temp_domains = set()
    with open(file, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            match = re.fullmatch(r"\|\|([a-zA-Z0-9.-]+)\^", line)
            if match:
                domain = match.group(1)
                # 跳过白名单放行域名
                if domain in allow_domain_set:
                    continue
                if domain not in dns_set:
                    temp_domains.add(domain)
    if temp_domains:
        dns_output.extend([
            "! ==============================================",
            f"! 📋 规则来源：{final_name}",
            f"! 📝 规则说明：{desc}",
            f"! 🔗 原始地址：{url}",
            "! ==============================================",
        ])
        for d in sorted(temp_domains):
            dns_output.append(d)
            dns_set.add(d)

with open(os.path.join(TARGET_DIR, "dns.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(dns_output) + "\n")

# ==========================================
# 运行统计
# ==========================================
print("\n✅ 全部合并&冲突过滤完成！")
print(f"📊 有效黑名单规则：{len(black_set)} 条")
print(f"📊 合并白名单总数：{len(all_white_raw)} 条")
print(f"📊 过滤后DNS拦截域名：{len(dns_set)} 个")
print(f"💡 已自动剔除黑名单中与白名单冲突的拦截规则")
