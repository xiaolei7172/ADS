import datetime
import pytz
import os
import re

# ================================
# 根目录
# ================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../.."))
RULE_DIR = os.path.join(REPO_ROOT, "data", "rules")

# ================================
# 读取统计数量
# ================================
def get_count(filename):
    path = os.path.join(RULE_DIR, filename)
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if "📊 有效规则：" in line:
                    return re.search(r"\d+", line).group()
    except:
        return "0"

adblock_num = get_count("adblock.txt")
dns_num = get_count("dns.txt")
allow_num = get_count("allow.txt")

# ================================
# 时间
# ================================
tz = pytz.timezone("Asia/Shanghai")
now = datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

# ================================
# 读取 README 并逐行稳定替换（百分百换行）
# ================================
readme_path = os.path.join(REPO_ROOT, "README.md")
with open(readme_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

output = []
in_stats = False

for line in lines:
    # 进入统计区
    if line.startswith("## 📊 项目统计"):
        in_stats = True
        output.append(line)
        output.append("\n")
        output.append("天影自用广告过滤规则\n")
        output.append(f"更新时间: {now}（北京时间）\n")
        output.append(f"拦截规则数量: {adblock_num}\n")
        output.append(f"DNS 拦截规则数量: {dns_num}\n")
        output.append(f"白名单规则数量: {allow_num}\n")
        output.append("\n")
    # 遇到下一个标题，退出统计区
    elif in_stats and line.startswith("## "):
        in_stats = False
        output.append(line)
    # 不在统计区，原样保留
    elif not in_stats:
        output.append(line)

# ================================
# 写回（保证换行 100% 正常）
# ================================
with open(readme_path, "w", encoding="utf-8") as f:
    f.writelines(output)

print("✅ README 已自动更新 → 自动换行正常！")
