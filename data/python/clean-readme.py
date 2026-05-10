import subprocess
import datetime
import pytz
import os

# 锁定脚本目录
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# 获取规则数量
def get_count(fpath):
    try:
        with open(fpath, 'r', encoding='utf-8') as f:
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

# 直接重写 README（最稳，不会不生效）
with open("README.md", "w", encoding="utf-8") as f:
    f.write(f"""# 广告过滤规则

更新时间: {beijing_time}
拦截规则数量: {num_adblock}
DNS拦截规则数量: {num_dns}
白名单规则数量: {num_allow}
""")

print("✅ 成功写入 README.md！")
print(f"更新时间: {beijing_time}")
print(f"拦截规则: {num_adblock}")
print(f"DNS规则: {num_dns}")
print(f"白名单: {num_allow}")
