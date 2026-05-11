import datetime
import pytz
import os
import re

# 项目根目录(README.md 就在这里)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../.."))
README_PATH = os.path.join(REPO_ROOT, "README.md")
RULES_PATH = os.path.join(REPO_ROOT, "data", "rules")

# 精准计数
def count_rules(filename):
    total = 0
    path = os.path.join(RULES_PATH, filename)
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                l = line.strip()
                if l and not l.startswith(("!", "#")):
                    total += 1
    except:
        pass
    return total

adblock = count_rules("adblock.txt")
dns = count_rules("dns.txt")
allow = count_rules("allow.txt")

# 北京时间
tz = pytz.timezone("Asia/Shanghai")
now = datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

# 读取原README
with open(README_PATH, "r", encoding="utf-8") as f:
    content = f.read()

# 正则原地【替换更新】，不新增、不重复
content = re.sub(r"🕒 \*\*更新时间\*\*：.*?（北京时间）", rf"🕒 **更新时间**：{now}（北京时间）", content)
content = re.sub(r"🚫 \*\*广告拦截规则\*\*：\d+ 条", rf"🚫 **广告拦截规则**：{adblock} 条", content)
content = re.sub(r"🌐 \*\*DNS 拦截域名\*\*：\d+ 个", rf"🌐 **DNS 拦截域名**：{dns} 个", content)
content = re.sub(r"✅ \*\*白名单放行规则\*\*：\d+ 条", rf"✅ **白名单放行规则**：{allow} 条", content)

# 写回原文件（覆盖旧内容）
with open(README_PATH, "w", encoding="utf-8") as f:
    f.write(content)

print("✅ 原地替换更新成功，无重复添加")
print(f"🕒{now} | 🚫{adblock} | 🌐{dns} | ✅{allow}")
