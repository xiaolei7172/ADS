import datetime
import pytz
import os

# ==========================================
# 强制定位到【仓库根目录】，永远不会错
# ==========================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../.."))
os.chdir(REPO_ROOT)

# ==========================================
# 强制从 【根目录/data/rules】读取计数
# ==========================================
def get_count(filename):
    file_path = os.path.join(REPO_ROOT, "data", "rules", filename)
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                if line.startswith('! Total count:'):
                    return line.strip().replace('! Total count:', '').strip()
    except:
        return "0"
    return "0"

num_adblock = get_count("adblock.txt")
num_dns     = get_count("dns.txt")
num_allow   = get_count("allow.txt")

# ==========================================
# 北京时间
# ==========================================
tz = pytz.timezone('Asia/Shanghai')
beijing_time = datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

# ==========================================
# 读取 → 更新 → 写回【根目录 README.md】
# ==========================================
readme_path = os.path.join(REPO_ROOT, "README.md")

with open(readme_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if line.startswith("更新时间:"):
        new_lines.append(f"更新时间: {beijing_time}（北京时间）\n")
    elif line.startswith("拦截规则数量:"):
        new_lines.append(f"拦截规则数量: {num_adblock}\n")
    elif line.startswith("DNS拦截规则数量:"):
        new_lines.append(f"DNS拦截规则数量: {num_dns}\n")
    elif line.startswith("白名单规则数量:"):
        new_lines.append(f"白名单规则数量: {num_allow}\n")
    else:
        new_lines.append(line)

# 写回根目录
with open(readme_path, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

# ==========================================
# 输出日志
# ==========================================
print("✅ 已更新根目录 README.md")
print(f"📦 仓库根目录: {REPO_ROOT}")
print(f"📊 拦截规则: {num_adblock}")
print(f"📊 DNS规则: {num_dns}")
print(f"📊 白名单: {num_allow}")
