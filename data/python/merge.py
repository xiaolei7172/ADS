# -*- coding: utf-8 -*-
"""
合并黑名单与白名单。
改进点（相对旧版）：
  1. 白名单过滤改为父子域匹配：@@||a.com^ 会放行 a.com 及其全部子域
     （旧版只做全等匹配，子域会被误拦）；
  2. 非法白名单行（如带空格的 @@||download- *.com^）不再进入匹配集合；
  3. 过滤混入的回环地址行（127.0.0.1 localhost 等）；
  4. 删除原第 4 段 dns.txt 生成——它会被 filter-dns.py 用 w 模式
     整个覆盖，属于死代码；dns.txt 统一由 filter-dns.py 生成。
"""
import os
import glob
import json
import re
import sys
from itertools import islice

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from common import (
    RULES_DIR, TMP_DIR, MOD_DIR,
    allow_domain, block_domain, is_allowed, is_junk_hosts_line, count_valid_lines, valid_domain,
    hosts_target,
)

os.makedirs(TMP_DIR, exist_ok=True)
os.makedirs(RULES_DIR, exist_ok=True)

# ==========================================
# 规则语法清洗：丢掉"看着像规则、实际有害或无效"的行
# 上游合并源里混着三类脏数据，必须挡在成品之外：
#   1. $badfilter —— AdGuard 里用于"取消某条规则"，留着等于反向放行广告；
#   2. ||domain. —— 尾点多一个句点，AdGuard 语法无效，纯废行；
#   3. 非回环 IP 的 hosts 行（如 110.43.121.13 bigota.d.miui.com）——
#      这是 IP 加速映射而非拦截，留着会把用户域名强行指向某 IP 造成故障。
# ==========================================
RE_IP_HOSTS = re.compile(r"^(?:\d{1,3}(?:\.\d{1,3}){3}|[0-9a-fA-F:]+)\s+\S+$")
LOOPBACK_IPS = {"0.0.0.0", "127.0.0.1", "::1", "::", "255.255.255.255"}

def is_bad_rule(line):
    if "$badfilter" in line.lower():
        return True
    if line.startswith("||") and line.endswith("."):
        return True
    if RE_IP_HOSTS.match(line):
        ip = line.split()[0].lower()
        if ip not in LOOPBACK_IPS and not ip.startswith("127."):
            return True
    return False

# ==========================================
# 智能提取头部信息
# ==========================================
def get_rule_meta(file_path):
    title = ""
    desc = ""
    source_name = "未知来源"
    source_url = "未知地址"

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            # islice：只要前 80 行。旧写法 readlines()[:80] 会先把整个文件
            # （单源最大 10 MB）读成列表再切片，白读 99% 的内容
            for line in islice(f, 80):
                line = line.strip()
                if line.startswith("! Title:"):
                    title = line.replace("! Title:", "").strip()
                if line.startswith("! Description:"):
                    desc = line.replace("! Description:", "").strip()
                if line.startswith("! 📋 规则来源："):
                    source_name = line.replace("! 📋 规则来源：", "").strip()
                if line.startswith("! 🔗 原始地址："):
                    source_url = line.replace("! 🔗 原始地址：", "").strip()
    except OSError:
        pass

    if not desc.strip():
        desc = "广告拦截规则"
    final_name = f"{source_name} [{title}]" if title.strip() else source_name
    return final_name, desc, source_url

# ==========================================
# 1. 收集所有白名单（内置 + 远程 + 本地）
# ==========================================
print("🚀 收集全部白名单（内置+远程+本地）")
all_white_raw = set()
ad_files = sorted(glob.glob(os.path.join(TMP_DIR, "adblock_*.txt")))
allow_files = sorted(glob.glob(os.path.join(TMP_DIR, "allow_*.txt")))
local_white_path = os.path.join(MOD_DIR, "whitelist.txt")
local_black_path = os.path.join(MOD_DIR, "adblock.txt")
local_exclude_path = os.path.join(MOD_DIR, "exclude.txt")

# ==========================================
# 死规则清单：域名已不存在（NXDOMAIN）的上游规则不再写入产物
# 由 probe-dead.py 生成（UDP 直连两台公共 DNS，都返回 RCODE=3 才判死）。
# 只过滤上游规则：本地自定义规则是用户明确要拦的，不参与——
# 即使域名暂时解析不出来，也不该由脚本替用户删掉。
#
# 安全阀：清单体量与当前拦截规模严重不成比例时整份忽略。
# dead.txt 是「删除名单」，一旦被投毒/写坏，能把产物清空；
# 正常水位约 11%，超过 35% 说明文件本身有问题，宁可这次不清理。
# ==========================================
dead_path = os.path.join(MOD_DIR, "dead.txt")
dead_set = set()
dead_skipped = 0
if os.path.exists(dead_path):
    with open(dead_path, "r", encoding="utf-8", errors="ignore") as _df:
        for _line in _df:
            _s = _line.strip()
            if _s and not _s.startswith(("!", "#")):
                dead_set.add(_s.lower())
    _block_hint = sum(count_valid_lines(_p) for _p in ad_files)
    if not dead_set:
        print("☠️ 死规则清单为空，跳过")
    elif _block_hint and len(dead_set) > max(_block_hint * 0.35, 1000):
        print(f"⚠️ 死规则清单 {len(dead_set):,} 条 vs 上游拦截 {_block_hint:,} 条，"
              f"占比 {len(dead_set) / _block_hint:.0%} 明显异常，本次忽略该清单（不删任何规则）")
        dead_set = set()
    else:
        print(f"☠️ 已加载死规则清单：{len(dead_set):,} 条（data/mod/dead.txt），上游规则命中即剔除")

# ==========================================
# 精确剔除表：只删"过宽的那一条"规则，不做父子域折叠
# 白名单治不了这类源——@@||company.com^ 会连带废掉几十条子域拦截，
# 副作用比问题本身还大；剔除表按域名逐条对齐，子域规则原样保留。
# ==========================================
exclude_block_domains = set()
exclude_allow_domains = set()
# 非常规形态的剔除（||pinduoduo.*^ 这类 TLD 通配、||*.domain^ 子域通配）：
# 域名正则认不出来，但这类规则恰恰最需要拆——一条通配能把整个品牌端掉。
exclude_block_raw = set()
if os.path.exists(local_exclude_path):
    with open(local_exclude_path, "r", encoding="utf-8", errors="ignore") as _f:
        for _line in _f:
            _s = _line.strip()
            if not _s or _s.startswith(("!", "#")):
                continue
            if _s.startswith("@@"):
                _d = allow_domain(_s)
                if _d:
                    exclude_allow_domains.add(_d)
            else:
                _d = block_domain(_s) or hosts_target(_s)
                if _d:
                    exclude_block_domains.add(_d)
                else:
                    _low = _s.lower()
                    if _low.startswith("||") and _low.endswith("^"):
                        exclude_block_raw.add(_low)
    print(f"🧯 已加载精确剔除表：data/mod/exclude.txt"
          f"（拦截 {len(exclude_block_domains)} 条 / 通配 {len(exclude_block_raw)} 条"
          f" / 放行 {len(exclude_allow_domains)} 条）")

def collect_white(path, convert_bare=False):
    """收集 @@ 白名单行；convert_bare=True 时把裸域名行转为 @@||domain^。

    背景：部分上游源（如 abclq/home-dns-adblock 的 config/whitelist.txt）
    用"一行一个域名"的配置格式表达白名单（子域自动保护），需转换后才能
    进入 AdGuard 语法管线。仅对白名单文件启用，拦截文件不受影响。
    """
    n = 0
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if line.startswith("@@"):
                all_white_raw.add(line)
                n += 1
            elif convert_bare and line and not line.startswith(("#", "!", "[")) and valid_domain(line):
                rule = f"@@||{line}^"
                if rule not in all_white_raw:
                    all_white_raw.add(rule)
                    n += 1
    return n

for file in ad_files:
    collect_white(file)
for file in allow_files:
    collect_white(file, convert_bare=True)
if os.path.exists(local_white_path):
    n = collect_white(local_white_path, convert_bare=True)
    print(f"✅ 已加载本地白名单：data/mod/whitelist.txt（{n} 条）")

# 精确剔除过宽的放行规则（如 @@||ucweb.com^ 会把 46 条 UC 广告域一起放行）。
# 必须在构建 allow_domain_set 之前剔除，否则子域拦截已被 is_allowed 判掉。
if exclude_allow_domains:
    _before = len(all_white_raw)
    all_white_raw = {r for r in all_white_raw
                     if (allow_domain(r) or "") not in exclude_allow_domains}
    print(f"🧯 精确剔除过宽放行规则 {_before - len(all_white_raw)} 条（data/mod/exclude.txt）")

# 白名单域名集合：只收合法行，跳过带空格等非法行
# （旧写法在 print 里又跑了一遍全量 allow_domain 推导式，等于多算两次）
allow_domain_set = set()
n_invalid_white = 0
for rule in all_white_raw:
    d = allow_domain(rule)
    if d:
        allow_domain_set.add(d)
    else:
        n_invalid_white += 1
print(f"📊 合法白名单域名：{len(allow_domain_set)} 个（丢弃非法白名单行 {n_invalid_white} 条）")

# ==========================================
# 2. 合并黑名单（自动过滤 + 写入本地自定义）
# ==========================================
print("🚀 合并黑名单并过滤冲突")
black_output = []
black_set = set()
blocked_by_white = 0
junk_skipped = 0
bad_skipped = 0
excluded_block = 0

def append_black(path):
    global junk_skipped, bad_skipped, excluded_block, dead_skipped
    final_name, desc, url = get_rule_meta(path)
    new_rules = []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith(("!", "#", "[", "@@")):
                continue
            # 回环地址行（127.0.0.1 localhost 之类）直接丢弃
            if is_junk_hosts_line(line):
                junk_skipped += 1
                continue
            # $badfilter / 尾点规则 / IP 加速映射行：不是拦截语义，丢弃
            if is_bad_rule(line):
                bad_skipped += 1
                continue
            # 精确剔除：只拆过宽的那一条（如 ||bytedance.com^），子域规则保留
            if exclude_block_raw and line.lower() in exclude_block_raw:
                excluded_block += 1
                continue
            if exclude_block_domains:
                _d = block_domain(line) or hosts_target(line)
                if _d and _d in exclude_block_domains:
                    excluded_block += 1
                    continue
            # 死规则：域名已 NXDOMAIN（probe-dead.py 双服务器确认），不再写入
            if dead_set:
                _dd = block_domain(line) or hosts_target(line)
                if _dd and _dd in dead_set:
                    dead_skipped += 1
                    continue
            # 大小写不敏感去重：||Media.net^ 与 ||media.net^ 是同一条规则
            key = line.lower()
            if key not in black_set:
                black_set.add(key)
                new_rules.append(line)
    if not new_rules:
        # 该来源的规则已全部被前面的来源覆盖，不写空分区头
        return 0
    black_output.extend([
        "! ==============================================",
        f"! 📋 规则来源：{final_name}",
        f"! 📝 规则说明：{desc}",
        f"! 🔗 原始地址：{url}",
        "! ==============================================",
    ])
    black_output.extend(new_rules)
    return len(new_rules)

for file in ad_files:
    append_black(file)

# 本地黑名单（优先级最高）
# 注意：dl.py 已把本地规则作为"源 00"（adblock_00.txt）注入，
# 这里通常已被上面去重吸收；只有本地分区带来新规则时才写分区头，
# 避免在 adblock.txt 末尾留下没有规则的空分区。
local_rule_lines = set()  # 本地自定义规则：豁免白名单过滤（用户明确意图）
if os.path.exists(local_black_path):
    print("✅ 已加载本地黑名单：data/mod/adblock.txt")
    local_new = []
    with open(local_black_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith(("!", "#", "[", "@@")):
                continue
            # 本地规则同样过一遍语法清洗（手写也可能误抄 IP 映射/尾点）
            if is_bad_rule(line):
                bad_skipped += 1
                continue
            local_rule_lines.add(line)
            key = line.lower()
            if key not in black_set:
                black_set.add(key)
                local_new.append(line)
    if local_new:
        black_output.extend([
            "! ==============================================",
            "! 📋 规则来源：本地自定义规则（data/mod/adblock.txt）",
            "! ⚠️ 优先级：最高",
            "! ==============================================",
        ])
        black_output.extend(local_new)

# ==========================================
# 可信通配白名单展开
# 上游白名单常用 @@||v*.douyinvod.com^ 这类通配放行 CDN 节点，
# 但 DNS 层域名集合只收纯域名，通配全部静默失效——上游黑名单
# 拦掉的节点无人兜底，被调度到这些节点的视频/图片加载失败。
# 解决：data/mod/wildcard_allow.txt 是经人工甄别的「可信模式表」
# （整组都是功能/CDN 域、不含广告），合并时把命中的拦截域名
# 展开为具体 @@||domain^ 加入白名单并参与过滤。
# 未列入本表的上游通配（如 *.a.yximgs.com 广告集群、t*.baidu.com
# 追踪域）继续忽略——忽略它们本身就是防线：盲目展开实测会放行
# 76 条规则，其中近半是广告/埋点。
# ==========================================
wildcard_expanded = []
wildcard_pat_path = os.path.join(MOD_DIR, "wildcard_allow.txt")
if os.path.exists(wildcard_pat_path):
    wild_pats = []
    with open(wildcard_pat_path, "r", encoding="utf-8") as _wf:
        for _line in _wf:
            _s = _line.split("!")[0].strip()   # 去行内注释
            if not _s or _s.startswith("#"):
                continue
            wild_pats.append(
                re.compile("^" + ".*".join(re.escape(x) for x in _s.split("*")) + "$"))
    if wild_pats:
        for _key in black_set:
            # 拦截规则有两种形态：||domain^ 与 0.0.0.0 domain（hosts），都要展开
            _dom = block_domain(_key) or hosts_target(_key)
            if not _dom:
                continue
            if _dom in exclude_allow_domains:
                continue
            if any(p.fullmatch(_dom) for p in wild_pats):
                _rule = f"@@||{_dom}^"
                if _rule not in all_white_raw:
                    all_white_raw.add(_rule)
                    allow_domain_set.add(_dom)
                    wildcard_expanded.append(_rule)
        print(f"🪄 可信通配展开：{len(wild_pats)} 个模式 → 新增放行 {len(wildcard_expanded)} 条"
              f"（data/mod/wildcard_allow.txt）")

# 白名单过滤统一放最后：黑名单里逐行判断代价高，改为
# 先收集 ||domain^ 行，再按父子域过滤。
# 本地自定义规则（data/mod/adblock.txt）豁免过滤——用户明确要拦的域，
# 即使被远程白名单放行也照样拦（「优先级：最高」落到代码上）。
final_black = []
exempt = 0
kept_block_rules = 0
wildcard_whitelisted = 0
for line in black_output:
    if line in local_rule_lines:
        final_black.append(line)
        if line.startswith("||"):
            kept_block_rules += 1
        continue
    if line.startswith("||") and line.endswith("^"):
        dom = line[2:-1].lower()
        # 通配规则的放行判定以基域为准：||*.pddpic.com^ 的拦截对象是整个子域族，
        # 白名单写 @@||pddpic.com^ 就该放行它。以前只认纯域名——block_domain 的正则不
        # 含 '*'，通配行在第二步匹配不到 allow_domain_set，于是"白名单写了、DNS 产物也
        # 干净，AdGuard 订阅里那条通配还在"，用户照样打不开图片/直播。
        if dom.startswith("*.") and is_allowed(dom[2:], allow_domain_set):
            wildcard_whitelisted += 1
            blocked_by_white += 1
            continue
        if is_allowed(dom, allow_domain_set):
            blocked_by_white += 1
            continue
        kept_block_rules += 1
    elif not line.startswith(("@@")):
        # hosts 行（0.0.0.0 domain）也要过白名单。以前只处理 ||domain^ 形态，
        # 于是整域放行 pddpic.com 之后 adblock.txt 里仍留着 0.0.0.0 video-dsp.pddpic.com：
        # dns.txt 靠 filter-dns 第二遍过滤是干净的，但直接订阅 adblock.txt、
        # 或把 adblock.txt 转 hosts 的用户照样被拦——同一份规则自己跟自己打架。
        hd = hosts_target(line)
        if hd and is_allowed(hd, allow_domain_set):
            blocked_by_white += 1
            continue
    final_black.append(line)

# ==========================================
# 闸门：白名单污染熔断
# 一条被投毒/错配的白名单上游（如整域 @@||qq.com^ 混进远程源）
# 能把几十万条拦截规则砍到残废。移除比例异常即中止发布——
# 宁可这次不更新，也不能发布被白名单清空的残缺规则。
# 正常运行时该比例约 1~2%，阈值放宽到 8% 留足余量。
# ==========================================
removed_ratio = blocked_by_white / max(kept_block_rules + blocked_by_white, 1)
if removed_ratio > 0.08:
    print(f"\n🚫 白名单熔断：{blocked_by_white}/{kept_block_rules + blocked_by_white} 条拦截规则"
          f"（{removed_ratio:.1%}）被白名单放行移除，远超正常水位（≈2%）。"
          f"疑似某路白名单源被投毒或黑白错配，中止本次更新。")
    sys.exit(1)

with open(os.path.join(RULES_DIR, "adblock.txt"), "w", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(final_black) + "\n")

# ==========================================
# 3. 合并完整白名单（含本地自定义）
# ==========================================
print("🚀 合并完整白名单（含本地自定义）")
white_output = []

def append_white(path, tag):
    final_name, _, _ = get_rule_meta(path)
    tmp = []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if line.startswith("@@"):
                if line in all_white_raw:
                    tmp.append(line)
            elif line and not line.startswith(("#", "!", "[")) and valid_domain(line):
                # 裸域名行：与 collect_white 相同的转换，命中集合才输出
                rule = f"@@||{line}^"
                if rule in all_white_raw:
                    tmp.append(rule)
    if tmp:
        white_output.extend([
            "! ==============================================",
            f"! 📋 白名单来源：{final_name}（{tag}）",
            "! ==============================================",
        ])
        white_output.extend(tmp)

# 通配展开的放行条目没有所属上游分区，写独立分区（便于溯源与审计）
if wildcard_expanded:
    white_output.extend([
        "! ==============================================",
        "! 📋 白名单来源：可信通配展开（data/mod/wildcard_allow.txt）",
        "! ⚠️ 上游通配白名单在 DNS 层无法表达，此处为按可信模式展开的具体域名",
        "! ==============================================",
    ])
    white_output.extend(sorted(wildcard_expanded))

for file in ad_files:
    append_white(file, "规则内置")
for file in allow_files:
    append_white(file, "远程白名单")
if os.path.exists(local_white_path):
    final_name, _, _ = get_rule_meta(local_white_path)
    tmp = []
    with open(local_white_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if line.startswith("@@") and line in all_white_raw:
                tmp.append(line)
    if tmp:
        white_output.extend([
            "! ==============================================",
            "! 📋 白名单来源：本地自定义规则（data/mod/whitelist.txt）",
            "! ⚠️ 优先级：最高",
            "! ==============================================",
        ])
        white_output.extend(tmp)

final_white = list(dict.fromkeys(white_output))

# 本地自定义拦截域（data/mod/adblock.txt）覆盖的 @@ 行必须从白名单成品剔除：
# AdGuard 中 @@ 放行优先于拦截，不剔除会让本地规则对双规则订阅用户失效。
local_block_domains = set()
if os.path.exists(local_black_path):
    with open(local_black_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            d = block_domain(line)
            if d:
                local_block_domains.add(d)
if local_block_domains:
    before = len(final_white)
    final_white = [l for l in final_white
                   if not (l.startswith("@@") and is_allowed(allow_domain(l) or "", local_block_domains))]
    print(f"✂️  因本地自定义拦截域，从白名单剔除 {before - len(final_white)} 条放行规则")

with open(os.path.join(RULES_DIR, "allow.txt"), "w", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(final_white) + "\n")

# ==========================================
# 完成
# ==========================================
print("\n✅ 全部合并完成！本地黑白名单均已完整写入！")
print(f"📊 黑名单：{count_valid_lines(os.path.join(RULES_DIR, 'adblock.txt'))} 条")
print(f"📊 白名单：{len(all_white_raw)} 条")
print(f"🚫 因白名单（父子域）放行而移除的拦截规则：{blocked_by_white} 条（本地自定义规则豁免）")
if wildcard_whitelisted:
    print(f"🪄 其中通配规则（||*.domain^）按基域白名单放行：{wildcard_whitelisted} 条")
print(f"🧯 因精确剔除表移除的过宽拦截规则：{excluded_block} 条（data/mod/exclude.txt）")
print(f"☠️ 因域名已不存在（NXDOMAIN）移除：{dead_skipped} 条（data/mod/dead.txt）")
print(f"🧹 丢弃回环/垃圾行：{junk_skipped} 条")
print(f"🧽 丢弃无效/有害语法（$badfilter、尾点规则、IP 映射行）：{bad_skipped} 条")
print("ℹ️  dns.txt 由 filter-dns.py 统一生成（原第 4 段会被它覆盖，已移除）")

# ==========================================
# 合并统计落盘
# clean-readme.py 的「总量骤降」闸门要扣除「死规则清理」这种**计划内**的减少，
# 否则第一次大规模清理（一次砍掉一成）会被判成上游腰斩，永远上不了线。
# 白名单移除量一并落盘，方便事后核对熔断阈值是否合理。
# ==========================================
try:
    with open(os.path.join(TMP_DIR, "merge-stats.json"), "w", encoding="utf-8") as _sf:
        json.dump({
            "dead_skipped": dead_skipped,
            "dead_list_size": len(dead_set),
            "blocked_by_white": blocked_by_white,
            "excluded_block": excluded_block,
            "kept_block_rules": kept_block_rules,
        }, _sf, ensure_ascii=False, indent=1)
except OSError as _e:
    print(f"⚠️ 合并统计写入失败（不影响产物）：{_e}")
