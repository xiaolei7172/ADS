import os
import glob
import re
from pathlib import Path

# ==========================================
# 强制定位到【仓库根目录】，全局统一
# ==========================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../.."))
TMP_DIR = os.path.join(REPO_ROOT, "tmp")
TARGET_DIR = os.path.join(REPO_ROOT, "data", "rules")

# 进入 tmp 目录（根目录下的）
os.makedirs(TMP_DIR, exist_ok=True)
os.chdir(TMP_DIR)

# ==================== 合并广告规则 ====================
print("合并上游拦截规则")
file_list = glob.glob("adblock*.txt")
with open("combined_adblock.txt", "w", encoding="utf-8") as outfile:
    for file in file_list:
        with open(file, "r", encoding="utf-8", errors="ignore") as infile:
            outfile.write(infile.read())
            outfile.write("\n")

with open("combined_adblock.txt", "r", encoding="utf-8") as f:
    content = f.read()
content = re.sub(r"^[!].*$\n", "", content, flags=re.MULTILINE)
content = re.sub(r"^#(?!\s*#).*\n?", "", content, flags=re.MULTILINE)
content = re.sub(r"\n+", "\n", content)

with open("cleaned_adblock.txt", "w", encoding="utf-8") as f:
    f.write(content)
print("✅ 拦截规则合并完成")

# ==================== 合并白名单 ====================
print("合并上游白名单规则")
allow_file_list = glob.glob("allow*.txt")
with open("combined_allow.txt", "w", encoding="utf-8") as outfile:
    for file in allow_file_list:
        with open(file, "r", encoding="utf-8", errors="ignore") as infile:
            outfile.write(infile.read())
            outfile.write("\n")

with open("combined_allow.txt", "r", encoding="utf-8") as f:
    content = f.read()
content = re.sub(r"^[!].*$\n", "", content, flags=re.MULTILINE)
content = re.sub(r"^#(?!\s*#).*\n?", "", content, flags=re.MULTILINE)
content = re.sub(r"\n+", "\n", content)

with open("cleaned_allow.txt", "w", encoding="utf-8") as f:
    f.write(content)
print("✅ 白名单规则合并完成")

# ==================== 提取 @@ 白名单 ====================
print("过滤白名单规则")
with open("cleaned_allow.txt", "r", encoding="utf-8") as f:
    allow_lines = f.readlines()

with open("allow.txt", "w", encoding="utf-8") as f:
    for line in allow_lines:
        line = line.strip()
        if line.startswith("@@"):
            f.write(line + "\n")

# ==================== 移动文件 → 仓库根目录 data/rules ====================
adblock_file = os.path.join(TMP_DIR, "cleaned_adblock.txt")
allow_file = os.path.join(TMP_DIR, "allow.txt")

Path(TARGET_DIR).mkdir(parents=True, exist_ok=True)

adblock_final = os.path.join(TARGET_DIR, "adblock.txt")
allow_final = os.path.join(TARGET_DIR, "allow.txt")

os.replace(adblock_file, adblock_final)
os.replace(allow_file, allow_final)

# ==================== 去重（只处理 data/rules 下的文件） ====================
print("规则去重中")
os.chdir(TARGET_DIR)

for file in os.listdir():
    if not os.path.isfile(file):
        continue
    if file not in ["adblock.txt", "allow.txt", "dns.txt"]:
        continue

    try:
        with open(file, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        lines = [line.rstrip("\n") for line in lines if line.strip()]
        lines = sorted(set(lines))

        with open(file, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

    except Exception as e:
        print(f"⚠️ 处理 {file} 出错: {e}")

print("✅ 规则去重完成")
