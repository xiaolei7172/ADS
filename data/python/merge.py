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
os.chdir(TMP_DIR)

# ==========================================
# 从文件头部提取 Title / Description
# ==========================================
def get_rule_meta(file_path):
    title = "未知规则"
    desc = "无描述"
    source_url = "未知地址"
    
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for _ in range(30):
                line = f.readline()
                if not line:
                    break
                # 提取规则名称
                if line.startswith("! Title:"):
                    title = line.replace("! Title:", "").strip()
                # 提取规则说明
                if line.startswith("! Description:"):
                    desc = line.replace("! Description:", "").strip()
                # 提取下载的原始地址（来自 dl.py 写入）
                if "! 🔗 原始地址：" in line:
                    source_url = line.replace("! 🔗 原始地址：", "").strip()
    except:
        pass
    
    return title, desc, source_url

# ==========================================
# 1. 合并黑名单（无总表头 · 纯净去重）
# ==========================================
print("🚀 合并黑名单")
ad_files = sorted(glob.glob("adblock_*.txt"))
black_output = []
black_set = set()

for file in ad_files:
    title, desc, url = get_rule_meta(file)
    
    # 分段来源注释
    black_output.append("! ==============================================")
    black_output.append(f"! 📋 规则来源：{title}")
    black_output.append(f"! 📝 规则说明：{desc}")
    black_output.append(f"! 🔗 原始地址：{url}")
    black_output.append("! ==============================================")

    # 读取并清洗规则
    with open(file, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()  # 去首尾空格
            if not line:         # 去空行
                continue
            if line.startswith(("!", "#", "[")):  # 跳过注释
                continue
            if line not in black_set:
                black_set.add(line)
                black_output.append(line)

# 输出纯净黑名单
with open(os.path.join(TARGET_DIR, "adblock.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(black_output) + "\n")

# ==========================================
# 2. 合并白名单（仅保留 @@ · 纯净去重）
# ==========================================
print("🚀 合并白名单")
allow_files = sorted(glob.glob("allow_*.txt"))
white_output = []
white_set = set()

for file in allow_files:
    title, desc, url = get_rule_meta(file)
    
    white_output.append("! ==============================================")
    white_output.append(f"! 📋 白名单来源：{title}")
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

# 输出纯净白名单
with open(os.path.join(TARGET_DIR, "allow.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(white_output) + "\n")

# ==========================================
# 3. 自动生成 DNS 域名（纯域名 · 无注释）
# ==========================================
print("🚀 生成 DNS 规则")
dns_set = set()
for line in black_set:
    match = re.fullmatch(r"\|\|([a-zA-Z0-9.-]+)\^", line)
    if match:
        dns_set.add(match.group(1))

# 输出纯 DNS 文件
with open(os.path.join(TARGET_DIR, "dns.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(sorted(dns_set)) + "\n")

# ==========================================
# 移动到最终目录
# ==========================================
Path(TARGET_DIR).mkdir(parents=True, exist_ok=True)
os.replace("adblock.txt", os.path.join(TARGET_DIR, "adblock.txt"))
os.replace("allow.txt", os.path.join(TARGET_DIR, "allow.txt"))
os.replace("dns.txt", os.path.join(TARGET_DIR, "dns.txt"))

# ==========================================
# 完成
# ==========================================
print("\n✅ 合并完成！无任何多余表头！")
print(f"📊 黑名单：{len(black_set)} 条")
print(f"📊 白名单：{len(white_set)} 条")
print(f"📊 DNS域名：{len(dns_set)} 个")
