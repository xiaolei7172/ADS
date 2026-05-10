import datetime
import pytz
import os

# ==========================================
# 【核心修复】强制定位到仓库根目录（master 根）
# ==========================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../.."))  # 直接跳回仓库根目录！
os.chdir(REPO_ROOT)

# 获取规则数量
def get_count(fpath):
    full_path = os.path.join(REPO_ROOT, fpath)
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('! Total count:'):
                    return line.strip().replace('! Total count:', '').strip()
        return "0"
    except:
        return "0"

num_adblock = get_count("./data/rules/adblock.txt")
num_dns = get_count("./data/rules/dns.txt")
num_allow = get_count("./data/rules/allow.txt")

# 北京时间
tz = pytz.timezone('Asia/Shanghai')
now = datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
beijing_time = f"{now}（北京时间）"

# ==========================================
# 读取并更新 【仓库根目录的 README.md】
# ==========================================
readme_path = os.path.join(REPO_ROOT, "README.md")

with open(readme_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if line.startswith("更新时间:"):
        new_lines.append(f"更新时间: {beijing_time}\n")
    elif line.startswith("拦截规则数量:"):
        new_lines.append(f"拦截规则数量: {num_adblock}\n")
    elif line.startswith("DNS拦截规则数量:"):
        new_lines.append(f"DNS拦截规则数量: {num_dns}\n")
    elif line.startswith("白名单规则数量:"):
        new_lines.append(f"白名单规则数量: {num_allow}\n")
    else:
        new_lines.append(line)

# 写回根目录 README
with open(readme_path, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("✅ 已成功更新【仓库根目录】README.md ！")
print(f"📁 路径: {readme_path}")
print(f"⏰ 更新时间: {beijing_time}")
print(f"📊 拦截规则: {num_adblock}")
print(f"📊 DNS规则: {num_dns}")
print(f"📊 白名单: {num_allow}")
