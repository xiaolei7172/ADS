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
# ✅ 全能来源识别（支持 ghproxy / ghfast / 原始链接）
# ==========================================
def get_source_info(file_path):
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        # 1. 匹配所有 GitHub 原始链接（含代理前缀）
        pattern = re.compile(
            r"(?:https://[^/]+/)?(https://raw\.githubusercontent\.com/([a-zA-Z0-9_-]+)/([a-zA-Z0-9_-]+)/[^\s]+)"
        )
        match = pattern.search(content)
        
        if match:
            full_url = match.group(1)  # 真实原始地址
            author = match.group(2)
            repo = match.group(3)
            source_name = f"{author} / {repo}"
            return source_name, full_url

    except Exception:
        pass

    return "未知上游", "无来源地址"

# ==========================================
# 合并广告规则 + 自动分段注释
# ==========================================
print("🔍 自动识别上游来源并合并拦截规则...")
ad_files = sorted(glob.glob("adblock*.txt"))
final_ad = []

for file in ad_files:
    source_name, source_url = get_source_info(file)
    final_ad.append("\n! ==============================================")
    final_ad.append(f"! 📋 规则来源：{source_name}")
    final_ad.append(f"! 🔗 原始地址：{source_url}")
    final_ad.append("! ==============================================\n")

    try:
        with open(file, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith(("!", "#", "[")):
                    final_ad.append(line)
    except:
        continue

# 去重（保留分段注释）
ad_lines = []
seen = set()
for line in final_ad:
    if line.startswith("!"):
        ad_lines.append(line)
    elif line not in seen:
        seen.add(line)
        ad_lines.append(line)

with open("cleaned_adblock.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(ad_lines) + "\n")

# ==========================================
# 合并白名单
# ==========================================
print("🔍 自动识别上游来源并合并白名单...")
allow_files = sorted(glob.glob("allow*.txt"))
final_allow = []

for file in allow_files:
    source_name, source_url = get_source_info(file)
    final_allow.append("\n! ==============================================")
    final_allow.append(f"! 📋 白名单来源：{source_name}")
    final_allow.append(f"! 🔗 原始地址：{source_url}")
    final_allow.append("! ==============================================\n")

    try:
        with open(file, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if line and line.startswith("@@"):
                    final_allow.append(line)
    except:
        continue

# 白名单去重
allow_lines = []
seen_allow = set()
for line in final_allow:
    if line.startswith("!"):
        allow_lines.append(line)
    elif line not in seen_allow:
        seen_allow.add(line)
        allow_lines.append(line)

with open("allow.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(allow_lines) + "\n")

# ==========================================
# 输出到最终目录
# ==========================================
Path(TARGET_DIR).mkdir(parents=True, exist_ok=True)
os.replace("cleaned_adblock.txt", os.path.join(TARGET_DIR, "adblock.txt"))
os.replace("allow.txt", os.path.join(TARGET_DIR, "allow.txt"))

# ==========================================
# 生成 DNS 规则
# ==========================================
print("🔍 生成 DNS 拦截规则...")
dns_domains = set()
try:
    with open(os.path.join(TARGET_DIR, "adblock.txt"), "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if re.match(r"^\|\|.+\^$", line):
                dns_domains.add(line.replace("||", "").replace("^", ""))
except:
    pass

with open(os.path.join(TARGET_DIR, "dns.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(sorted(dns_domains)) + "\n")

print("✅ 全部完成：自动识别来源 + 分段注释 + 去重")
