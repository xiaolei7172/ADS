#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证 10 种格式对同一域名的判定是否一致（格式感知解析 + 父子域语义）"""
import re, sys
from pathlib import Path

R = Path("data/rules")


def parse(path):
    """返回 (精确集合, 后缀集合)。后缀集合 = DOMAIN-SUFFIX / ||x^ / hosts 视为覆盖子域"""
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
            suffix.add(m.group(1).rstrip("."))
            continue
        m = re.match(r"^-\s*['\"]?\+?\.?([a-z0-9._*-]+)", low)  # mihomo yaml: - '+.domain'
        if m:
            suffix.add(m.group(1).rstrip(".").strip("'\""))
            continue
        if " " not in low and "." in low and re.fullmatch(r"[a-z0-9._*-]+", low):
            suffix.add(low.rstrip("."))
    return exact, suffix


def hit(rule_sets, dom):
    exact, suffix = rule_sets
    parts = dom.split(".")
    chain = [".".join(parts[i:]) for i in range(len(parts) - 1)] + [dom]
    for c in chain:
        if c in exact:
            return True, c
    for c in chain:
        if c in suffix:
            return True, c
    return False, None


FILES = ["dns.txt", "hosts.txt", "qx.list", "surge.list", "smartdns.conf", "mihomo.yaml"]
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
    ("v6-novelapp.fqnovelvod.com", True, "番茄视频广告"),
    ("adtrack.ucweb.com", True, "UC 广告追踪"),
    ("ucads.ucweb.com", True, "UC 广告"),
    ("union.ucweb.com", True, "UC 广告联盟"),
    ("insight.ucweb.com", True, "UC 统计"),
    ("px-intl.ucweb.com", True, "UC 国际广告"),
    ("ads3-normal-hl.zijieapi.com", True, "番茄广告计费"),
]

sets = {f: parse(R / f) for f in FILES if (R / f).exists()}
print(f"解析格式：{', '.join(sets)}\n")
print(f"{'域名':36s} {'期望':5s} {'各格式结果':46s} 判定")
print("-" * 110)
fails = 0
for dom, exp, note in CASES:
    res = []
    for f, s in sets.items():
        h, _ = hit(s, dom)
        res.append("拦" if h else "放")
    consistent = len(set(res)) == 1
    good = consistent and (res[0] == "拦") == exp
    if not good:
        fails += 1
    print(f"{dom:36s} {'拦' if exp else '放':5s} {'/'.join(res):46s} "
          f"{'✓ ' + note if good else '✗ 不一致/不符 ' + note}")

print("\n" + "=" * 110)
print(f"用例 {len(CASES)} 个，失败 {fails} 个")
sys.exit(1 if fails else 0)
