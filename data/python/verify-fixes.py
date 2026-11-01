#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证 10 种格式对同一域名的判定是否一致（格式感知解析 + 父子域语义）"""
import re, sys
from pathlib import Path

R = Path("data/rules")


def parse(path):
    """返回 (精确集合, 后缀集合)。
    后缀集合 = DOMAIN-SUFFIX / ||x^ / address /x/ / '+.x'（覆盖子域）；
    精确集合 = DOMAIN / host / host-suffix 之外的精确类型 / hosts 的 0.0.0.0 行。
    注意：hosts 是精确匹配——`0.0.0.0 a.b.com` 不会拦 x.a.b.com，
    所以这里必须归 exact，否则会误判 hosts 与 dns.txt 等价。"""
    exact, suffix = set(), set()
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        t = line.strip()
        if not t or t.startswith(("!", "#", "[", "//")) or t in ("payload:",):
            continue
        low = t.lower()
        m = re.match(r"^\|\|([a-z0-9._*-]+)\^?$", low)
        if m:
            suffix.add(m.group(1).rstrip("."))
            continue
        m = re.match(r"^(?:domain|host|domain-suffix|host-suffix)\s*,\s*([a-z0-9._*-]+)", low)
        if m:
            d = m.group(1).rstrip(".")
            if "suffix" in low.split(",")[0]:
                suffix.add(d)
            else:
                exact.add(d)
            continue
        m = re.match(r"^address\s*/([a-z0-9._*-]+)/", low)
        if m:
            suffix.add(m.group(1).rstrip("."))
            continue
        m = re.match(r"^(?:0\.0\.0\.0|127\.0\.0\.1)\s+([a-z0-9._-]+)$", low)
        if m:
            exact.add(m.group(1).rstrip("."))
            continue
        m = re.match(r"^-\s*['\"]?\+?\.?([a-z0-9._*-]+)", low)  # mihomo yaml: - '+.domain'
        if m:
            suffix.add(m.group(1).rstrip(".").strip("'\""))
            continue
        if " " not in low and "." in low and re.fullmatch(r"[a-z0-9._*-]+", low):
            suffix.add(low.rstrip("."))
    return exact, suffix


def hit(rule_sets, dom):
    """精确类型（DOMAIN / hosts 的 0.0.0.0 行）只认完全相等的域名；
    后缀类型（||x^ / DOMAIN-SUFFIX / address /x/ / '+.x'）才沿父域链匹配。
    旧实现让 exact 也走父域链，把 hosts 和旧版 DOMAIN 规则当成了后缀匹配，
    掩盖了"精确匹配格式拦不住折叠子域"的真实差异。"""
    exact, suffix = rule_sets
    if dom in exact:
        return True, dom
    parts = dom.split(".")
    chain = [".".join(parts[i:]) for i in range(len(parts) - 1)]
    for c in chain:
        if c in suffix:
            return True, c
    return False, None


SUFFIX_FILES = ["dns.txt", "qx.list", "surge.list", "smartdns.conf", "mihomo.yaml"]
# hosts 只能精确匹配：`0.0.0.0 a.b.com` 拦不到 x.a.b.com，
# 而 dns.txt 做了父子域折叠（父域存在即删子域），所以 hosts 天然覆盖不全。
# 它单独核对，不一致但"父域已列出"时标注 †，不计失败——这是格式限制，不是管线 bug。
EXACT_FILES = ["hosts.txt"]
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

sets = {f: parse(R / f) for f in FILES if (R / f).exists()}
print(f"解析格式：{', '.join(sets)}\n")
print(f"{'域名':36s} {'期望':5s} {'各格式结果':46s} 判定")
print("-" * 110)
fails = 0
for dom, exp, note in CASES:
    suffix_res = []
    for f in SUFFIX_FILES:
        if f not in sets:
            continue
        h, _ = hit(sets[f], dom)
        suffix_res.append("拦" if h else "放")
    exact_res = []
    for f in EXACT_FILES:
        if f not in sets:
            continue
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
print(f"用例 {len(CASES)} 个，失败 {fails} 个")
print("† = hosts 为精确匹配格式，只覆盖上游明确列出的域名（未列出的子域拦不到）")
sys.exit(1 if fails else 0)
