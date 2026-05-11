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
readme_path = os.path.join(REPO_ROOT, "README.md")

# ================================
# 精准计数
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

adblock_num = count_valid_lines(os.path.join(RULE_DIR, "adblock.txt"))
dns_num = count_valid_lines(os.path.join(RULE_DIR, "dns.txt"))
allow_num = count_valid_lines(os.path.join(RULE_DIR, "allow.txt"))

# ================================
# 北京时间
# ================================
tz = pytz.timezone("Asia/Shanghai")
now = datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

# ================================
# 完全复刻你现有居中统计区块
# ================================
new_stats = f"""<div align="center">

## 📊 实时项目统计

### 🔮 天影自用广告过滤规则集群


🕒 **更新时间**：{now}（北京时间）


🚫 **广告拦截规则**：{adblock_num} 条


🌐 **DNS 拦截域名**：{dns_num} 个


✅ **白名单放行规则**：{allow_num} 条

---

</div>"""

# ================================
# 读取并替换整块
# ================================
with open(readme_path, "r", encoding="utf-8", errors="ignore") as f:
    content = f.read()

# 精准匹配起止标记
start_flag = '<div align="center">\n\n## 📊 实时项目统计'
end_flag = '\n\n</div>\n\n## 📥 规则订阅中心'

if start_flag in content and end_flag in content:
    left = content.split(start_flag)[0]
    right = content.split(end_flag)[1]
    final_content = left + new_stats + end_flag + right

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(final_content)
    print("✅ README 统计区块更新成功！")
    print(f"🕒 {now} | 🚫{adblock_num} | 🌐{dns_num} | ✅{allow_num}")
else:
    print("❌ 未匹配到统计区块，格式不匹配未更新")
