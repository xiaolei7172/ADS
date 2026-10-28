# -*- coding: utf-8 -*-
"""
源探针：新源接入前先验证 —— 自动分辨白名单/黑名单 + 冲突预演。

背景：接新源时最容易踩两个坑——
  1. 黑白不分：把黑名单挂进 allow_rules（放行广告），或白名单挂进
     adblock_rules（白名单成品被当拦截规则，语义全反）；
  2. 未知冲突：白名单接进去才发现它放行的域，正好砍掉现有几十万条
     拦截规则里的几千条，误杀防线瞬间开洞。

用法：
  python probe_source.py <url>              # 自动分类（推荐）
  python probe_source.py <url> allow        # 强制按白名单分析
  python probe_source.py <url> block        # 强制按黑名单分析

判定逻辑：
  A. 语法统计：@@||d^ → 放行；||d^ / 0.0.0.0 d → 拦截；裸域名 → 中性
  B. 文件名启发：whitelist/white/allow/ok/exempt → 白名单侧；其余 → 黑名单侧
  C. 白名单探针会额外做「冲突预演」：算出新源将放行而现有拦截规则
     仍在拦的域名数，并列出受影响域名，接入前先看清楚要放什么。
"""
import os
import sys
import tempfile

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from fetch import download_file
from common import (
    allow_domain, block_domain, hosts_target, valid_domain, is_allowed,
    RULES_DIR, MOD_DIR,
)

# ----------------------------------------
# 文件名启发：与白名单强相关的词
# ----------------------------------------
ALLOW_HINTS = ("whitelist", "white", "allow", "ok.", "exempt", "trust", "bai", "pass")
BLOCK_HINTS = ("blacklist", "black", "adblock", "block", "hosts", "dns", "ad-",
               "filter", "ban", "adblock", "deny")


def name_hint(url):
    low = url.rsplit("/", 1)[-1].lower()
    if any(h in low for h in ALLOW_HINTS):
        return "allow"
    if any(h in low for h in BLOCK_HINTS):
        return "block"
    return "unknown"


# ----------------------------------------
# 语法统计
# ----------------------------------------
def analyze(path):
    stats = {"allow": 0, "block": 0, "hosts": 0, "bare": 0, "other": 0, "comment": 0}
    allow_domains, block_domains = set(), set()
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith(("!", "#", "[")):
                stats["comment"] += 1
                continue
            d = allow_domain(s)
            if d:
                stats["allow"] += 1
                allow_domains.add(d)
                continue
            d = block_domain(s)
            if d:
                stats["block"] += 1
                block_domains.add(d)
                continue
            d = hosts_target(s)
            if d:
                stats["hosts"] += 1
                block_domains.add(d)
                continue
            if valid_domain(s):
                stats["bare"] += 1
                continue
            stats["other"] += 1
    return stats, allow_domains, block_domains


def classify(stats, url):
    """返回 (判定, 置信度, 依据说明)"""
    n_allow, n_block = stats["allow"], stats["block"] + stats["hosts"]
    total = n_allow + n_block + stats["bare"]
    hint = name_hint(url)
    if total < 20:
        if hint != "unknown":
            return hint, "低", (f"有效规则仅 {total} 条，语法信号不足；文件名含"
                                f"{'白名单' if hint == 'allow' else '黑名单'}关键词，建议加参数强制复核确认")
        return None, 0, f"有效规则太少（{total} 条）且文件名无黑白线索，无法判定"
    # 语法占主导：@@ 占比高 → 白名单
    if n_allow > total * 0.5 and n_block < total * 0.2:
        return "allow", "高", f"放行语法 {n_allow}/{total} 条（{n_allow/total:.0%}），拦截语法仅 {n_block} 条"
    # 拦截语法占主导 → 黑名单
    if n_block > total * 0.5 and n_allow < total * 0.2:
        return "block", "高", f"拦截语法 {n_block}/{total} 条（{n_block/total:.0%}），放行语法仅 {n_allow} 条"
    # 裸域名为主 → 文件名定方向（拦截清单收裸域名=域名黑名单；白名单收裸域名=配置格式）
    if stats["bare"] > total * 0.5:
        if hint == "allow":
            return "allow", "中", f"裸域名 {stats['bare']}/{total} 条 + 文件名含白名单关键词（裸域名按 @@||d^ 转换接入）"
        if hint == "block":
            return "block", "中", f"裸域名 {stats['bare']}/{total} 条 + 文件名含黑名单关键词"
        return None, 0, f"裸域名 {stats['bare']}/{total} 条且文件名无黑白线索，需人工判断"
    # 混合文件
    return "mixed", "低", f"放行 {n_allow} 条 / 拦截 {n_block} 条 / 裸域名 {stats['bare']} 条，比例接近，属混合文件"


# ----------------------------------------
# 冲突预演
# ----------------------------------------
def load_current_allows():
    """现有白名单域名：成品 allow.txt + 本地 mod/whitelist.txt"""
    allows = set()
    for path in (os.path.join(RULES_DIR, "allow.txt"),
                 os.path.join(MOD_DIR, "whitelist.txt")):
        if not os.path.exists(path):
            continue
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                d = allow_domain(line)
                if d:
                    allows.add(d)
    return allows


def load_dns_block_domains():
    """现有 DNS 拦截域名（data/rules/dns.txt 的 ||d^ 行）"""
    blocks = set()
    path = os.path.join(RULES_DIR, "dns.txt")
    if not os.path.exists(path):
        return blocks
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            d = block_domain(line)
            if d:
                blocks.add(d)
    return blocks


def rehearse_allow(candidate_domains):
    """白名单冲突预演：新放行域 vs 现有拦截域，返回 (放行影响明细, 统计)"""
    current_allows = load_current_allows()
    dup = len(candidate_domains) - sum(1 for d in candidate_domains
                                       if not is_allowed(d, current_allows))
    new_allows = {d for d in candidate_domains if not is_allowed(d, current_allows)}
    dns_blocks = load_dns_block_domains()
    affected = {}          # 会被解封的现有拦截域名 → 命中的新放行域
    unaffected_new = 0     # 新放行域当前没在拦（不产生变化）
    for d in new_allows:
        hit = [b for b in dns_blocks if is_allowed(b, {d})]
        if hit:
            for b in hit:
                affected[b] = d
        else:
            unaffected_new += 1
    return affected, len(new_allows), unaffected_new, dup


def rehearse_block(candidate_domains):
    """黑名单冲突预演：与现有 DNS 拦截的重叠度"""
    dns_blocks = load_dns_block_domains()
    dup = sum(1 for d in candidate_domains if is_allowed(d, dns_blocks) or d in dns_blocks)
    new = len(candidate_domains) - dup
    return dup, new


# ----------------------------------------
# 主流程
# ----------------------------------------
def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    url = sys.argv[1]
    forced = sys.argv[2] if len(sys.argv) > 2 else None

    print(f"🔍 源探针启动：{url}\n")

    # 1. 试下载（与正式管线同通道同体检）
    tmp = os.path.join(tempfile.gettempdir(), "tianying_probe.txt")
    ok, err, used = download_file(url, tmp)
    if not ok:
        print(f"❌ 下载失败：{err}\n   六通道全部不可达，暂不接入（等上游恢复再探）。")
        sys.exit(1)
    used_channel = "raw 直连" if used == url else f"镜像兜底：{used.rsplit('/', 2)[0]}"
    print(f"✅ 下载成功（{used_channel}），{os.path.getsize(tmp)} 字节")

    # 2. 语法统计 + 自动分类
    stats, allow_doms, block_doms = analyze(tmp)
    print(f"\n📊 语法统计：放行(@@) {stats['allow']} · 拦截(||) {stats['block']} · "
          f"hosts拦截 {stats['hosts']} · 裸域名 {stats['bare']} · 其他 {stats['other']} · 注释 {stats['comment']}")

    verdict, confidence, reason = classify(stats, url)
    if forced:
        verdict, confidence = forced, "用户强制"
        reason = f"用户指定按 {'白名单' if forced == 'allow' else '黑名单'} 分析"
    if verdict is None:
        print(f"\n❓ 无法自动判定：{reason}")
        print("   请人工查看文件头部说明后，加参数重跑：python probe_source.py <url> allow|block")
        sys.exit(2)

    tag = "🟢 白名单" if verdict == "allow" else "🔴 黑名单"
    if verdict == "mixed":
        tag = "🟡 混合文件"
    print(f"\n🧭 判定：{tag}（置信度：{confidence}）")
    print(f"   依据：{reason}")

    # 3. 冲突预演
    if verdict == "allow":
        candidate = set(allow_doms) | ({d for d in
                                        (l.strip() for l in open(tmp, encoding="utf-8", errors="ignore"))
                                        if valid_domain(d)} if stats["bare"] else set())
        affected, n_new, n_neutral, n_dup = rehearse_allow(candidate)
        print(f"\n⚗️  冲突预演（白名单）：")
        print(f"   候选放行域 {len(candidate)} 条：与现有白名单重复 {n_dup} 条，"
              f"净新增 {n_new} 条（其中 {n_neutral} 条当前无拦截规则在拦）")
        if not affected:
            print("   ✅ 零冲突：这些放行域目前没有任何拦截规则在拦，接入零风险")
        else:
            print(f"   ⚠️ 将解封 {len(affected)} 条现有拦截规则，受影响域名（前 20 条）：")
            for i, (b, a) in enumerate(sorted(affected.items())[:20]):
                print(f"      {b}  ←被 {a} 放行")
            if len(affected) > 20:
                print(f"      ……共 {len(affected)} 条")
            risk = "高危" if len(affected) > 1000 else "需确认" if len(affected) > 50 else "低风险"
            print(f"   风险评级：{risk} —— 请逐条确认这些解封是否符合预期，再决定是否接入")
    elif verdict == "block":
        dup, new = rehearse_block(block_doms)
        print(f"\n⚗️  冲突预演（黑名单）：")
        print(f"   拦截域 {len(block_doms)} 条：与现有 DNS 拦截重复 {dup} 条，预计净新增 {new} 条")
        if len(block_doms) == 0:
            print("   ⚠️ 未解析出任何拦截域名，接入价值存疑")
        elif new == 0:
            print("   ℹ️ 全部与现有规则重叠——接入仅提供多源冗余保障，不会改变拦截面")

    # 4. 接入建议
    print(f"\n📌 接入建议：")
    if verdict == "allow":
        target = "dl.py 的 allow_rules"
    elif verdict == "block":
        target = "dl.py 的 adblock_rules"
    else:
        target = "先人工拆分再决定，不建议整文件接入"
    print(f"   1. 判定通过后，把该 URL 加入 {target}，name 建议带上黑白属性（如 xx 白名单/xx 拦截规则）")
    print(f"   2. 接入后本地跑：python dl.py && python merge.py && python filter-dns.py && python check-quality.py")
    print(f"   3. 正式管线另有双保险：下载方向体检（dl.py）+ 白名单污染熔断（merge.py，移除比例>8% 即中止）")
    os.remove(tmp)


if __name__ == "__main__":
    main()
