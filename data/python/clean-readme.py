import datetime
import pytz
import os
import re

# ================================
# 目录配置
# ================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../.."))
RULE_DIR = os.path.join(REPO_ROOT, "data", "rules")

# ================================
# 从你的专属表头中提取 📊 有效规则：数字 条
# ================================
def get_count_from_header(filename):
    path = os.path.join(RULE_DIR, filename)
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for _ in range(20):  # 只读取头部20行，超快
                line = f.readline()
                if not line:
                    break
                # 匹配你的格式：! 📊 有效规则：12345 条
                match = re.search(r"📊 有效规则：(\d+) 条", line)
                if match:
                    return match.group(1)
    except:
        return "0"
    return "0"

# ================================
# 自动读取三个文件的规则数
# ================================
num_adblock = get_count_from_header("adblock.txt")
num_dns     = get_count_from_header("dns.txt")
num_allow   = get_count_from_header("allow.txt")

# 北京时间
tz = pytz.timezone("Asia/Shanghai")
beijing_time = datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

# ================================
# README 自动更新（保证 100% 换行）
# ================================
readme_path = os.path.join(REPO_ROOT, "README.md")
with open(readme_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

output = []
in_stats_area = False

for line in lines:
    # 进入统计区域
    if line.startswith("## 📊 项目统计"):
        in_stats_area = True
        output.append(line)
        output.append("\n")
        output.append("天影自用广告过滤规则\n")
        output.append(f"更新时间: {beijing_time}（北京时间）\n")
        output.append(f"拦截规则数量: {num_adblock}\n")
        output.append(f"DNS 拦截域名数量: {num_dns}\n")
        output.append(f"白名单规则数量: {num_allow}\n")
        output.append("\n")
    
    # 遇到下一个标题，停止替换
    elif in_stats_area and line.startswith("## "):
        in_stats_area = False
        output.append(line)
    
    # 不在统计区 → 保持原样
    elif not in_stats_area:
        output.append(line)

# 写回 README
with open(readme_path, "w", encoding="utf-8") as f:
    f.writelines(output)

print("✅ README 已自动更新完成！")
print(f"🕒 更新时间：{beijing_time}")
print(f"📊 拦截规则：{num_adblock} 条")
print(f"📊 DNS 域名：{num_dns} 条")
print(f"📊 白名单：{num_allow} 条")
