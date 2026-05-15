import os
import subprocess
import time
import shutil

# ==============================================
# 目录配置（100% 对齐 merge.py）
# ==============================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../.."))

# ✅ 绝对正确：data/tmp
TMP_DIR = os.path.join(REPO_ROOT, "data", "tmp")
MOD_DIR = os.path.join(REPO_ROOT, "data", "mod")

# ==============================================
# 清空临时目录
# ==============================================
try:
    shutil.rmtree(TMP_DIR)
except:
    pass
os.makedirs(TMP_DIR, exist_ok=True)

# ==============================================
# 写入来源头部
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
# 广告规则
# ==============================================
adblock_rules = [
    {"url": "https://raw.githubusercontent.com/qq5460168/666/master/rules.txt", "name": "个人合并规则"},
    #{"url": "https://oss.xlxbk.cn/dns.txt", "name": "xlxbk DNS黑名单"},
    {"url": "https://raw.gitcode.com/rssv/qy-Ads-Rule/raw/main/black.txt", "name": "晴雅规则"},
    {"url": "https://raw.githubusercontent.com/damengzhu/banad/main/jiekouAD.txt", "name": "酷安@大萌主"},
    {"url": "https://raw.githubusercontent.com/2Gardon/SM-Ad-FuckU-hosts/master/SMAdHosts", "name": "基于安卓APP抓取的规则"},
    {"url": "http://hgzs.uunat.com/hg1.txt", "name": "海哥规则"},
    {"url": "https://raw.githubusercontent.com/afwfv/DD-AD/main/rule/DD-AD.txt", "name": "dd-ad 规则"},
    {"url": "https://gh-proxy.com/raw.githubusercontent.com/changzhaoCZ/fqnovel-adrules/refs/heads/main/fqnovel-fxxk_ads", "name": "对不对个人维护规则"},
    #{"url": "https://raw.githubusercontent.com/qq5460168/dangchu/main/black.txt", "name": "番茄去广告规则"},
    {"url": "https://raw.githubusercontent.com/TG-Twilight/AWAvenue-Ads-Rule/main/AWAvenue-Ads-Rule.txt", "name": "秋风广告规则"},
    {"url": "https://raw.githubusercontent.com/xinggsf/Adblock-Plus-Rule/master/mv.txt", "name": "乘风视频规则"},
    {"url": "https://raw.githubusercontent.com/xinggsf/Adblock-Plus-Rule/master/rule.txt", "name": "乘风通用规则"},
    {"url": "https://anti-ad.net/easylist.txt", "name": "anti-ad 官方规则"},
    #{"url": "https://raw.githubusercontent.com/banbendalao/ADgk/master/ADgk.txt", "name": "ADgk 广告规则"},
    #{"url": "https://raw.githubusercontent.com/qq5460168/generate-adguard/refs/heads/main/adguard_rules/filtered_rules.txt", "name": "从AdGuard Home日志生成的拦截规则"},
    
]

allow_rules = [
    #{"url": "https://raw.githubusercontent.com/xiaolei7172/ADS/refs/heads/master/data/mod/whitelist.txt", "name": "天影白名单"},
    #{"url": "https://oss.xlxbk.cn/allow.txt", "name": "xlxbk白名单"},
    {"url": "https://raw.githubusercontent.com/qq5460168/dangchu/main/white.txt", "name": "当初白名单"},
    {"url": "https://raw.githubusercontent.com/liwenjie119/adg-rules/master/white.txt", "name": "李文杰白名单"},
    {"url": "https://raw.githubusercontent.com/AdguardTeam/AdguardFilters/master/ChineseFilter/sections/allowlist.txt", "name": "AdGuard 中文白名单"},
    {"url": "https://raw.githubusercontent.com/AdguardTeam/AdguardFilters/master/SpywareFilter/sections/allowlist.txt", "name": "AdGuard 跟踪白名单"},
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
# 下载广告规则
# ==============================================
for i, rule in enumerate(adblock_rules):
    url = rule["url"]
    name = rule["name"]
    save_path = os.path.join(TMP_DIR, f"adblock_{i+1:02d}.txt")
    
    if download_file(url, save_path):
        write_source_header(save_path, name, url)
        print(f"✅ 下载成功：{name}")
    else:
        print(f"❌ 下载失败：{name}")
    time.sleep(1)

# ==============================================
# 下载白名单规则
# ==============================================
for i, rule in enumerate(allow_rules):
    url = rule["url"]
    name = rule["name"]
    save_path = os.path.join(TMP_DIR, f"allow_{i+1:02d}.txt")
    
    if download_file(url, save_path):
        write_source_header(save_path, name, url)
        print(f"✅ 下载成功：{name}")
    else:
        print(f"❌ 下载失败：{name}")
    time.sleep(1)

print("\n🎉 全部下载完成 + 来源已自动写入！")
