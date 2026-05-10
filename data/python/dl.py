import os
import subprocess
import time
import shutil

# ==============================================
# ✅ 官方 GitHub 仓库根目录（永远正确）
# ==============================================
if "GITHUB_WORKSPACE" in os.environ:
    BASE_DIR = os.environ["GITHUB_WORKSPACE"]
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DATA_RULES = os.path.join(BASE_DIR, "data", "rules")
TMP_DIR = os.path.join(BASE_DIR, "tmp")
MOD_DIR = os.path.join(BASE_DIR, "data", "mod")

# ==============================================
# 清空目录
# ==============================================
try:
    shutil.rmtree(TMP_DIR)
except:
    pass
os.makedirs(TMP_DIR, exist_ok=True)

# ==============================================
# 复制本地自定义规则
# ==============================================
if os.path.exists(os.path.join(MOD_DIR, "adblock.txt")):
    shutil.copy(
        os.path.join(MOD_DIR, "adblock.txt"),
        os.path.join(TMP_DIR, "adblock01.txt")
    )

if os.path.exists(os.path.join(MOD_DIR, "whitelist.txt")):
    shutil.copy(
        os.path.join(MOD_DIR, "whitelist.txt"),
        os.path.join(TMP_DIR, "allow01.txt")
    )

# ==============================================
# 正确规则地址（全部可访问）
# ==============================================
adblock_urls = [
    "https://raw.githubusercontent.com/TG-Twilight/AWAvenue-Ads-Rule/main/AWAvenue-Ads-Rule.txt",
    "https://raw.githubusercontent.com/xinggsf/Adblock-Plus-Rule/master/mv.txt",
    "https://raw.githubusercontent.com/xinggsf/Adblock-Plus-Rule/master/rule.txt",
    "https://anti-ad.net/easylist.txt",
    "https://raw.githubusercontent.com/banbendalao/ADgk/master/ADgk.txt"
]

allow_urls = [
    "https://raw.githubusercontent.com/qq5460168/dangchu/main/white.txt",
    "https://raw.githubusercontent.com/liwenjie119/adg-rules/master/white.txt",
    "https://raw.githubusercontent.com/AdguardTeam/AdguardFilters/master/ChineseFilter/sections/allowlist.txt",
    "https://raw.githubusercontent.com/AdguardTeam/AdguardFilters/master/SpywareFilter/sections/allowlist.txt"
]

# ==============================================
# ✅ 修复下载：真正能下载，不会空文件
# ==============================================
def download_file(url, save_path):
    try:
        result = subprocess.run(
            ["curl", "-L", "--connect-timeout", "30", "--max-time", "120", "-o", save_path, url],
            capture_output=True,
            text=True
        )
        if result.returncode == 0 and os.path.exists(save_path):
            if os.path.getsize(save_path) > 100:  # 小于100字节就是下载失败
                return True
        os.remove(save_path)
    except:
        pass
    return False

# 下载广告规则
for index, url in enumerate(adblock_urls):
    save_path = os.path.join(TMP_DIR, f"adblock{index+1}.txt")
    if download_file(url, save_path):
        print(f"✅ 下载成功: {url}")
    else:
        print(f"❌ 下载失败: {url}")
    time.sleep(1)

# 下载白名单
for index, url in enumerate(allow_urls):
    save_path = os.path.join(TMP_DIR, f"allow{index+1}.txt")
    if download_file(url, save_path):
        print(f"✅ 下载成功: {url}")
    else:
        print(f"❌ 下载失败: {url}")
    time.sleep(1)

print("\n🎉 规则下载完成！文件保存在: " + TMP_DIR)
