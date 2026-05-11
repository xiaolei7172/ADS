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
# 北京时间
# ================================
tz = pytz.timezone("Asia/Shanghai")
now = datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

# ================================
# 美化版 项目统计区块
# ================================
stats_block = f"""

<div align="center">

### 📊 项目统计

---

**天影自用广告过滤规则**

<br>

🕒 更新时间：{now}（北京时间）

<br>

🚫 拦截规则数量：{adblock_num} 条

<br>

🌐 DNS 拦截域名：{dns_num} 个

<br>

✅ 白名单规则数量：{allow_num} 条

---

</div>

"""

# ================================
# 替换 README 统计区域
# ================================
readme_path = os.path.join(REPO_ROOT, "README.md")
with open(readme_path, "r", encoding="utf-8") as f:
    content = f.read()

# 标记起止，直接整块替换
start_flag = "## 📊 项目统计"
end_flag = "## 📥 规则订阅"

if start_flag in content and end_flag in content:
    part1 = content.split(start_flag)[0]
    part2 = content.split(end_flag)[1]
    new_content = part1 + stats_block + "## 📥 规则订阅" + part2
else:
    new_content = content

with open(readme_path, "w", encoding="utf-8") as f:
    f.write(new_content)

print("✅ README 统计区块已高级美化更新完成")
