import os
import subprocess
import time
import shutil

# ==============================================
# ✅ 目录配置
# ==============================================
if "GITHUB_WORKSPACE" in os.environ:
    BASE_DIR = os.environ["GITHUB_WORKSPACE"]
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

TMP_DIR = os.path.join(BASE_DIR, "tmp")
MOD_DIR = os.path.join(BASE_DIR, "data", "mod")

# ==============================================
# 清空临时目录
# ==============================================
try:
    shutil.rmtree(TMP_DIR)
except:
    pass
os.makedirs(TMP_DIR, exist_ok=True)

# ==============================================
# 写入来源头部（关键函数）
# ==============================================
def write_source_header(file_path, source_name, source_url):
    if not os.path.exists(file_path):
        return
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    header = f"! 📋 规则来源：{source_name}\n! 🔗 原始地址：{source_url}\n\n"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(header + content)

# ==============================================
# 复制本地自定义规则
# ==============================================
if os.path.exists(os.path.join(MOD_DIR, "adblock.txt")):
    dst = os.path.join(TMP_DIR, "adblock_00.txt")
    shutil.copy(os.path.join(MOD_DIR, "adblock.txt"), dst)
    write_source_header(dst, "本地自定义规则", "本地文件")

if os.path.exists(os.path.join(MOD_DIR, "whitelist.txt")):
    dst = os.path.join(TMP_DIR, "allow_00.txt")
    shutil.copy(os.path.join(MOD_DIR, "whitelist.txt"), dst)
    write_source_header(dst, "本地白名单", "本地文件")

# ==============================================
# ✅ 你要的格式：链接 + # 规则名称
# ==============================================
adblock_urls = [
    "https://raw.githubusercontent.com/TG-Twilight/AWAvenue-Ads-Rule/main/AWAvenue-Ads-Rule.txt",  # 秋风广告规则
    "https://raw.githubusercontent.com/xinggsf/Adblock-Plus-Rule/master/mv.txt",                  # 兴趣合并规则
    "https://raw.githubusercontent.com/xinggsf/Adblock-Plus-Rule/master/rule.txt",              # 兴趣基础规则
    "https://anti-ad.net/easylist.txt",                                                          # anti-ad 官方规则
    "https://raw.githubusercontent.com/banbendalao/ADgk/master/ADgk.txt",                      # ADgk 广告规则
    "https://raw.githubusercontent.com/xiaolei7172/ADS/refs/heads/master/data/mod/adblock.txt",  # 天影自用补充
]

allow_urls = [
    "https://raw.githubusercontent.com/xiaolei7172/ADS/refs/heads/master/data/mod/whitelist.txt",# 天影白名单
    "https://raw.githubusercontent.com/qq5460168/dangchu/main/white.txt",                        # 当初白名单
    "https://raw.githubusercontent.com/liwenjie119/adg-rules/master/white.txt",                  # 李文杰白名单
    "https://raw.githubusercontent.com/AdguardTeam/AdguardFilters/master/ChineseFilter/sections/allowlist.txt",  # AdGuard 中文白名单
    "https://raw.githubusercontent.com/AdguardTeam/AdguardFilters/master/SpywareFilter/sections/allowlist.txt",   # AdGuard 跟踪白名单
]

# ==============================================
# 下载函数
# ==============================================
def download_file(url, save_path):
    try:
        result = subprocess.run(
            ["curl", "-L", "--connect-timeout", "30", "--max-time", "120", "-o", save_path, url],
            capture_output=True, text=True
        )
        if result.returncode == 0 and os.path.exists(save_path) and os.path.getsize(save_path) > 100:
            return True
        if os.path.exists(save_path):
            os.remove(save_path)
    except:
        pass
    return False

# ==============================================
# 下载广告规则 + 自动识别 # 后面的名称
# ==============================================
for i, url in enumerate(adblock_urls):
    # 自动获取 # 后面的规则名称
    name = url.split("#")[-1].strip() if "#" in url else f"广告规则{i+1}"
    pure_url = url.split("#")[0].strip()

    save_path = os.path.join(TMP_DIR, f"adblock_{i+1:02d}.txt")
    if download_file(pure_url, save_path):
        write_source_header(save_path, name, pure_url)
        print(f"✅ 下载成功：{name}")
    else:
        print(f"❌ 下载失败：{pure_url}")
    time.sleep(1)

# ==============================================
# 下载白名单 + 自动识别 # 后面的名称
# ==============================================
for i, url in enumerate(allow_urls):
    name = url.split("#")[-1].strip() if "#" in url else f"白名单{i+1}"
    pure_url = url.split("#")[0].strip()

    save_path = os.path.join(TMP_DIR, f"allow_{i+1:02d}.txt")
    if download_file(pure_url, save_path):
        write_source_header(save_path, name, pure_url)
        print(f"✅ 下载成功：{name}")
    else:
        print(f"❌ 下载失败：{pure_url}")
    time.sleep(1)

print("\n🎉 全部下载完成 + 来源已自动写入！")
