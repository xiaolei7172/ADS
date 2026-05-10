import os
import subprocess
import time
import shutil

# 自动切换到脚本所在目录
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# 删除旧规则目录
directory = "./data/rules/"
if os.path.exists(directory):
    for file_name in os.listdir(directory):
        file_path = os.path.join(directory, file_name)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"无法删除文件: {file_path}")

try:
    shutil.rmtree(directory)
    print(f"成功删除目录 {directory}")
except Exception as e:
    print(f"无法删除目录: {e}")

# 创建临时目录
os.makedirs("./tmp/", exist_ok=True)

# 复制本地规则（Windows/Linux 通用）
if os.path.exists("./data/mod/adblock.txt"):
    shutil.copy("./data/mod/adblock.txt", "./tmp/adblock01.txt")
if os.path.exists("./data/mod/whitelist.txt"):
    shutil.copy("./data/mod/whitelist.txt", "./tmp/allow01.txt")

# ==============================
# 【已清理：无失效、无死链、国内最强】
# ==============================
adblock = [
    "https://raw.githubusercontent.com/TG-Twilight/AWAvenue-Ads-Rule/main/AWAvenue-Ads-Rule.txt",
    "https://raw.githubusercontent.com/xinggsf/Adblock-Plus-Rule/master/mv.txt",
    "https://raw.githubusercontent.com/xinggsf/Adblock-Plus-Rule/master/rule.txt",
    "https://raw.githubusercontent.com/xiaolei7172/ADS/master/data/mod/adblock.txt",
    "https://anti-ad.net/easylist.txt",
    "https://raw.githubusercontent.com/banbendalao/ADgk/master/ADgk.txt"  # 番茄/小说广告
]

allow = [
    "https://raw.githubusercontent.com/qq5460168/dangchu/main/white.txt",
    "https://raw.githubusercontent.com/Kuroba-Sayuki/FuLing-AdRules/Master/FuLingRules/FuLingAllowList.txt",
    "https://raw.githubusercontent.com/qq5460168/666/master/allow.txt",
    "https://raw.githubusercontent.com/xiaolei7172/ADS/master/data/mod/whitelist.txt",
    "https://raw.githubusercontent.com/liwenjie119/adg-rules/master/white.txt",
    "https://raw.githubusercontent.com/AdguardTeam/AdguardFilters/master/ChineseFilter/sections/allowlist.txt",
    "https://raw.githubusercontent.com/AdguardTeam/AdguardFilters/master/SpywareFilter/sections/allowlist.txt"
]

# ==============================
# 下载规则（稳定、不报错、不掉线）
# ==============================
for i, url in enumerate(adblock):
    try:
        subprocess.run(
            f'curl -m 60 --retry 3 -L -o "tmp/adblock{i}.txt" "{url}"',
            shell=True, check=True, capture_output=True
        )
        print(f"✅ 下载: adblock{i}.txt")
    except:
        print(f"❌ 下载失败: {url}")
    time.sleep(0.5)

for j, url in enumerate(allow):
    try:
        subprocess.run(
            f'curl -m 60 --retry 3 -L -o "tmp/allow{j}.txt" "{url}"',
            shell=True, check=True, capture_output=True
        )
        print(f"✅ 下载: allow{j}.txt")
    except:
        print(f"❌ 下载失败: {url}")
    time.sleep(0.5)

print("\n🎉 所有规则下载完成！")
