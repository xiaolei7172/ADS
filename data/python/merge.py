import os
import glob
import re
from pathlib import Path

# ==========================================
# 目录配置
# ==========================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../.."))
TMP_DIR = os.path.join(REPO_ROOT, "tmp")
TARGET_DIR = os.path.join(REPO_ROOT, "data", "rules")

os.makedirs(TMP_DIR, exist_ok=True)
os.makedirs(TARGET_DIR, exist_ok=True)
os.chdir(TMP_DIR)

# ==========================================
# 智能提取信息（修复版）
# ==========================================
def get_rule_meta(file_path):
    title = ""
    desc = ""
    source_name = "未知来源"
    source_url = "未知地址"
    
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
            
            for line in lines[:50]:
                line = line.strip()
                
                # 提取规则标题
                if line.startswith("! Title:"):
                    title = line.replace("! Title:", "").strip()
                
                # 提取规则描述
                if line.startswith("! Description:"):
                    desc = line.replace("! Description:", "").strip()
                
                # 提取 DL 里的来源名称
                if line.startswith("! 📋 规则来源："):
                    source_name = line.replace("! 📋 规则来源：", "").strip()
                
                # 提取下载链接
                if line.startswith("! 🔗 原始地址："):
                    source_url = line.replace("! 🔗 原始地址：", "").strip()
    except:
        pass

    # ======================
    # 智能显示名称（核心修复）
    # ======================
    if title.strip() != "" and title != "未知规则":
        final_name = f"{source_name} [{title}]"
    else:
        final_name = source_name

    # 描述为空则不显示
    if desc.strip() == "":
        desc = "无描述"

    return final_name, desc, source_url

# ==========================================
# 1. 合并黑名单
# ==========================================
print("🚀 合并黑名单")
ad_files = sorted(glob.glob("adblock_*.txt"))
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
            if not line:
                continue
            if line.startswith(("!", "#", "[")):
                continue
            if line not in black_set:
                black_set.add(line)
                black_output.append(line)

with open(os.path.join(TARGET_DIR, "adblock.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(black_output) + "\n")

# ==========================================
# 2. 合并白名单
# ==========================================
print("🚀 合并白名单")
allow_files = sorted(glob.glob("allow_*.txt"))
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
# 3. 生成 DNS
# ==========================================
print("🚀 生成 DNS 规则")
dns_set = set()
for line in black_set:
    match = re.fullmatch(r"\|\|([a-zA-Z0-9.-]+)\^", line)
    if match:
        dns_set.add(match.group(1))

with open(os.path.join(TARGET_DIR, "dns.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(sorted(dns_set)) + "\n")

# ==========================================
# 完成
# ==========================================
print("\n✅ 合并完成！")
print(f"📊 黑名单：{len(black_set)} 条")
print(f"📊 白名单：{len(white_set)} 条")
print(f"📊 DNS域名：{len(dns_set)} 个")
