import subprocess
import datetime
import pytz
import os

# 确保脚本在正确的目录执行
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# 提取规则计数（兼容 Windows/Linux，修复空值问题）
def get_count(file_path):
    try:
        result = subprocess.getoutput(f"sed -n 's/^! Total count: //p' {file_path}")
        return result.strip() if result.strip() else "未统计"
    except:
        return "统计失败"

num_adblock = get_count("./data/rules/adblock.txt")
num_dns = get_count("./data/rules/dns.txt")
num_allow = get_count("./data/rules/allow.txt")

# 获取北京时间
utc_now = datetime.datetime.now(pytz.timezone('UTC'))
beijing_time = utc_now.astimezone(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')

# 更新 README.md（修复 sed 语法，兼容所有系统）
subprocess.run(
    f"sed -i 's/^更新时间:.*/更新时间: {beijing_time}（北京时间）/g' README.md",
    shell=True, capture_output=True
)
subprocess.run(
    f"sed -i 's/^拦截规则数量:.*/拦截规则数量: {num_adblock}/g' README.md",
    shell=True, capture_output=True
)
subprocess.run(
    f"sed -i 's/^DNS拦截规则数量:.*/DNS拦截规则数量: {num_dns}/g' README.md",
    shell=True, capture_output=True
)
subprocess.run(
    f"sed -i 's/^白名单规则数量:.*/白名单规则数量: {num_allow}/g' README.md",
    shell=True, capture_output=True
)

print("✅ 已成功更新 README.md 规则统计与时间")
print(f"📊 拦截规则：{num_adblock}")
print(f"📊 DNS规则：{num_dns}")
print(f"📊 白名单：{num_allow}")
print(f"⏰ 更新时间：{beijing_time}")
