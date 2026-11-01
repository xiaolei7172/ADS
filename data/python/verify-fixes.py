#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证 8 种拦截产物对同一域名的判定是否一致。

解析器统一来自 formats.py（与生成器、质量闸门共用同一份 reader）：
以前这里是 11 种格式各写一套正则，生成器认为写对了、校验器认为没问题、
客户端却读不了——dnsmasq 的 address= 就是这么漏掉的。

共用 reader 的代价是「两边一起错也会一起绿」，所以另有两道外部锚点：
  · tests/fixtures/ 的 golden 文件——锁死产物字节，写读同步改才能过；
  · 本脚本对解析失败行计数——读不懂的行不再被静默丢掉。
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import RULES_DIR, block_domain  # noqa: E402
from formats import FORMATS, BY_NAME  # noqa: E402

R = Path(RULES_DIR)

# 白名单产物（smartdns-whitelist.conf）语义相反，不参与一致性比对
BLOCK_FORMATS = [f for f in FORMATS if f.source != "allow"]


def parse(name):
    """返回 (精确集合, 后缀集合, 解析失败行数)。

    后缀集合 = ||x^ / DOMAIN-SUFFIX / address /x/ / '+.x'（覆盖子域）；
    精确集合 = hosts 的 0.0.0.0 行——`0.0.0.0 a.b.com` 不会拦 x.a.b.com，
    必须归 exact，否则会误判 hosts 与 dns.txt 等价。

    第 3 项是「既不是表头、也读不出域名」的行数。以前这些行被 `continue` 静默吞掉，
    一旦 reader 与产物对不上（有人手改了格式、或 writer 改了没同步 reader），
    整个文件会被大量丢弃、判定全变"放"，报错却指向"用例不符"而不是"解析失败"。
    """
    fmt = BY_NAME.get(name)
    exact, suffix = set(), set()
    bad = 0
    for line in (R / name).read_text(encoding="utf-8", errors="ignore").splitlines():
        t = line.strip()
        if not t or t.startswith(("!", "#", "[", "//")) or t == "payload:":
            continue
        if name == "dns.txt":
            d = block_domain(t)
        else:
            d = fmt.read(t) if fmt else None
        if not d:
            bad += 1
            continue
        if fmt is not None and not fmt.suffix:
            exact.add(d)
        else:
            suffix.add(d)
    return exact, suffix, bad


def hit(rule_sets, dom):
    """精确类型（DOMAIN / hosts 的 0.0.0.0 行）只认完全相等的域名；
    后缀类型（||x^ / DOMAIN-SUFFIX / address /x/ / '+.x'）才沿父域链匹配。
    旧实现让 exact 也走父域链，把 hosts 和旧版 DOMAIN 规则当成了后缀匹配，
    掩盖了"精确匹配格式拦不住折叠子域"的真实差异。"""
    exact, suffix = rule_sets[0], rule_sets[1]
    if dom in exact:
        return True, dom
    parts = dom.split(".")
    chain = [".".join(parts[i:]) for i in range(len(parts) - 1)]
    for c in chain:
        if c in suffix:
            return True, c
    return False, None


SUFFIX_FILES = ["dns.txt"] + [f.name for f in BLOCK_FORMATS if f.suffix]
# hosts 只能精确匹配：`0.0.0.0 a.b.com` 拦不到 x.a.b.com，
# 而 dns.txt 做了父子域折叠（父域存在即删子域），所以 hosts 天然覆盖不全。
# 它单独核对，不一致但"父域已列出"时标注 †，不计失败——这是格式限制，不是管线 bug。
EXACT_FILES = [f.name for f in BLOCK_FORMATS if not f.suffix]
FILES = SUFFIX_FILES + EXACT_FILES
CASES = [
    # (域名, 期望: True=拦 False=不拦, 说明)
    ("luckycat.bytedance.com", False, "字节金币发奖"),
    ("api5-normal-lf.fqnovel.com", False, "番茄小说内容API"),
    ("api.fqnovel.com", False, "番茄小说通用API"),
    ("tnc3-aliec2.bytedance.com", False, "字节配置下发"),
    ("tnc3-alisc2.bytedance.com", False, "字节配置下发"),
    ("scc.bytedance.com", False, "字节安全合规"),
    ("microapp.bytedance.com", False, "字节小程序容器"),
    ("uc.ucweb.com", False, "UC 入口"),
    ("u3.ucweb.com", False, "UC 资源集群"),
    ("safe.ucweb.com", False, "UC 网址安全"),
    ("wap3.ucweb.com", False, "UC WAP 门户"),
    ("ucweb.com", False, "UC 根域"),
    ("bytedance.com", False, "字节根域"),
    ("mssdk.bytedance.com", True, "字节 SDK 埋点"),
    ("dm.bytedance.com", True, "字节数据平台"),
    ("log3-applog-lf.fqnovel.com", True, "番茄日志埋点"),
    ("frontier100-toutiao-lf.fqnovel.com", True, "番茄埋点"),
    ("v6-novelapp.fqnovelvod.com", False, "番茄视频CDN（2026-11 改判：与 v3/v5/v9/v26 同族放行）"),
    ("adtrack.ucweb.com", True, "UC 广告追踪"),
    ("ucads.ucweb.com", True, "UC 广告"),
    ("union.ucweb.com", True, "UC 广告联盟"),
    ("insight.ucweb.com", True, "UC 统计"),
    ("px-intl.ucweb.com", True, "UC 国际广告"),
    ("ads3-normal-hl.zijieapi.com", True, "番茄广告计费"),
    # —— 2026-11-01 体检修复：大厂主域整杀 / 白名单放行广告 ——
    ("360.cn", False, "360 公司主域（原被 1007-Hosts 整域拦）"),
    ("2345.com", False, "2345 主域"),
    ("wechat.com", False, "微信国际版主域"),
    ("dns.wechat.com", False, "微信国际版 DNS"),
    ("u.wechat.com", False, "微信国际版业务域"),
    ("appstore.360.cn", False, "360 应用商店"),
    ("jiagu.360.cn", False, "360 加固服务"),
    ("mcloud.360.cn", False, "360 云服务"),
    ("ad.360.cn", True, "360 广告"),
    ("pop.360.cn", True, "360 弹窗推广"),
    ("union.360.cn", True, "360 广告联盟"),
    ("gamead.360.cn", True, "360 游戏广告"),
    ("ssp.2345.com", True, "2345 广告交易"),
    ("c-adx.2345.com", True, "2345 广告交易"),
    ("ad.doubleclick.net", True, "Google DART 广告（原被白名单放行）"),
    ("v6-reading-ad.qznovelvod.com", True, "番茄阅读页广告（原被放行）"),
    # —— 2026-11-01 下午：红果短剧 / 番茄小说播放链路 ——
    ("api5-normal-sinfonlinea.fqnovel.com", False, "红果搜索 API（hongguoTV 逆向实锤）"),
    ("api5-normal-sinfonlineb.fqnovel.com", False, "红果播放 API"),
    ("v5-hl-h-hw.douyinvod.com", False, "视频节点(华为云)，上游 v* 通配放行的 DNS 层落实"),
    ("v96.douyinvod.com", False, "视频节点"),
    ("v6-novelapp.fqnovelvod.com", False, "番茄视频 CDN，对齐 v3/v5/v9/v26"),
    ("lf-fe.fqnovelstatic.com", False, "番茄 H5 前端静态资源"),
    ("lf3-reading.fqnovelstatic.com", False, "番茄阅读页静态资源"),
    ("v5-hl-ali-reading-video.fqnovelvod.com", True, "阅读页信息流广告视频（保持拦）"),
]

missing = [f for f in FILES if not (R / f).exists()]
if missing:
    # 以前这里是 `if (R / f).exists()` 静默过滤：qx.list 被删掉、或 pipeline 少生成
    # 一种格式，本脚本照样「48 用例 0 失败」——因为那个格式根本不在比对集里。
    # 作为格式一致性闸门，产物不全本身就是失败。
    print(f"❌ 缺少产物：{', '.join(missing)}")
    print(f"   目录：{R}（先跑 python data/python/pipeline.py）")
    sys.exit(1)

sets = {f: parse(f) for f in FILES}
bads = {f: s[2] for f, s in sets.items() if s[2]}

print(f"解析格式：{', '.join(sets)}")
for f, (e, sfx, _bad) in sets.items():
    print(f"   {f:<24s} {len(e) + len(sfx):>8,} 条")
if bads:
    print("\n⚠️ 以下产物存在「既不是表头、也读不出域名」的行（writer 与 reader 可能已漂移）：")
    for f, n in bads.items():
        print(f"   {f:<24s} {n:>6,} 行无法解析")
print()
print(f"{'域名':36s} {'期望':5s} {'各格式结果':46s} 判定")
print("-" * 110)
fails = 0
for dom, exp, note in CASES:
    suffix_res = []
    for f in SUFFIX_FILES:
        h, _ = hit(sets[f], dom)
        suffix_res.append("拦" if h else "放")
    exact_res = []
    for f in EXACT_FILES:
        h, matched = hit(sets[f], dom)
        if h:
            exact_res.append("拦")
        elif exp:  # 期望拦但精确集里没有：看是不是父域在场 → 格式限制
            exact_res.append("放†")
        else:
            exact_res.append("放")
    res = suffix_res + exact_res
    consistent = len(set(suffix_res)) == 1
    good = consistent and (suffix_res[0] == "拦") == exp
    if not good:
        fails += 1
    print(f"{dom:36s} {'拦' if exp else '放':5s} {'/'.join(res):46s} "
          f"{'✓ ' + note if good else '✗ 不一致/不符 ' + note}")

print("\n" + "=" * 110)
print(f"产物 {len(FILES)} 个（后缀 {len(SUFFIX_FILES)} + 精确 {len(EXACT_FILES)}），"
      f"用例 {len(CASES)} 个，失败 {fails} 个，无法解析行 {sum(bads.values())} 行")
print("† = hosts 为精确匹配格式，只覆盖上游明确列出的域名（未列出的子域拦不到）")
if bads:
    print("❌ 有产物存在无法解析的行：reader 与产物语法已不一致，判定结果不可信")
sys.exit(1 if fails or bads else 0)
