import os
import glob
import re

# ==========================================
# 目录配置
# ==========================================
SCRIPT_DIR = os.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../.."))
TMP_DIR = os.path.join(REPO_ROOT, "data", "tmp")
TARGET_DIR = os.path.join(REPO_ROOT, "data", "rules")

os.makedirs(TMP_DIR, exist_ok=True)
os.makedirs(TARGET_DIR, exist_ok=True)

# ==========================================
# 智能提取信息（修复 Description 为空）
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

    # ======================
    # ✅ 修复：没有 Description 就自动赋值
    # ======================
    if not desc.strip():
        desc = "广告拦截规则"

    final_name = f"{source_name} [{title}]" if title.strip() else source_name
    return final_name, desc, source_url

# ==========================================
# 1. 合并黑名单（带注释）
# ==========================================
print("🚀 合并黑名单")
ad_files = sorted(glob.glob(os.path.join(TMP_DIR, "adblock_*.txt")))
black_output = []
black_set = set()

for file in ad_files:
    final_name, desc, url = get_rule_meta(file)
    black_output.append("! ==============================================")
    black_output.append(f"! 📋 以下规则来源：{final_name}")
    black_output.append(f"! 📝 规则说明：{desc}")
    black_output.append(f"! 🔗 原始地址：{url}")
    black_output.append("! ==============================================")

    with open(file, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith(("!", "#", "[")):
                continue
            if line not in black_set:
                black_set.add(line)
                black_output.append(line)

with open(os.path.join(TARGET_DIR, "adblock.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(black_output) + "\n")

# ==========================================
# 2. 合并白名单（带注释）
# ==========================================
print("🚀 合并白名单")
allow_files = sorted(glob.glob(os.path.join(TMP_DIR, "allow_*.txt")))
white_output = []
white_set = set()

for file in allow_files:
    final_name, desc, url = get_rule_meta(file)
    white_output.append("! ==============================================")
    white_output.append(f"! 📋 以下白名单来源：{final_name}")
    white_output.append(f"! 📝 规则说明：{desc}")
    white_output.append(f"! 🔗 原始地址：{url}")
    white_output.append("! ==============================================")

    with open(file, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith("@@") and line not in white_set:
                white_set.add(line)
                white_output.append(line)

with open(os.path.join(TARGET_DIR, "allow.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(white_output) + "\n")

# ==========================================
# 3. 生成 DNS 规则【带来源分段注释】
# ==========================================
print("🚀 生成 DNS 规则（全分段注释）")
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
                if domain not in dns_set:
                    temp_domains.add(domain)

    if temp_domains:
        dns_output.append("! ==============================================")
        dns_output.append(f"! 📋 以下规则来源：{final_name}")
        dns_output.append(f"! 📝 规则说明：{desc}")
        dns_output.append(f"! 🔗 原始地址：{url}")
        dns_output.append("! ==============================================")
        for d in sorted(temp_domains):
            dns_output.append(d)
            dns_set.add(d)

with open(os.path.join(TARGET_DIR, "dns.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(dns_output) + "\n")

# ==========================================
# 完成
# ==========================================
print("\n✅ 全部合并完成！全文件带分段注释！")
print(f"📊 黑名单：{len(black_set)} 条")
print(f"📊 白名单：{len(white_set)} 条")
print(f"📊 DNS域名：{len(dns_set)} 个")
