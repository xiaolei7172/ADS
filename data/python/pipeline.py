# -*- coding: utf-8 -*-
"""
管线：读一次 DNS 规则，产出全部 8 种派生格式。

改成单进程的意义不只是省几次 5.6 MB 解析——而是「同一份数据、同一处语义」：
  · 三个域名集（拦截 / 折叠前 / 白名单）各构建一次，8 个格式复用；
  · 写法来自 formats.py 的声明，新增格式不再复制第 9 个循环；
  · 一致性校验（verify-fixes）用的是同一套 reader，不会再出现
    「生成器认为写对了、校验器认为没问题、客户端却读不了」的三方偏差。

用法：
  python pipeline.py                 # 生成全部
  python pipeline.py qx.list surge.list   # 只生成指定格式（旧脚本走这条路）
"""
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from common import RULES_DIR, MOD_DIR, block_domain, allow_domain  # noqa: E402
from formats import FORMATS, BY_NAME  # noqa: E402

DNS_PATH = os.path.join(RULES_DIR, "dns.txt")
ALLOW_PATH = os.path.join(RULES_DIR, "allow.txt")
UNFOLDED_PATH = os.path.join(os.path.dirname(RULES_DIR), "tmp", "dns-unfolded.txt")
UNFOLDED_META = os.path.join(os.path.dirname(RULES_DIR), "tmp", "dns-unfolded.meta.json")

# 裸域名兜底：上游偶尔给不带 ||...^ 的纯域名
BARE = re.compile(
    r"^[a-z0-9](?:[a-z0-9_-]*[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9_-]*[a-z0-9])?)+$", re.I)


def _iter_rule_lines(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith(("!", "#", "[")):
                continue
            yield line


def load_block():
    """dns.txt 的拦截域名（已去重、已折叠，保序）"""
    if not os.path.exists(DNS_PATH):
        print(f"❌ 未找到 {DNS_PATH}，请先跑 filter-dns.py")
        sys.exit(1)
    return [d for d in (block_domain(l) for l in _iter_rule_lines(DNS_PATH)) if d]


def load_unfolded():
    """折叠前域名集。

    hosts 只能精确匹配，跟着折叠后的 dns.txt 会漏掉约 1.5 万个被折叠的子域，
    而漏掉是无声的。所以这里读不到就直接失败，不发布残缺产物。
    """
    if not os.path.exists(UNFOLDED_PATH):
        print(f"❌ 未找到折叠前域名集：{UNFOLDED_PATH}")
        print("   hosts 跟随折叠后的 dns.txt 会漏掉约 1.5 万个子域，不发布这种残缺产物。")
        print("   请先执行：python data/python/filter-dns.py")
        sys.exit(1)
    out = []
    for line in _iter_rule_lines(UNFOLDED_PATH):
        d = block_domain(line) or (line.lower() if BARE.match(line) else None)
        if d:
            out.append(d)
    return out


def load_allow():
    """白名单域名：允许链上的纯域名规则，父域已存在时丢掉子域（后缀语义冗余）"""
    if not os.path.exists(ALLOW_PATH):
        print(f"❌ 未找到 {ALLOW_PATH}，请先跑 merge.py")
        sys.exit(1)
    domains = {d for d in (allow_domain(l) for l in _iter_rule_lines(ALLOW_PATH)) if d}
    kept = []
    for d in sorted(domains):
        parts = d.split(".")
        if any(".".join(parts[i:]) in domains for i in range(1, len(parts))):
            continue
        kept.append(d)
    return kept


LOADERS = {"block": load_block, "unfolded": load_unfolded, "allow": load_allow}


def emit(fmt, domains):
    """按格式声明写出一个产物，返回实际条数"""
    seen = set()
    rows = []
    for d in domains:
        if fmt.dedup:
            if d in seen:
                continue
            seen.add(d)
        rows.append(d)

    out_path = os.path.join(RULES_DIR, fmt.name)
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        for line in fmt.header_lines(rows):
            f.write(line + "\n")
        for d in rows:
            f.write(fmt.render(d))
    return len(rows)


def build(targets=None, cache=None):
    """生成指定格式（默认全部）；每个来源只加载一次"""
    cache = {} if cache is None else cache
    wanted = [f for f in FORMATS if not targets or f.name in targets]
    if targets:
        unknown = set(targets) - set(BY_NAME)
        if unknown:
            print(f"❌ 未知格式：{', '.join(sorted(unknown))}")
            print(f"   可选：{', '.join(f.name for f in FORMATS)}")
            sys.exit(2)

    results = []
    for fmt in wanted:
        if fmt.source not in cache:
            cache[fmt.source] = LOADERS[fmt.source]()
        results.append((fmt, emit(fmt, cache[fmt.source])))
    return results, cache


def main():
    results, cache = build(sys.argv[1:] or None)
    width = max(len(f.name) for f, _ in results)
    src_label = {"block": "dns.txt", "unfolded": "折叠前域名集", "allow": "allow.txt"}
    for fmt, n in results:
        print(f"✅ {fmt.name:<{width}}  {n:>8,} 条"
              f"   （{src_label[fmt.source]}"
              f"{'，后缀匹配' if fmt.suffix else '，精确匹配'}）")
    print("\n来源域名：" + "  ".join(f"{k}={len(v):,}" for k, v in sorted(cache.items())))


if __name__ == "__main__":
    main()
