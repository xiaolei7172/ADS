# -*- coding: utf-8 -*-
"""
下载全部上游规则。
改进点（相对旧版）：
  1. curl 加 -f：404 不再被当成"下载成功"；
  2. 下载后做内容体检：HTML 错误页 / Cloudflare 挑战页直接拒收；
  3. raw.githubusercontent.com 被墙时自动走 GitHub Contents API 兜底；
  4. 失败来源汇总，若全部失败或失败过半，exit 1 中止工作流——
     宁可这次不更新，也不能把空规则/垃圾页发布出去。
"""
import os
import re
import subprocess
import time
import shutil
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../.."))

TMP_DIR = os.path.join(REPO_ROOT, "data", "tmp")
MOD_DIR = os.path.join(REPO_ROOT, "data", "mod")

try:
    shutil.rmtree(TMP_DIR)
except OSError:
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
# 内容体检：拦住 404 页、Cloudflare 挑战页、空文件
# 注意：不能拿 "cloudflare" 当关键词——规则正文合法地含它（如
# @@||xx.cloudflare.com^），本文件就误杀过当初白名单。
# 判 HTML 要认结构标签，判挑战页要用完整短语。
# ==============================================
BAD_MARKERS = re.compile(
    r"<!doctype\s|<html[\s>]|</html>|<title>|just a moment|checking your browser"
    r"|enable javascript and cookies|attention required",
    re.IGNORECASE,
)

def content_ok(path):
    try:
        size = os.path.getsize(path)
        if size < 200:
            return False, f"文件过小({size}B)"
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            head = f.read(4096)
        if BAD_MARKERS.search(head):
            return False, "内容是HTML/挑战页，不是规则"
        if head.lstrip().startswith("{"):
            return False, "内容是JSON（API报错），不是规则"
        return True, ""
    except OSError as e:
        return False, str(e)


# ==============================================
# raw.githubusercontent.com → 多通道兜底
# 实测可用性（2026-10-27，国内网络）：raw 直连时断时续，
# API 匿名限额 60次/小时容易耗尽，cdn.jsdelivr.net 主域被重置，
# 但 fastly/testingcf/gcore 三个 jsDelivr 子域和 gh-proxy.com 稳定可用
# ==============================================
RE_RAW_URL = re.compile(
    r"^https://raw\.githubusercontent\.com/([^/]+)/([^/]+)/([^/]+)/(.+)$"
)

def mirror_urls(url):
    """返回 [(url, 是否API模式), ...]，按可靠性排序"""
    attempts = [(url, False)]
    m = RE_RAW_URL.match(url)
    if m:
        owner, repo, branch, path = m.groups()
        # GitHub Contents API（有令牌时限额 1000/小时）
        attempts.append(
            (f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={branch}", True)
        )
        # jsDelivr 三个可用子域（主域 cdn.jsdelivr.net 国内被重置，勿用）
        for cdn in ("fastly.jsdelivr.net", "testingcf.jsdelivr.net", "gcore.jsdelivr.net"):
            attempts.append((f"https://{cdn}/gh/{owner}/{repo}@{branch}/{path}", False))
        # gh-proxy 加速代理
        attempts.append((f"https://gh-proxy.com/{url}", False))
    # http 源补 https 变体（部分网络环境禁明文 http）
    if url.startswith("http://"):
        attempts.append((url.replace("http://", "https://", 1), False))
    return attempts


def download_file(url, save_path):
    """多通道下载 + 体检，任一通道成功即返回 (True, '')"""
    last_err = "未知错误"
    for u, is_api in mirror_urls(url):
        cmd = [
            "curl", "-fsSL", "--retry", "3", "--retry-delay", "2",
            "--retry-all-errors", "--connect-timeout", "15", "--max-time", "180",
            "-A", "Mozilla/5.0 (compatible; TianYing-Rules/1.0)",
            "-o", save_path, u,
        ]
        if is_api:
            # API 要拿原始文件内容；有令牌时带上，避免匿名限额（60次/小时）
            cmd[cmd.index("-o"):cmd.index("-o")] = ["-H", "Accept: application/vnd.github.raw"]
            token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
            if token:
                cmd[cmd.index("-o"):cmd.index("-o")] = ["-H", f"Authorization: Bearer {token}"]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=200)
        except subprocess.TimeoutExpired:
            last_err = "下载超时"
            continue
        if result.returncode == 0 and os.path.exists(save_path):
            ok, err = content_ok(save_path)
            if ok:
                return True, ""
            os.remove(save_path)
            last_err = err
        else:
            last_err = f"curl 退出码 {result.returncode}"
    if os.path.exists(save_path):
        os.remove(save_path)
    return False, last_err


# ==============================================
# 规则来源清单
# ==============================================
adblock_rules = [
    #Hosts：
    {"url": "https://raw.githubusercontent.com/lingeringsound/10007_auto/master/all", "name": "1007-Hosts"},
    {"url": "https://raw.githubusercontent.com/lingeringsound/10007_auto/master/reward", "name": "1007-保留奖励名单"},

    #DNS：
    {"url": "https://anti-ad.net/easylist.txt", "name": "anti-ad 官方规则"},
    {"url": "https://gp.adrules.top/dns.txt", "name": "AdRules DNS List"},
    {"url": "https://adguardteam.github.io/AdGuardSDNSFilter/Filters/filter.txt", "name": "AdGuard DNS Filter 官方"},
    {"url": "https://small.oisd.nl/", "name": "OISD 拦截规则"},

    #AdGurad：
    {"url": "https://raw.githubusercontent.com/qq5460168/666/master/rules.txt", "name": "个人合并规则"},
    {"url": "https://raw.githubusercontent.com/damengzhu/banad/main/jiekouAD.txt", "name": "酷安@大萌主"},
    {"url": "https://raw.githubusercontent.com/Thelongdarkorg/ad-rules-merged/main/merged.txt", "name": "浮风拦截规则"},
    {"url": "http://hgzs.uunat.com/hg1.txt", "name": "海哥规则"},
    {"url": "https://raw.githubusercontent.com/TG-Twilight/AWAvenue-Ads-Rule/main/AWAvenue-Ads-Rule.txt", "name": "秋风广告规则"},
    {"url": "https://raw.githubusercontent.com/xinggsf/Adblock-Plus-Rule/master/mv.txt", "name": "乘风视频规则"},
    {"url": "https://raw.githubusercontent.com/xinggsf/Adblock-Plus-Rule/master/rule.txt", "name": "乘风通用规则"},
    {"url": "https://raw.githubusercontent.com/rssvcn/qy-Ads-Rule/main/black.txt", "name": "晴雅拦截规则"},
]

allow_rules = [
    {"url": "https://raw.githubusercontent.com/qq5460168/dangchu/main/white.txt", "name": "当初白名单"},
    {"url": "https://raw.githubusercontent.com/liwenjie119/adg-rules/master/white.txt", "name": "李文杰白名单"},
    {"url": "https://raw.githubusercontent.com/AdguardTeam/AdguardFilters/master/ChineseFilter/sections/allowlist.txt", "name": "AdGuard 中文白名单"},
    {"url": "https://raw.githubusercontent.com/AdguardTeam/AdguardFilters/master/SpywareFilter/sections/allowlist.txt", "name": "AdGuard 跟踪白名单"},
    {"url": "https://raw.githubusercontent.com/BlueSkyXN/AdGuardHomeRules/master/ok.txt", "name": "BlueSkyXN 白名单"},
]

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
# 下载
# ==============================================
failed = []

def fetch_all(rules, prefix):
    for i, rule in enumerate(rules):
        url, name = rule["url"], rule["name"]
        save_path = os.path.join(TMP_DIR, f"{prefix}_{i+1:02d}.txt")
        ok, err = download_file(url, save_path)
        if ok:
            write_source_header(save_path, name, url)
            print(f"✅ 下载成功：{name}")
        else:
            failed.append(name)
            print(f"❌ 下载失败：{name} —— {err}")
        time.sleep(1)

fetch_all(adblock_rules, "adblock")
fetch_all(allow_rules, "allow")

total = len(adblock_rules) + len(allow_rules)
print(f"\n📊 下载结果：成功 {total - len(failed)}/{total}")
if failed:
    print("❌ 失败清单：" + "、".join(failed))

# ==============================================
# 闸门：全部失败或失败过半 → 中止工作流，绝不发布残缺规则
# ==============================================
if len(failed) * 2 >= total:
    print(f"\n🚫 失败来源达 {len(failed)}/{total}，判定为网络/上游大面积故障，中止本次更新（不发布残缺规则）。")
    sys.exit(1)

print("\n🎉 全部下载完成 + 来源已自动写入！")
