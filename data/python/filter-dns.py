import os
import datetime

# ==========================================
# 强制定位到【仓库根目录】，永远正确
# ==========================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../.."))
os.chdir(REPO_ROOT)

# 确保目录存在
os.makedirs(os.path.join(REPO_ROOT, "tmp"), exist_ok=True)
os.makedirs(os.path.join(REPO_ROOT, "data", "rules"), exist_ok=True)

print("正在从 adblock.txt 提取 DNS 规则...")

# ==========================================
# 强制读写【仓库根目录 /data/rules/】
# ==========================================
input_path = os.path.join(REPO_ROOT, "data", "rules", "adblock.txt")
output_path = os.path.join(REPO_ROOT, "data", "rules", "dns.txt")

with open(input_path, 'r', encoding='utf-8', errors='ignore') as input_file, \
     open(output_path, 'w', encoding='utf-8') as output_file:

    for line in input_file:
        line = line.strip()
        if len(line) >= 2 and line.startswith("||") and line.endswith("^"):
            output_file.write(line + '\n')

print("✅ DNS 规则提取完成！已生成 → " + output_path)
