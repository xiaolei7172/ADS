# -*- coding: utf-8 -*-
"""
发布前质量自检闸门：验证去重与文件结构的真实性，不合格 exit 1。
检查项：
  1. adblock.txt / allow.txt：0 精确重复（大小写不敏感）；
  2. dns.txt / qx.list / smartdns.conf / dnsmasq.conf / ad-domain.txt / hosts.txt：
     0 精确重复、0 父子域冗余（本地自定义域豁免，与 filter-dns.py 口径一致）；
  3. dns.txt 分区自洽：每个 "! 📊 本区规则：N 条" 与该分区实际行数一致，
     分区总和 = 总行数；
  4. 规则量下限：dns.txt 不得低于 50000 条（防上游大面积故障后带病发布）；
  5. adblock.txt 无脏语法：$badfilter / ||domain. 尾点 / 非回环 IP 映射行；
  6. 跨文件父子域冲突：本地白名单被父域拦截架空即失败（存量登记基线）；
  7. 关键功能域（data/mod/critical-domains.txt）不得被整域拦截。
任何一项失败 → exit 1 拦截 git push，问题不会流到线上。

另附（只报告不拦）：死规则清单（data/mod/dead.txt）的条数与时效——
清单是「已确认 NXDOMAIN」的域，超过 35 天没重跑探测就该更新了，
域名会复活（上游换 CDN 重新启用），旧清单可能删掉已经能用的规则。
"""
import datetime
import os
import re
import sys
from collections import Counter

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from common import RULES_DIR, MOD_DIR, block_domain, allow_domain
from formats import BY_NAME

DNS_FLOOR = 50000
DOMAIN_FILES = ["dns.txt", "qx.list", "smartdns.conf", "ad-domain.txt", "hosts.txt",
                "mihomo.yaml", "surge.list", "dnsmasq.conf"]
# hosts 只能精确匹配，必须保留被折叠的子域才能拦住它们（否则 1.5 万个子域漏网），
# 所以父子域冗余检查对它豁免；精确重复、脏语法仍然照查。
COLLAPSE_EXEMPT = {"hosts.txt"}
RAW_FILES = ["adblock.txt", "allow.txt"]

errors = []

# 本地自定义拦截域：父子域检查豁免（与 filter-dns.py 同口径）
local_block = set()
local_path = os.path.join(MOD_DIR, "adblock.txt")
if os.path.exists(local_path):
    with open(local_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            d = block_domain(line)
            if d:
                local_block.add(d)


def rule_lines(path):
    """返回文件中的规则行（跳过注释/空行），按 formats.py 的声明提取目标域。

    这里不再为每种格式写一个分支：写法与读法都声明在 formats.FORMATS 里，
    生成器用 write、这里用 read，两边不可能再各说各话。
    """
    out = []
    name = os.path.basename(path)
    fmt = BY_NAME.get(name)
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith(("!", "#", "[")):
                continue
            if fmt:
                out.append(fmt.read(line))
            elif name == "dns.txt":
                out.append(block_domain(line))
            else:
                out.append(line.lower())
    return [l for l in out if l]


# ---- 1/2. 精确重复 + 父子域冗余 ----
for name in RAW_FILES + DOMAIN_FILES:
    path = os.path.join(RULES_DIR, name)
    if not os.path.exists(path):
        errors.append(f"{name}: 文件不存在")
        continue
    lines = rule_lines(path)
    if not lines:
        errors.append(f"{name}: 0 条规则，异常")
        continue

    dup = [k for k, v in Counter(lines).items() if v > 1]
    if dup:
        errors.append(f"{name}: {len(dup)} 条精确重复，如 {dup[:3]}")

    if name in DOMAIN_FILES and name not in COLLAPSE_EXEMPT:
        s = set(lines)
        redundant = []
        for d in lines:
            if d in local_block:
                continue  # 本地自定义域豁免
            parts = d.split(".")
            if any(".".join(parts[i:]) in s for i in range(1, len(parts) - 1)):
                redundant.append(d)
        if redundant:
            errors.append(f"{name}: {len(redundant)} 条父子域冗余，如 {redundant[:3]}")

# ---- 3. dns.txt 分区自洽 ----
dns_path = os.path.join(RULES_DIR, "dns.txt")
with open(dns_path, "r", encoding="utf-8", errors="ignore") as f:
    dns_lines = [l.rstrip("\n") for l in f]

declared_total, actual_total, section_declared, section_actual = 0, 0, None, 0
for line in dns_lines:
    line = line.strip()
    if line.startswith("! 📊 本区规则："):
        if section_declared is not None and section_declared != section_actual:
            errors.append(f"dns.txt: 某分区标注 {section_declared} 条，实际 {section_actual} 条")
        try:
            section_declared = int(line.replace("! 📊 本区规则：", "").strip().split()[0])
        except ValueError:
            errors.append(f"dns.txt: 分区计数行解析失败 → {line!r}")
            section_declared = None
        section_actual = 0
        declared_total += section_declared or 0
    elif line.startswith("||") and line.endswith("^"):
        actual_total += 1
        section_actual += 1
if section_declared is not None and section_declared != section_actual:
    errors.append(f"dns.txt: 末分区标注 {section_declared} 条，实际 {section_actual} 条")
if declared_total != actual_total:
    errors.append(f"dns.txt: 分区计数总和 {declared_total} != 实际规则行 {actual_total}")

# ---- 4. 规则量下限 ----
if actual_total < DNS_FLOOR:
    errors.append(f"dns.txt: 仅 {actual_total} 条，低于绝对下限 {DNS_FLOOR}")

# ---- 5. adblock.txt 脏语法（merge.py 已清洗，此处防回归） ----
#   $badfilter       → AdGuard 里用于取消规则，留着等于反向放行广告
#   ||domain.        → 尾点多一个句点，语法无效
#   IP 映射 hosts 行 → 如 110.43.121.13 bigota.d.miui.com，是加速映射不是拦截
RE_IP_HOSTS = re.compile(r"^(?:\d{1,3}(?:\.\d{1,3}){3}|[0-9a-fA-F:]+)\s+\S+$")
LOOPBACK_IPS = {"0.0.0.0", "127.0.0.1", "::1", "::", "255.255.255.255"}
dirty = {"$badfilter": 0, "尾点规则": 0, "IP映射行": 0}
with open(os.path.join(RULES_DIR, "adblock.txt"), "r", encoding="utf-8", errors="ignore") as f:
    for raw in f:
        line = raw.strip()
        if not line or line.startswith(("!", "#", "[")):
            continue
        if "$badfilter" in line.lower():
            dirty["$badfilter"] += 1
        if line.startswith("||") and line.endswith("."):
            dirty["尾点规则"] += 1
        m = RE_IP_HOSTS.match(line)
        if m and m.group(0):
            ip = line.split()[0].lower()
            if ip not in LOOPBACK_IPS and not ip.startswith("127."):
                dirty["IP映射行"] += 1
for kind, n in dirty.items():
    if n:
        errors.append(f"adblock.txt: {n} 条 {kind}（应为 0，merge.py 清洗漏网）")

# ---- 6. 跨文件父子域冲突：白名单子域被黑名单父域架空 ----
# allow.txt 里 @@||img.pddpic.com^ 这类点名放行，若父域 pddpic.com 同时出现在
# 后缀匹配产物里，这条白名单在生产环境等于没写：dnsmasq 的 address=/pddpic.com/0.0.0.0
# 与 DOMAIN-SUFFIX,pddpic.com 都会吃掉全部子域，而这些单文件客户端根本不加载 allow.txt。
# 2026-11-07 拼多多图片/直播/短视频同时挂掉就是这个形状——8 种格式判定完全一致，
# verify-fixes 的一致性闸门天然抓不到"一致地错"，必须单独查黑白名单的父子域关系。
SUFFIX_PRODUCTS = [n for n in DOMAIN_FILES if n not in COLLAPSE_EXEMPT]
suffix_union = set()
for name in SUFFIX_PRODUCTS:
    suffix_union |= set(rule_lines(os.path.join(RULES_DIR, name)))


def parent_in_blacklist(d):
    """返回把 d 架空的父域；无冲突返回 None。本地明确要拦的父域不算冲突。"""
    parts = d.split(".")
    for i in range(1, len(parts) - 1):
        parent = ".".join(parts[i:])
        if parent in local_block:
            return None
        if parent in suffix_union:
            return parent
    return None


def read_allow(path):
    """只取 DNS 层可生效的纯域名白名单（@@||domain^）。

    allow.txt 里另有约 3,267 条路径级 / $domain= / 正则规则，本来就只在浏览器版
    AdGuard 里生效，拿它们比对"被父域架空"没有意义——会报一堆假冲突。
    """
    out = set()
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for raw in f:
            d = allow_domain(raw.strip())
            if d:
                out.add(d)
    return out


# 只对本地白名单（data/mod/whitelist.txt）严格：这些是我们主动写的，必须确保生效。
# 上游白名单有 300+ 条历史失效项（多为分析/统计域，且随上游每日漂移），
# 拿它当发布闸门会让 CI 天天红，故只统计不拦发布。
local_allow = read_allow(os.path.join(MOD_DIR, "whitelist.txt"))
upstream_allow = read_allow(os.path.join(RULES_DIR, "allow.txt")) - local_allow

# 基线：已知且暂未处置的本地冲突，逐条清理后从本文件删除。
# 新加的本地白名单若被父域架空，不在基线里 → 当场失败。
baseline_path = os.path.join(MOD_DIR, "allow-conflicts.baseline")
baseline = set()
if os.path.exists(baseline_path):
    with open(baseline_path, "r", encoding="utf-8", errors="ignore") as f:
        for raw in f:
            s = raw.split("!")[0].strip()
            if s:
                # 每行形如「域名<TAB>父域」，只取第一列做比对
                baseline.add(s.split()[0])

local_conflicts = {d: p for d in local_allow if (p := parent_in_blacklist(d))}
new_conflicts = {d: p for d, p in local_conflicts.items() if d not in baseline}
if new_conflicts:
    sample = [f"{d} ⊂ {p}" for d, p in list(new_conflicts.items())[:3]]
    errors.append(
        f"whitelist.txt: {len(new_conflicts)} 条本地白名单被父域拦截架空，如 {sample}"
        f" —— 子域放行在单文件格式（dnsmasq/qx/surge/mihomo）里不生效，"
        f"要么整域放行、要么拆父域规则；确认可接受则登记到 "
        f"data/mod/allow-conflicts.baseline")

stale_baseline = [d for d in baseline if d in local_allow and d not in local_conflicts]
upstream_conflict_n = sum(1 for d in upstream_allow if parent_in_blacklist(d))

# ---- 7. 关键功能域不得被整域拦截 ----
# 数据在 data/mod/critical-domains.txt，收录政务/银行/支付/运营商/交通/系统更新/公共 CDN
# 等「拦了就是功能故障」的域。为什么需要这道闸门：
#   · verify-fixes 只比对「8 种格式判得一样不一样」，一致地错它抓不到；
#   · 白名单冲突闸门只管「我们主动写的白名单有没有失效」，管不到「上游新拦了一个不该拦的」；
#   · 2026-11-07 平安银行（父域 pingan.com 被海哥源整域端掉）、拼多多（pddpic.com）、
#     同花顺官网、微信群聊图片 CDN（gchat.qpic.cn）四起，全是靠人工体检才发现的。
# 口径：域名自身被拦、或任一上级域被拦（后缀匹配连带），都算失败；
# 行尾 `#exact-ok` 表示只允许这一条精确规则、父域不许拦（如 s.bdstatic.com）。
critical_path = os.path.join(MOD_DIR, "critical-domains.txt")
critical = []
if os.path.exists(critical_path):
    with open(critical_path, "r", encoding="utf-8", errors="ignore") as f:
        for raw in f:
            s = raw.split("!")[0].strip()
            if not s:
                continue
            body, _, note = s.partition("#")
            d = body.strip().lower()
            if d:
                critical.append((d, "exact-ok" in note))
else:
    errors.append("critical-domains.txt: 文件缺失（关键功能域闸门无法生效）")

hosts_exact = set(rule_lines(os.path.join(RULES_DIR, "hosts.txt")))
broken_critical = []
for d, exact_ok in critical:
    hits = []
    if not exact_ok:
        if d in suffix_union:
            hits.append(f"自身被 ||{d}^ 拦")
        elif d in hosts_exact:
            hits.append("自身被 hosts 行拦")
    parts = d.split(".")
    for i in range(1, len(parts) - 1):
        parent = ".".join(parts[i:])
        if parent in suffix_union or parent in hosts_exact:
            hits.append(f"父域 {parent} 被拦（后缀匹配连带）")
            break
    if hits:
        broken_critical.append(f"{d}（{'；'.join(hits)}）")

if broken_critical:
    errors.append(
        f"关键功能域 {len(broken_critical)} 个被整域拦截，如 {broken_critical[:3]}"
        f" —— 这些域拦掉是功能故障（白屏/裂图/登录失败），不是少看一条广告。"
        f"处置：确认该域确属功能域后加进 data/mod/whitelist.txt 整域放行；"
        f"若只是单条精确规则过宽，用 data/mod/exclude.txt 拆那一条")

# ---- 8. 死规则清单：条数与时效（只报告，不拦发布）----
dead_path = os.path.join(MOD_DIR, "dead.txt")
dead_n = 0
dead_age = None
if os.path.exists(dead_path):
    with open(dead_path, "r", encoding="utf-8", errors="ignore") as f:
        head = f.read(1500)
        f.seek(0)
        dead_n = sum(1 for line in f
                     if line.strip() and not line.startswith(("!", "#")))
    m = re.search(r"生成时间：(\d{4}-\d{2}-\d{2})", head)
    if m:
        try:
            dead_age = (datetime.date.today()
                        - datetime.date.fromisoformat(m.group(1))).days
        except ValueError:
            dead_age = None

# ---- 结果 ----
if errors:
    print("🚫 质量自检未通过：")
    for e in errors:
        print(f"   ❌ {e}")
    sys.exit(1)

print(f"✅ 质量自检通过：全部文件 0 重复、0 脏语法，dns.txt {actual_total} 条，分区计数自洽"
      f"（hosts.txt 因需覆盖子域，父子域冗余检查豁免）")
print(f"ℹ️ 本地白名单父子域冲突：{len(local_conflicts)} 条已登记基线"
      f"（data/mod/allow-conflicts.baseline），本轮新增 {len(new_conflicts)} 条")
print(f"ℹ️ 上游白名单另有 {upstream_conflict_n} 条被父域架空"
      f"（分析/统计域为主，随上游每日漂移，仅统计不拦发布）")
print(f"ℹ️ 关键功能域 {len(critical)} 个：0 个被整域拦截（data/mod/critical-domains.txt）")
if dead_n:
    if dead_age is None:
        fresh = "生成时间未知"
    elif dead_age > 35:
        fresh = f"⚠️ 已 {dead_age} 天未更新，建议重跑 probe-dead.py（域名会复活）"
    else:
        fresh = f"{dead_age} 天前探测"
    print(f"☠️ 死规则清单 {dead_n:,} 条已从上游规则中剔除（{fresh}，data/mod/dead.txt）")
if stale_baseline:
    print(f"🧹 基线中 {len(stale_baseline)} 条冲突已消失，可从基线删除：{stale_baseline[:5]}")
