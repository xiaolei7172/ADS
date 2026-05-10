import os
import glob
import re
from pathlib import Path

# ==========================================
# 强制定位仓库根目录
# ==========================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../.."))
TMP_DIR = os.path.join(REPO_ROOT, "tmp")
TARGET_DIR = os.path.join(REPO_ROOT, "data", "rules")

# 进入 tmp
os.makedirs(TMP_DIR, exist_ok=True)
os.chdir(TMP_DIR)

# ==========================================
# 合并广告规则 + 去重
# ==========================================
print("合并上游拦截规则...")
file_list = glob.glob("adblock*.txt")
all_lines = set()  # 🔥 自动去重

for file in file_list:
    try:
        with open(file, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                # 跳过注释、空行
                if not line: continue
                if line.startswith(("!", "#", "[")): continue
                all_lines.add(line)  # 集合自动去重
    except:
        continue

# 排序并保存
sorted_lines = sorted(list(all_lines))
with open("cleaned_adblock.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(sorted_lines) + "\n")

print("✅ 拦截规则合并完成（已去重）")

# ==========================================
# 合并白名单 + 去重
# ==========================================
print("合并上游白名单规则...")
allow_files = glob.glob("allow*.txt")
white_lines = set()

for file in allow_files:
    try:
        with open(file, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line: continue
                if line.startswith(("!", "#", "[")): continue
                white_lines.add(line)
    except:
        continue

sorted_white = sorted(list(white_lines))
with open("cleaned_allow.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(sorted_white) + "\n")

print("✅ 白名单规则合并完成（已去重）")

# ==========================================
# 提取白名单 @@
# ==========================================
print("过滤白名单规则...")
final_white = []
with open("cleaned_allow.txt", "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line.startswith("@@"):
            final_white.append(line)

with open("allow.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(final_white) + "\n")

# ==========================================
# 移动到 /data/rules（覆盖旧文件）
# ==========================================
Path(TARGET_DIR).mkdir(parents=True, exist_ok=True)

adblock_final = os.path.join(TARGET_DIR, "adblock.txt")
allow_final = os.path.join(TARGET_DIR, "allow.txt")

os.replace(os.path.join(TMP_DIR, "cleaned_adblock.txt"), adblock_final)
os.replace(os.path.join(TMP_DIR, "allow.txt"), allow_final)

# ==========================================
# 最终去重（保险）
# ==========================================
print("规则最终去重处理...")
for fname in ["adblock.txt", "allow.txt", "dns.txt"]:
    fpath = os.path.join(TARGET_DIR, fname)
    if not os.path.exists(fpath):
        continue

    try:
        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
            lines = [l.strip() for l in f if l.strip() and not l.strip().startswith(("!", "#", "["))]
        
        unique = sorted(list(set(lines)))
        with open(fpath, "w", encoding="utf-8") as f:
            f.write("\n".join(unique) + "\n")
    except:
        continue

print("✅ 所有规则去重完成！全新生成成功！")
