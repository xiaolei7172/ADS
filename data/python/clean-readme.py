import datetime
import pytz
import os

# ================================
# 目录
# ================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../.."))
RULE_DIR = os.path.join(REPO_ROOT, "data", "rules")

# ================================
# 统计有效规则行数
# ================================
def count_valid_lines(filename):
    path = os.path.join(RULE_DIR, filename)
    count = 0
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("!"):
                    count += 1
    except:
        return 0
    return count

adblock_num = count_valid_lines("adblock.txt")
dns_num = count_valid_lines("dns.txt")
allow_num = count_valid_lines("allow.txt")

# ================================
# 时间
# ================================
tz = pytz.timezone("Asia/Shanghai")
now = datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

# ================================
# 更新 README
# ================================
readme_path = os.path.join(REPO_ROOT, "README.md")
with open(readme_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

out = []
in_stats = False

for line in lines:
    if line.startswith("## 📊 项目统计"):
        in_stats = True
        out.append(line)
        out.append("\n")
        out.append("天影自用广告过滤规则\n")
        out.append(f"更新时间: {now}（北京时间）\n")
        out.append(f"拦截规则数量: {adblock_num}\n")
        out.append(f"DNS 拦截域名数量: {dns_num}\n")
        out.append(f"白名单规则数量: {allow_num}\n")
        out.append("\n")
    elif in_stats and line.startswith("## "):
        in_stats = False
        out.append(line)
    elif not in_stats:
        out.append(line)

with open(readme_path, "w", encoding="utf-8") as f:
    f.writelines(out)

print("✅ README 更新完成！")
