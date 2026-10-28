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
import json
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../.."))
sys.path.insert(0, SCRIPT_DIR)
from fetch import download_file

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
# 下载后方向体检：放错清单的源当场报警
# 白名单文件里混几条拦截语法是常态（上游自带的防误杀），但若
# 拦截语法占大头，多半是把黑名单错挂到了 allow_rules——
# 现在线上就报警，不用等 merge 阶段才发现白名单把规则砍光了。
# ==============================================
def sanity_hint(path, prefix):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
    except OSError:
        return
    n_allow = n_block = 0
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith(("!", "#", "[")):
            continue
        if s.startswith("@@"):
            n_allow += 1
        elif s.startswith("||") or is_hosts_block(s):
            n_block += 1
    if n_allow + n_block < 20:
        return  # 样本太少，不判方向
    if prefix == "allow" and n_block > n_allow * 2:
        print(f"⚠️  方向警告：{os.path.basename(path)} 拦截语法 {n_block} 条 ≫ 放行语法 {n_allow} 条，"
              f"疑似黑名单被误挂到 allow_rules，请用 probe_source.py 核实！")
    elif prefix == "adblock" and n_allow > n_block and n_allow > 100:
        print(f"⚠️  方向警告：{os.path.basename(path)} 放行语法 {n_allow} 条 ≫ 拦截语法 {n_block} 条，"
              f"疑似白名单被误挂到 adblock_rules，请用 probe_source.py 核实！")


def is_hosts_block(line):
    """0.0.0.0/127.0.0.1 指向正常域名 → 拦截语义"""
    m = re.match(r"^(?:0\.0\.0\.0|127\.0\.0\.\d+)\s+(\S+)$", line)
    if not m:
        return False
    t = m.group(1).lower()
    return "." in t and not t.replace(".", "").isdigit()


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
    {"url": "https://raw.githubusercontent.com/abclq/home-dns-adblock/refs/heads/main/dist/hosts.txt", "name": "abclq Hosts 拦截规则"},
]

allow_rules = [
    {"url": "https://raw.githubusercontent.com/qq5460168/dangchu/main/white.txt", "name": "当初白名单"},
    {"url": "https://raw.githubusercontent.com/liwenjie119/adg-rules/master/white.txt", "name": "李文杰白名单"},
    {"url": "https://raw.githubusercontent.com/AdguardTeam/AdguardFilters/master/ChineseFilter/sections/allowlist.txt", "name": "AdGuard 中文白名单"},
    {"url": "https://raw.githubusercontent.com/AdguardTeam/AdguardFilters/master/SpywareFilter/sections/allowlist.txt", "name": "AdGuard 跟踪白名单"},
    {"url": "https://raw.githubusercontent.com/BlueSkyXN/AdGuardHomeRules/master/ok.txt", "name": "BlueSkyXN 白名单"},
    {"url": "https://raw.githubusercontent.com/abclq/home-dns-adblock/refs/heads/main/config/whitelist.txt", "name": "abclq 防误杀白名单"},
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
dl_status = []   # 源健康度：clean-readme.py 读取后写入 README

MAX_WORKERS = 5  # 并发下载数：对上游保持礼貌，5 线程已能把 21 源从串行 2 分钟压到半分钟内

def fetch_one(i_rule, prefix):
    i, rule = i_rule
    url, name = rule["url"], rule["name"]
    save_path = os.path.join(TMP_DIR, f"{prefix}_{i+1:02d}.txt")
    ok, err, _ = download_file(url, save_path)
    if ok:
        write_source_header(save_path, name, url)
        sanity_hint(save_path, prefix)
    return name, ok, err

def fetch_all(rules, prefix):
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        # map 保序：输出顺序与清单一致，便于对照
        for name, ok, err in pool.map(fetch_one, list(enumerate(rules)), [prefix] * len(rules)):
            if ok:
                dl_status.append({"name": name, "ok": True, "err": ""})
                print(f"✅ 下载成功：{name}")
            else:
                failed.append(name)
                dl_status.append({"name": name, "ok": False, "err": err})
                print(f"❌ 下载失败：{name} —— {err}")

fetch_all(adblock_rules, "adblock")
fetch_all(allow_rules, "allow")

# 健康度落盘：clean-readme.py 读取并渲染进 README
try:
    with open(os.path.join(TMP_DIR, "dl_status.json"), "w", encoding="utf-8") as f:
        json.dump(dl_status, f, ensure_ascii=False, indent=1)
except OSError as e:
    print(f"⚠️ 源健康度写入失败（不影响主流程）：{e}")

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
