import datetime
import pytz
import os
import re

# ================================
# 仓库根目录
# ================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../.."))
os.chdir(REPO_ROOT)

# ================================
# 读取规则数量
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
    content = f.read()

# ================================
# ✅ 固定格式：自动换行 100% 正常
# ================================
new_stats = f"""## 📊 项目统计

天影自用广告过滤规则
更新时间: {beijing_time}（北京时间）
拦截规则数量: {num_adblock}
DNS 拦截规则数量: {num_dns}
白名单规则数量: {num_allow}

"""

# ================================
# ✅ 最强稳定替换：支持所有格式换行
# ================================
content = re.sub(r"## 📊 项目统计[\s\S]*?(?=\n## )", new_stats, content)

# ================================
# 写回
# ================================
with open(readme_path, "w", encoding="utf-8") as f:
    f.write(content)

print("✅ README 写入成功！自动换行正常！")
print(f"🕒 {beijing_time}")
print(f"📊 拦截:{num_adblock} DNS:{num_dns} 白名单:{num_allow}")
