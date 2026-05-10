import os
import subprocess
import time
import shutil

# ==============================================
# 【核心：强制锁定 GitHub 仓库根目录】
# 从此所有路径 永远指向 仓库根目录 /data/rules
# ==============================================
BASE_DIR = os.path.abspath("/")

# 自动识别 GitHub Actions 环境 / 本地环境
if os.path.exists("/github/workspace"):
    BASE_DIR = "/github/workspace"
else:
    # 脚本在 ./data/python/ → 跳回仓库根目录
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 最终目录：仓库根目录/data/rules
DATA_RULES = os.path.join(BASE_DIR, "data", "rules")
TMP_DIR = os.path.join(BASE_DIR, "tmp")
MOD_DIR = os.path.join(BASE_DIR, "data", "mod")

# ==============================================
# 删除 【仓库根目录】旧规则
# ==============================================
print(f"🗑️ 正在清理旧规则：{DATA_RULES}")

if os.path.exists(DATA_RULES):
    for file_name in os.listdir(DATA_RULES):
        file_path = os.path.join(DATA_RULES, file_name)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
        except:
            pass

try:
    shutil.rmtree(DATA_RULES)
except:
    pass

# ==============================================
# 创建临时目录（根目录下的 tmp）
# ==============================================
os.makedirs(TMP_DIR, exist_ok=True)

# ==============================================
# 复制本地规则（从仓库根目录/data/mod 复制）
# ==============================================
adblock_mod = os.path.join(MOD_DIR, "adblock.txt")
whitelist_mod = os.path.join(MOD_DIR, "whitelist.txt")

if os.path.exists(adblock_mod):
    shutil.copy(adblock_mod, os.path.join(TMP_DIR, "adblock01.txt"))

if os.path.exists(whitelist_mod):
    shutil.copy(whitelist_mod, os.path.join(TMP_DIR, "allow01.txt"))

# ==============================
# 规则列表（稳定无死链）
# ==============================
adblock = [
    "https://raw.githubusercontent.com/TG-Twilight/AWAvenue-Ads-Rule/main/AWAvenue-Ads-Rule.txt",
    "https://raw.githubusercontent.com/xinggsf/Adblock-Plus-Rule/master/mv.txt",
    "https://raw.githubusercontent.com/xinggsf/Adblock-Plus-Rule/master/rule.txt",
    "https://raw.githubusercontent.com/xiaolei7172/ADS/master/data/mod/adblock.txt",
    "https://anti-ad.net/easylist.txt",
    "https://raw.githubusercontent.com/banbendalao/ADgk/master/ADgk.txt"
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
# 下载规则 → 强制下载到 仓库根目录/tmp
# ==============================
for i, url in enumerate(adblock):
    out_path = os.path.join(TMP_DIR, f"adblock{i}.txt")
    try:
        subprocess.run(
            f'curl -m 60 --retry 3 -L -o "{out_path}" "{url}"',
            shell=True, check=True, capture_output=True
        )
        print(f"✅ 下载: adblock{i}.txt")
    except:
        print(f"❌ 下载失败: {url}")
    time.sleep(0.5)

for j, url in enumerate(allow):
    out_path = os.path.join(TMP_DIR, f"allow{j}.txt")
    try:
        subprocess.run(
            f'curl -m 60 --retry 3 -L -o "{out_path}" "{url}"',
            shell=True, check=True, capture_output=True
        )
        print(f"✅ 下载: allow{j}.txt")
    except:
        print(f"❌ 下载失败: {url}")
    time.sleep(0.5)

print("\n🎉 所有规则下载完成！（已保存到仓库根目录 tmp）")
