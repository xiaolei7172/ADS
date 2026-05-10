import datetime
import pytz
import os

# ================================
# 根目录
# ================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../.."))
os.chdir(REPO_ROOT)

# ================================
# 读取数量
# ================================
def get_count(filename):
    path = os.path.join(REPO_ROOT, "data", "rules", filename)
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if line.startswith("! Total count:"):
                    return line.strip().replace("! Total count:", "").strip()
    except:
        return "0"
    return "0"

num_adblock = get_count("adblock.txt")
num_dns = get_count("dns.txt")
num_allow = get_count("allow.txt")

# ================================
# 时间
# ================================
tz = pytz.timezone("Asia/Shanghai")
beijing_time = datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

# ================================
# 读取 README
# ================================
readme_path = os.path.join(REPO_ROOT, "README.md")
with open(readme_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# ================================
# 逐行处理，只替换统计区域（最稳）
# ================================
in_stats = False
new_lines = []
for line in lines:
    if line.startswith("## 📊 项目统计"):
        in_stats = True
        # 写入新的统计
        new_lines.append("## 📊 项目统计\n")
        new_lines.append("\n")
        new_lines.append("天影自用广告过滤规则\n")
        new_lines.append(f"更新时间: {beijing_time}（北京时间）\n")
        new_lines.append(f"拦截规则数量: {num_adblock}\n")
        new_lines.append(f"DNS 拦截规则数量: {num_dns}\n")
        new_lines.append(f"白名单规则数量: {num_allow}\n")
        new_lines.append("\n")
    elif in_stats and line.startswith("## "):
        # 遇到下一个标题，停止替换
        in_stats = False
        new_lines.append(line)
    elif not in_stats:
        new_lines.append(line)

# ================================
# 写回
# ================================
with open(readme_path, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("✅ README 写入成功！自动换行正常！")
