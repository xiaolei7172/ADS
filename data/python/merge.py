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
# 读取来源信息（配合你的 dl.py）
# ==========================================
def get_source_info(file_path):
    name = "未知规则"
    url = "未知地址"
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for _ in range(20):
                line = f.readline()
                if not line: break
                if "! 📋 规则来源：" in line:
                    name = line.replace("! 📋 规则来源：", "").strip()
                if "! 🔗 原始地址：" in line:
                    url = line.replace("! 🔗 原始地址：", "").strip()
    except:
        pass
    return name, url

# ==========================================
# 1. 合并 黑名单 (Adblock 规则)
# ==========================================
print("\n🚀 开始合并【黑名单】")
ad_files = sorted(glob.glob("adblock_*.txt"))
final_black = []
black_set = set()

for file in ad_files:
    s_name, s_url = get_source_info(file)
    final_black.append("! ==============================================")
    final_black.append(f"! 📋 规则来源：{s_name}")
    final_black.append(f"! 🔗 原始地址：{s_url}")
    final_black.append("! ==============================================")

    with open(file, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()  # 去首尾空格
            if not line: continue  # 去空行
            if line.startswith(("!", "#", "[")): continue

            if line not in black_set:
                black_set.add(line)
                final_black.append(line)

with open("final_adblock.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(final_black) + "\n")

# ==========================================
# 2. 合并 白名单 (仅保留 @@)
# ==========================================
print("\n🚀 开始合并【白名单】")
allow_files = sorted(glob.glob("allow_*.txt"))
final_white = []
white_set = set()

for file in allow_files:
    s_name, s_url = get_source_info(file)
    final_white.append("! ==============================================")
    final_white.append(f"! 📋 白名单来源：{s_name}")
    final_white.append(f"! 🔗 原始地址：{s_url}")
    final_white.append("! ==============================================")

    with open(file, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line: continue
            if line.startswith("@@"):  # 只保留白名单规则
                if line not in white_set:
                    white_set.add(line)
                    final_white.append(line)

with open("final_allow.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(final_white) + "\n")

# ==========================================
# 3. 自动生成 DNS 域名清单 (智能提取)
# ==========================================
print("\n🚀 开始生成【DNS 域名规则】")
dns_domains = set()

# 从 黑名单 里自动提取 ||domain.com^ 格式
with open("final_adblock.txt", "r", encoding="utf-8", errors="ignore") as f:
    for line in f:
        line = line.strip()
        match = re.fullmatch(r"\|\|([a-zA-Z0-9.-]+)\^", line)
        if match:
            domain = match.group(1)
            dns_domains.add(domain)

# 排序保存 DNS
dns_sorted = sorted(dns_domains)
with open("final_dns.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(dns_sorted) + "\n")

# ==========================================
# 移动到最终目录
# ==========================================
Path(TARGET_DIR).mkdir(parents=True, exist_ok=True)

os.replace("final_adblock.txt", os.path.join(TARGET_DIR, "adblock.txt"))
os.replace("final_allow.txt", os.path.join(TARGET_DIR, "allow.txt"))
os.replace("final_dns.txt", os.path.join(TARGET_DIR, "dns.txt"))

# ==========================================
# 完成
# ==========================================
print("\n✅ 全部处理完成！")
print(f"📊 黑名单规则：{len(black_set)} 条")
print(f"📊 白名单规则：{len(white_set)} 条")
print(f"📊 DNS 域名数量：{len(dns_domains)} 个")
