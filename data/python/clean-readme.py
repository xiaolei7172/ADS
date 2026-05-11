import datetime
import pytz
import os

# ================================
# 仓库根目录
# ================================
if "GITHUB_WORKSPACE" in os.environ:
    REPO_ROOT = os.environ["GITHUB_WORKSPACE"]
else:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../.."))

RULE_DIR = os.path.join(REPO_ROOT, "data", "rules")

# ================================
# 精准计数（与 title.py 逻辑完全一致）
# ================================
def count_valid_lines(file_path):
    count = 0
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith(("!", "#")):
                    count += 1
    except:
        pass
    return count

# ================================
# 统计三个核心规则
# ================================
adblock_num = count_valid_lines(os.path.join(RULE_DIR, "adblock.txt"))
dns_num = count_valid_lines(os.path.join(RULE_DIR, "dns.txt"))
allow_num = count_valid_lines(os.path.join(RULE_DIR, "allow.txt"))

# ================================
# 北京时间
# ================================
tz = pytz.timezone("Asia/Shanghai")
now = datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

# ================================
# 严格匹配你现有 README 排版格式
# ================================
stats_block = """## 📊 实时项目统计

### 🔮 天影自用广告过滤规则集群


🕒 **更新时间**：{}（北京时间）


🚫 **广告拦截规则**：{} 条


🌐 **DNS 拦截域名**：{} 个


✅ **白名单放行规则**：{} 条

---""".format(now, adblock_num, dns_num, allow_num)

# ================================
# 只替换统计区块，不改动其他任何内容
# ================================
readme_path = os.path.join(REPO_ROOT, "README.md")
with open(readme_path, "r", encoding="utf-8", errors="ignore") as f:
    content = f.read()

# 定位起止标记
start_mark = "## 📊 实时项目统计"
end_mark = "---\n\n## 📥 规则订阅中心"

if start_mark in content and end_mark in content:
    part1 = content.split(start_mark)[0]
    part2 = content.split(end_mark)[1]
    new_content = part1 + stats_block + end_mark + part2
else:
    new_content = content

with open(readme_path, "w", encoding="utf-8") as f:
    f.write(new_content)

print("✅ README 统计已更新，计数精准同步！")
print(f"📊 拦截：{adblock_num} | DNS：{dns_num} | 白名单：{allow_num}")
