#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
来源骤降熔断：某路上游「返半截」时中止发布，而不是把残缺规则发出去。

为什么需要
----------
现有防线管的是「源全挂」和「白名单投毒」：
- dl.py：失败源过半 → 中止
- merge.py：白名单移除比例 > 8% → 熔断
但**源拿到了、HTTP 200、只是内容腰斩**这件事没人管。

AdRules 一家占全量 49.7%（约 12 万条），它自己也是聚合源。上游脚本跑挂
时经常返回半截文件或只剩头部注释——HTTP 依然 200，dl.py 判成功，
merge.py 也看不出异常，于是 12 万条规则一夜蒸发，用户侧表现为
「广告突然全部拦不住了」，而且没有任何告警。

判定口径
--------
- 基线：最近 7 个有记录的日期里，该源原始规则数的**中位数**
  （用中位数不用均值：上游偶发的大幅波动不该抬高基线）
- 骤降：本次 < 中位数 × 50% **且** 绝对减少 > 500 条
  （双条件缺一不可：小源从 300 掉到 150 是正常波动，不告警；
   大源从 800 掉到 700 也不算骤降）
- 例外：dl_status.json 里标记下载失败的源不判骤降（那是「挂」不是「降」，
  由 dl.py 的失败过半闸门负责）

数据落在 data/stats/source-counts.json，按日期累积（保留 30 天）。
首次运行只建基线、不告警——没有历史就无法判断「降」。

用法
----
  python source-guard.py            # 检查并记录
  python source-guard.py --check    # 只检查，不写记录（预演）
  python source-guard.py --window 7 --drop 0.5
"""
import argparse
import datetime
import json
import os
import statistics
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from common import REPO_ROOT, TMP_DIR, count_valid_lines, beijing_now  # noqa: E402

STATS = os.path.join(REPO_ROOT, "data", "stats", "source-counts.json")
KEEP_DAYS = 30

# 源名写在 dl.py 注入的头部：`! 📋 规则来源：<name>`
PREFIX = "! 📋 规则来源："


def read_source_name(path):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for _ in range(6):
                line = f.readline()
                if not line:
                    break
                if line.startswith(PREFIX):
                    return line[len(PREFIX):].strip()
    except OSError:
        pass
    return None


def collect_today():
    """从 data/tmp 的下载产物统计各源原始规则数（去重前的真实条数）。"""
    counts = {}
    if not os.path.isdir(TMP_DIR):
        return counts
    for fname in sorted(os.listdir(TMP_DIR)):
        if not fname.endswith(".txt"):
            continue
        if not (fname.startswith("adblock_") or fname.startswith("allow_")):
            continue
        path = os.path.join(TMP_DIR, fname)
        name = read_source_name(path)
        if not name:
            continue
        n = count_valid_lines(path)
        counts[name] = counts.get(name, 0) + n
    return counts


def load_failed():
    """dl.py 记下的下载失败源：这些源不参与骤降判定。"""
    path = os.path.join(TMP_DIR, "dl_status.json")
    if not os.path.exists(path):
        return set()
    try:
        with open(path, "r", encoding="utf-8") as f:
            return {d["name"] for d in json.load(f) if not d.get("ok")}
    except (OSError, ValueError, KeyError, TypeError):
        return set()


def load_history():
    if not os.path.exists(STATS):
        return {}
    try:
        with open(STATS, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_history(history, today, counts):
    history[today] = counts
    # 只留最近 KEEP_DAYS 天（按日期字符串排序即可，格式是 ISO）
    for old in sorted(history)[:-KEEP_DAYS]:
        history.pop(old, None)
    os.makedirs(os.path.dirname(STATS), exist_ok=True)
    with open(STATS, "w", encoding="utf-8", newline="\n") as f:
        json.dump(history, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")


def median_baseline(history, today, window):
    """每个源在最近 window 个历史日期里的中位数。"""
    dates = [d for d in sorted(history) if d < today][-window:]
    per_source = {}
    for name in {n for d in dates for n in history[d]}:
        vals = [history[d][name] for d in dates if name in history[d]]
        if vals:
            per_source[name] = statistics.median(vals)
    return per_source, dates


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--window", type=int, default=7)
    ap.add_argument("--drop", type=float, default=0.5, help="低于基线的比例阈值")
    ap.add_argument("--min-abs", type=int, default=500, help="绝对减少量下限（小源免疫）")
    ap.add_argument("--total-drop", type=float, default=0.6, help="总量低于基线的比例阈值")
    ap.add_argument("--check", action="store_true", help="只检查，不写记录")
    args = ap.parse_args()

    today = datetime.date.today().isoformat()
    counts = collect_today()
    if not counts:
        print("⚠️ data/tmp 下没有下载产物，跳过来源体检（先跑 dl.py）")
        return 0

    failed = load_failed()
    history = load_history()
    baseline, dates = median_baseline(history, today, args.window)

    total = sum(counts.values())
    print(f"📡 来源体检  {beijing_now()}")
    print(f"   本次 {len(counts)} 个源 / {total:,} 条；基线窗口 {len(dates)} 天"
          + (f"（{dates[0]} ~ {dates[-1]}）" if dates else "（无历史，本次建立基线）"))

    alerts = []
    if baseline:
        print(f"\n{'来源':<28}{'本次':>9}{'基线':>9}{'变化':>10}")
        print("-" * 58)
        for name, c in sorted(counts.items(), key=lambda x: -x[1]):
            base = baseline.get(name)
            if base is None:
                print(f"{name:<28}{c:>9,}{'—':>9}{'新源':>10}")
                continue
            delta = c - base
            pct = delta / base if base else 0
            flag = ""
            if name in failed:
                flag = "  ❌ 下载失败（不判骤降）"
            elif base >= 1000 and c < base * args.drop and (base - c) > args.min_abs:
                flag = "  🚨 骤降"
                alerts.append((name, c, base, delta, pct))
            print(f"{name:<28}{c:>9,}{base:>9,.0f}{delta:>+10,.0f} ({pct:+.0%}){flag}")

        # 曾经有、这次整份消失的源（未标记失败 = 异常）
        gone = [n for n in baseline if n not in counts and n not in failed]
        if gone:
            print("\n⚠️ 本次未出现（且未标记下载失败）：")
            for n in sorted(gone):
                print(f"   {n}（基线 {baseline[n]:,.0f} 条）")
                alerts.append((n, 0, baseline[n], -baseline[n], -1.0))

        # 总量熔断：单源未触发但整体腰斩（多个源同时半截）
        total_base = sum(baseline.get(n, 0) for n in counts) or sum(baseline.values())
        if total_base and total < total_base * args.total_drop:
            print(f"\n🚨 总量骤降：{total:,} vs 基线 {total_base:,.0f}（{total/total_base:.0%}）")
            alerts.append(("（总量）", total, total_base, total - total_base, total / total_base - 1))

    if not args.check:
        save_history(history, today, counts)
        print(f"\n💾 已记录到 data/stats/source-counts.json（保留 {KEEP_DAYS} 天）")

    if alerts:
        print("\n" + "=" * 58)
        print("🚫 来源骤降熔断：以下源本次返回的规则数远低于基线")
        for name, c, base, delta, pct in alerts:
            print(f"   {name}：{c:,} ← 基线 {base:,.0f}（{pct:+.0%}，{delta:+,.0f} 条）")
        print("\n   典型原因：上游脚本跑挂返回半截、仓库被重置、换分支后文件还在但内容清空。")
        print("   处置：确认上游状态后重跑；若是上游真下线，从 dl.py 移除该源再发布。")
        print("   ⛔ 本次不发布（宁可规则停一天，也不发残缺规则）。")
        return 1

    print("\n✅ 来源体检通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
