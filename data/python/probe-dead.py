#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
死规则探测：把「域名已不存在」的拦截规则识别出来，生成 data/mod/dead.txt。

为什么需要
----------
上游规则只增不减。实测随机抽样：约 11% 的拦截域名已是 NXDOMAIN——
一次性垃圾域（uujhveglpo.xyz 这类随机串）、活动结束后下线的推广域、
换过品牌的旧域。它们占着规则行数、拖慢客户端匹配、让「今天拦明天不拦」
的抖振更难排查。管线原来只探测「源是否可达」（probe_source.py），
从不探测「单条域名是否还活着」。

判定口径（这是本脚本最关键的部分）
----------------------------------
只认 **RCODE=3（NXDOMAIN）**，且必须**两台不同 DNS 服务器都返回 3**。

踩过的坑，别再走回去：
1. `socket.getaddrinfo` 抛 11001（WSAHOST_NOT_FOUND）**不等于域名不存在**。
   实测 analytics.tdameritrade.com 本地判死，但三家 DoH 全部 Status=0
   （NOERROR / 无 A 记录，域名存在但没配 A）。误判率实测约 1/3。
2. DoH 走 HTTPS，单条要建 TLS 连接，被服务端限流死在 ~32 条/秒，
   24 万条要 2 小时，加线程完全无效（限流是服务端的，不是客户端的）。
3. 原生 UDP 直连公共 DNS：无握手、单包往返，短时能到 380 条/秒。
   但**必须限速**：裸跑十几分钟后公共解析器开始丢包，实测 24.6 万条
   跑完错误率 63.9%（15.7 万条超时），整轮作废。限到 150 条/秒
   （两台各 75）实测错误率 <1%，全量约 33 分钟。后扩到 4 台独立运营商
   （阿里/腾讯/114/百度），单台速率不变、聚合翻倍，全量约 20 分钟。

所以：UDP 主探测（限速）+ 换服务器复核。复核用**另一台**服务器，
避免「某台 DNS 抽风把整个 TLD 返回 NXDOMAIN」造成批量误删。

安全阀（任一触发都不写盘，exit 1）
----------------------------------
- 网络错误率 > 15%：链路有问题，判死结果不可信
- 死规则占比 > 40%：不合常理，多半是 DNS 被劫持或服务器异常
- 探测域名数 < 1000：输入异常

复活机制
--------
每次运行都会把旧 dead.txt 里的域名**一并重探**：
上次判死、这次能解析 → 从 dead.txt 移除（广告域复活很常见，
上游换 CDN 重新启用）。所以 dead.txt 永远是「截至本次探测的死域全集」，
不需要人工清理。

增量模式（--incremental）
--------------------------
全量 22 万+ 条每周重探一遍，探测时间全花在「上周就验过是活的」域上。
增量模式引入快照文件（--snapshot，随 dead.txt 一起提交进仓库），
每周只探三类：
  1. **新增域**：当前产物 - 上周快照 → 全量探测（增量模式的主战场）
  2. **抽样复核**：上上周验过活着的域，按域名哈希稳定抽 --recheck-ratio
     （默认 10%）重验——稳定哈希保证中断续传时抽的是同一批；
     每个活域平均 ≤10 周被轮到一次，新死域最迟 10 周内被清出
  3. **旧死域全集**：dead.txt 全部重验（复活机制不受增量模式影响）
预计运行时间从 35 分钟压到 10 分钟以内。
首次以增量模式运行时快照不存在 → 自动退化为全量探测并生成快照。

用法
----
  python probe-dead.py                 # 全量探测，写 data/mod/dead.txt
  python probe-dead.py --incremental   # 增量探测（每周例行用这个）
  python probe-dead.py --limit 5000    # 只测前 5000 条（调试）
  python probe-dead.py --dry-run       # 只打印统计，不写盘
  python probe-dead.py --workers 192   # 调并发（默认 128）
"""
import argparse
import hashlib
import json
import os
import random
import re
import socket
import struct
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from common import RULES_DIR, MOD_DIR, TMP_DIR, beijing_now, block_domain, hosts_target  # noqa: E402

SOURCE = os.path.join(RULES_DIR, "dns.txt")
OUT = os.path.join(MOD_DIR, "dead.txt")

# 两台独立公共 DNS：223.5.5.5（阿里）与 119.29.29.29（腾讯）。
# 主探测在两台之间轮换（每域一台），复核换另一台——单台抽风不会造成批量判死。
# ⚠️ 曾试过扩到 4 台（+114/百度）提聚合吞吐：本机（境内）4 台全绿，
# 但 CI 出口在境外，到 114/百度延迟 300ms+ 且大量丢包，复核吞吐崩到
# 50-80 条/秒，run 撞 100 分钟上限被取消（run#2, 2026-11-10）。
# 阿里/腾讯是 anycast，境外也快——公共 DNS 探测必须选境外可达的 anycast 端点。
SERVERS = ["223.5.5.5", "119.29.29.29"]

RCODE_NXDOMAIN = 3
RCODE_NOERROR = 0


# ----------------------------------------
# DNS 报文：只构查询、只读 RCODE
# 不需要解析 Answer（可能含压缩指针，逻辑多且易错）；
# 判死只看响应第 4 字节低 4 位，够用。
# ----------------------------------------
def build_query(qname, qid):
    pkt = struct.pack(">HHHHHH", qid, 0x0100, 1, 0, 0, 0)  # RD=1
    for label in qname.split("."):
        raw = label.encode("idna") if any(ord(c) > 127 for c in label) else label.encode("ascii", "ignore")
        if not raw or len(raw) > 63:
            return None
        pkt += bytes([len(raw)]) + raw
    return pkt + b"\x00" + struct.pack(">HH", 1, 1)  # QTYPE=A, QCLASS=IN


class RateLimiter:
    """全局令牌桶：把总请求速率钉在 qps。

    为什么必须有它：160 线程裸跑，短测能到 380 条/秒看起来很爽，
    但持续十几分钟后公共 DNS 开始限流——实测 24.6 万条跑完，
    错误率 63.9%（15.7 万条超时），整个探测白跑。
    公共解析器对单 IP 的 QPS 有阈值，探得越快越不准。
    限到低 QPS（单台 50~75 条/秒）实测稳定；加台数提聚合吞吐，不提单台速率。
    """

    def __init__(self, qps):
        self.interval = 1.0 / qps if qps and qps > 0 else 0.0
        self.next_time = time.monotonic()
        self.lock = threading.Lock()

    def acquire(self):
        if not self.interval:
            return
        with self.lock:
            now = time.monotonic()
            slot = max(self.next_time, now)
            self.next_time = slot + self.interval
            wait = slot - now
        if wait > 0:
            time.sleep(wait)  # 在锁外睡，否则所有线程被串行化

    def pause(self, seconds):
        """全体暂停：把发放时间整体推后 seconds。

        复盘数据：150 条/秒裸跑，前 6000 条错误率 0.7%，跑满 24.6 万条
        后整体错误率 25.8%——公共解析器的限制不是瞬时 QPS，而是持续
        压力下的配额。每 3 万条歇 15 秒，让配额回血，比降速更划算。
        """
        with self.lock:
            self.next_time = max(self.next_time, time.monotonic()) + seconds



def query_rcode(sock, server, qname, qid, timeout):
    pkt = build_query(qname, qid)
    if pkt is None:
        return None
    sock.settimeout(timeout)
    sock.sendto(pkt, (server, 53))
    data, _ = sock.recvfrom(512)
    # ID 必须回显匹配，否则是串包（高并发 UDP 下真实存在）
    if len(data) < 4 or struct.unpack(">H", data[:2])[0] != qid:
        return None
    return data[3] & 0x0F


def probe_batch(items, timeout, retries, counter, lock, limiter):
    """一个线程处理一批 (域名, 服务器) 组合，逐条 yield (域名, 服务器, rcode)。

    socket 每 500 条重建一次：长时间复用同一个 UDP socket，中间设备的
    NAT 表项会老化，之后所有包都被丢弃（表现为「前面很快、后面全超时」）。
    """
    sock = None
    try:
        for i, (dom, server) in enumerate(items):
            if sock is None or i % 500 == 0:
                if sock:
                    sock.close()
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            rcode = None
            for _ in range(retries):
                limiter.acquire()
                try:
                    rcode = query_rcode(sock, server, dom, random.randint(0, 0xFFFF), timeout)
                    if rcode is not None:
                        break
                except socket.timeout:
                    continue
                except OSError:
                    continue
            with lock:
                counter["total"] += 1
                if rcode is None:
                    counter["err"] += 1
                elif rcode == RCODE_NXDOMAIN:
                    counter["nx"] += 1
                else:
                    counter["ok"] += 1
            yield dom, server, rcode
    finally:
        if sock:
            sock.close()


def save_state(path, result):
    """原子落盘探测进度：写 .tmp 再 rename，中途被 kill 不会留下半个 JSON。"""
    if not path:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(result, f)
    os.replace(tmp, path)


def save_flat_state(path, first):
    """把主探测结果 {域: {服务器: rcode}} 压扁成续传格式 {域: rcode} 再落盘。

    续传只复用「有明确结果」的域（rcode 非 None），扁平格式即可表达；
    当时用了哪台服务器不需要记——续传域复核时对全部服务器复测，口径只紧不松。
    """
    flat = {}
    for d, srvs in first.items():
        for rc in srvs.values():
            if rc is not None:
                flat[d] = rc
                break
    save_state(path, flat)


def load_state(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def run_parallel(items, workers, timeout, retries, label, qps,
                 result=None, state_path=None, batch=30000, cooldown=15):
    """并发探测 items=[(域名, 服务器), ...]，返回 {域名: {服务器: rcode|None}}。

    result 传入非空字典即「续传」：已有结果直接复用，只补缺失的 (域, 服务器) 组合。
    每 batch 条落盘一次并把全体暂停 cooldown 秒——持续打压会被限流，
    而中断一次丢掉几十分钟的探测结果，比重试更贵。
    state_path 只在「每域一台服务器」的主探测场景使用，落盘格式为扁平 {域: rcode}。
    """
    result = result if result is not None else {}
    counter = {"total": 0, "nx": 0, "ok": 0, "err": 0}
    lock = threading.Lock()
    limiter = RateLimiter(qps)
    chunks = [items[i::workers] for i in range(workers)]
    started = time.time()
    last_saved = [sum(1 for v in result.values() if v)]

    def save_flat():
        """主探测续传格式：{域: rcode}（每域只有一条结果时才成立）。"""
        flat = {}
        for d, srvs in result.items():
            for rc in srvs.values():
                if rc is not None:
                    flat[d] = rc
                    break
        save_state(state_path, flat)

    def wrapped(chunk):
        for dom, server, rcode in probe_batch(chunk, timeout, retries, counter, lock, limiter):
            with lock:
                result.setdefault(dom, {})[server] = rcode
                done = sum(1 for v in result.values() if v)
                must_save = state_path and done - last_saved[0] >= batch
                if must_save:
                    last_saved[0] = done
                    save_flat()
            if done % 5000 == 0:
                rate = done / max(time.time() - started, 1e-6)
                print(f"   … {label} {done}/{len(items)}  ({rate:.0f} 条/秒)", flush=True)
            if must_save:
                limiter.pause(cooldown)
                print(f"   ⏸️ 已落盘 {done:,} 条，冷却 {cooldown}s（缓解公共 DNS 配额压力）",
                      flush=True)

    threads = [threading.Thread(target=wrapped, args=(c,), daemon=True) for c in chunks if c]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return result, counter


def load_domains(path):
    """从拦截产物里抽取全部域名：||domain^ 与 hosts 行都收。"""
    doms = set()
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith(("!", "#", "[", "@@")):
                continue
            d = block_domain(s) or hosts_target(s)
            if d:
                doms.add(d)
    return doms


def load_old_dead(path):
    doms = set()
    if not os.path.exists(path):
        return doms
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            s = line.strip()
            if s and not s.startswith(("!", "#")):
                doms.add(s.lower())
    return doms


def load_snapshot(path):
    """读上次探测时的产物快照（纯域名列表，可带注释头）。缺失返回 None。"""
    if not os.path.exists(path):
        return None
    doms = set()
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            s = line.strip().lower()
            if s and not s.startswith(("!", "#")):
                doms.add(s)
    return doms


def stable_sample(doms, ratio):
    """按域名 MD5 哈希稳定抽样。

    为什么不用 random.sample：抽样结果必须跨次运行一致——
    探测中断续传时 targets 要重算，哈希桶保证两次抽的是同一批域，
    已落盘的进度不会作废（random.sample 每次换种子会抽到不同子集）。
    """
    threshold = round(ratio * 10000)
    return {d for d in doms
            if int(hashlib.md5(d.encode()).hexdigest()[:8], 16) % 10000 < threshold}


def save_snapshot(path, doms):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    header = [
        "! ==============================================",
        "! 📸 死规则探测快照（上次探测时的拦截域全集）",
        f"! 🕒 生成时间：{beijing_now()}（北京时间）",
        "! 📌 用途：probe-dead.py --incremental 用它算「新增域」，",
        "!         并对存量域做哈希稳定抽样复核。随 dead.txt 一起提交。",
        "! ⚠️ 本文件由脚本自动生成，手动编辑会在下次探测时被覆盖。",
        "! ==============================================",
        "",
    ]
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(header) + "\n".join(sorted(doms)) + "\n")
    os.replace(tmp, path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default=SOURCE)
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--workers", type=int, default=64)
    ap.add_argument("--qps", type=int, default=100, help="总请求速率上限（条/秒），0=不限速")
    ap.add_argument("--limit", type=int, default=0, help="只测前 N 条（0=全量）")
    ap.add_argument("--timeout", type=float, default=3.0)
    ap.add_argument("--retries", type=int, default=2)
    ap.add_argument("--max-nx-ratio", type=float, default=0.40)
    # 未判定（超时/SERVFAIL）不判死，只降低清理覆盖率，所以容忍度可以放宽到 30%。
    # 公共 DNS 的配额在长时间打压下会收紧，一轮跑不完是常态——配合续传即可。
    ap.add_argument("--max-err-ratio", type=float, default=0.30)
    ap.add_argument("--state", default=os.path.join(TMP_DIR, "probe-state.json"),
                    help="断点续传文件（默认 data/tmp/probe-state.json）")
    ap.add_argument("--reset", action="store_true", help="丢弃上次进度，从零开始")
    ap.add_argument("--batch", type=int, default=30000, help="每 N 条落盘并冷却一次")
    ap.add_argument("--cooldown", type=int, default=15, help="每批之间暂停秒数")
    ap.add_argument("--incremental", action="store_true",
                    help="增量模式：只探新增域 + 哈希抽样复核存量 + 旧死域全集复验")
    ap.add_argument("--snapshot", default=os.path.join(MOD_DIR, "probe-snapshot.txt"),
                    help="增量模式快照文件（默认 data/mod/probe-snapshot.txt）")
    ap.add_argument("--recheck-ratio", type=float, default=0.10,
                    help="增量模式对存量活域的抽样复核比例（默认 0.10）")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    print(f"🔍 死规则探测  {beijing_now()}  {'（增量模式）' if args.incremental else '（全量模式）'}")

    if not os.path.exists(args.source):
        print(f"❌ 找不到 {args.source}，先跑 merge.py + filter-dns.py")
        sys.exit(1)

    live = load_domains(args.source)
    old_dead = load_old_dead(args.out)
    print(f"📥 当前拦截域 {len(live):,} 条；上次 dead.txt {len(old_dead):,} 条（一并复验，防复活）")

    if args.incremental:
        snap = load_snapshot(args.snapshot)
        if snap is None:
            print("📸 快照不存在，本轮自动退化为全量探测，结束后生成快照")
            targets = sorted(live | old_dead)
            probed_live = set(live)
        else:
            new_doms = live - snap
            common = live & snap
            sampled = stable_sample(common, args.recheck_ratio)
            probed_live = new_doms | sampled
            targets = sorted(probed_live | old_dead)
            print(f"📸 增量口径：新增 {len(new_doms):,} + 存量抽样 "
                  f"{len(sampled):,}/{len(common):,}（{args.recheck_ratio:.0%}，哈希稳定）"
                  f" + 旧死域复验 {len(old_dead):,}")
    else:
        targets = sorted(live | old_dead)
        probed_live = set(live)

    if args.limit:
        targets = targets[:args.limit]
        probed_live &= set(targets)
    if len(targets) < 1000 and not args.limit:
        print(f"🚫 待探测域名仅 {len(targets)} 条，输入异常，中止（不写盘）")
        sys.exit(1)

    # 断点续传：只复用「有明确结果」的域。上一轮超时（None）的这次重测——
    # 每轮配额有限，跑完一轮必然剩一批没测出来的，重跑同一命令即可补齐。
    if args.reset and args.state and os.path.exists(args.state):
        os.remove(args.state)
        print("🧹 已清除上次进度（--reset）")
    prior = load_state(args.state) if args.state else {}
    target_set = set(targets)
    prior = {d: rc for d, rc in prior.items() if rc is not None and d in target_set}
    todo = [d for d in targets if d not in prior]
    if prior:
        print(f"♻️ 续传：已有 {len(prior):,} 条明确结果，本次补测 {len(todo):,} 条"
              f"（含上轮超时的 {len([d for d in targets if d not in prior]):,} 条）")

    # 主探测结果统一为 {域: {服务器: rcode}}；续传的旧格式（{域: rcode}）
    # 没有「当时用了哪台服务器」的信息，占位 None——复核时对这类域全服务器复测。
    first = {d: {None: rc} for d, rc in prior.items()}
    if todo:
        items = [(d, SERVERS[i % len(SERVERS)]) for i, d in enumerate(todo)]
        print(f"🚀 主探测（UDP 直连 {', '.join(SERVERS)}，{args.workers} 线程，"
              f"限速 {args.qps or '不限'} 条/秒，预计 {len(items) / max(args.qps or 333, 1) / 60:.0f} 分钟）")
        t0 = time.time()
        first, c1 = run_parallel(items, args.workers, args.timeout, args.retries,
                                 "主探测", args.qps, result=first, state_path=args.state,
                                 batch=args.batch, cooldown=args.cooldown)
        print(f"   主探测完成：{c1['total']:,} 条 / {time.time() - t0:.0f}s  "
              f"NX={c1['nx']:,} OK={c1['ok']:,} ERR={c1['err']:,}")
    else:
        print("✅ 全部域名都已有明确结果，跳过主探测")
        c1 = {"total": 0, "nx": 0, "ok": 0, "err": 0}

    err_ratio = c1["err"] / max(c1["total"], 1)
    if err_ratio > args.max_err_ratio:
        # 先落盘再退出：这一轮的成果下次可直接续传，不必从零重跑
        save_flat_state(args.state, first)
        print(f"🚫 本轮网络错误率 {err_ratio:.1%} > {args.max_err_ratio:.0%}"
              f"（{c1['err']:,}/{c1['total']:,} 条未判定），超出本次容忍上限，不写 dead.txt。")
        print(f"   已完成的 {sum(1 for v in first.values() if any(rc is not None for rc in v.values())):,} "
              f"条结果已落盘，直接重跑同一命令即可续传（超时域会自动重测）。")
        print(f"   未判定不等于判死：这些域不会被删除，只是这轮没测出来。")
        sys.exit(1)

    # 复核：NX 候选换到「主探测没用过的其余服务器」再查，
    # 全部应答服务器都返回 NXDOMAIN 才判死（单台抽风不会造成批量误删）。
    candidates = sorted(d for d, srvs in first.items()
                        if any(rc == RCODE_NXDOMAIN for rc in srvs.values()))
    confirm_items = []
    for d in candidates:
        used = set(first[d])
        for s in SERVERS:
            if s not in used:
                confirm_items.append((d, s))
    print(f"\n🔁 复核 {len(candidates):,} 条 NXDOMAIN 候选"
          f"（{len(confirm_items):,} 条查询，其余 {len(SERVERS)}-1 台服务器逐台确认）")
    second, c2 = run_parallel(confirm_items, args.workers, args.timeout, args.retries,
                              "复核", args.qps)
    confirmed = []
    disputed = 0
    for d in candidates:
        srvs = second.get(d, {})
        expected = len(SERVERS) - len(set(first[d]) & set(SERVERS))
        answered = [rc for rc in srvs.values()]
        if len(answered) == expected and all(rc == RCODE_NXDOMAIN for rc in answered):
            confirmed.append(d)
        else:
            disputed += 1

    dead_in_live = [d for d in confirmed if d in probed_live]
    revived = sorted(old_dead - set(confirmed))
    # 增量模式下占比只对「本轮实际探测过的活域」计算——
    # 未抽到的存量域没探过，把它们放进分母会把占比稀释得失真。
    nx_ratio = len(dead_in_live) / max(len(probed_live), 1)

    print(f"\n📊 结果")
    print(f"   确认死域（全部应答服务器 NXDOMAIN）：{len(confirmed):,} 条，"
          f"占本轮探测活域 {nx_ratio:.1%}"
          + ("" if args.incremental else f"（占当前拦截域 {nx_ratio:.1%}）"))
    print(f"   各台结果不一致/未答全（保守保留，不判死）：{disputed:,} 条")
    print(f"   本期复活（上次判死、本次可解析）：{len(revived):,} 条")
    print(f"   dead.txt 将记录 {len(confirmed):,} 条"
          f"（其中 {len(set(confirmed) - live):,} 条已不在当前产物，保留用于持续跟踪）")

    if nx_ratio > args.max_nx_ratio:
        print(f"🚫 死域占比 {nx_ratio:.1%} > {args.max_nx_ratio:.0%}，不合常理"
              f"（多半是 DNS 被劫持或服务器异常），中止（不写盘）")
        sys.exit(1)

    if args.dry_run:
        print("\n🧪 --dry-run：不写盘")
        return

    header = [
        "! ==============================================",
        "! ☠️ 死规则清单（NXDOMAIN 确认）",
        f"! 🕒 生成时间：{beijing_now()}（北京时间）",
        ("! 🔬 探测方式：UDP 直连 " + " / ".join(SERVERS)
         + f"，两台均返回 RCODE=3 才判定"),
        ("! 🧭 探测口径：" + ("增量（新增域全探 + 存量哈希抽样 {}% + 旧死域复验）"
                            .format(round(args.recheck_ratio * 100))
                            if args.incremental else "全量")),
        f"! 📊 本轮探测 {len(targets):,} 条 → 确认死域 {len(confirmed):,} 条"
        f"（占本轮探测活域 {nx_ratio:.1%}）；结果不一致 {disputed:,} 条（保留）",
        f"! ♻️ 本期复活 {len(revived):,} 条（已从本清单移除，规则恢复拦截）",
        "! 📌 用途：merge.py 读取本文件，命中域名的**上游**拦截规则不再写入产物；",
        "!         本地自定义规则（data/mod/adblock.txt）豁免，用户明确要拦的照拦。",
        "! 🔁 重新生成：python data/python/probe-dead.py",
        "! ⚠️ 本文件由脚本自动生成，手动编辑会在下次探测时被覆盖。",
        "! ==============================================",
        "",
    ]
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(header) + "\n".join(confirmed) + "\n")

    def _pretty(path):
        """展示用相对路径；跨盘符（如 C: 输出、D: 脚本）时 relpath 会抛
        ValueError，退回绝对路径——本地调试常用场景，不能让收尾打印崩掉。"""
        try:
            return os.path.relpath(path, os.path.dirname(SCRIPT_DIR))
        except ValueError:
            return path

    print(f"\n✅ 已写入 {_pretty(args.out)}"
          f"（{len(confirmed):,} 条）")
    if revived:
        print(f"   ♻️ {len(revived):,} 条复活域名已恢复拦截")
    # 快照在 dead.txt 写成功后更新：两者必须同代，否则下轮「新增域」会算错
    if args.incremental:
        save_snapshot(args.snapshot, live)
        print(f"   📸 快照已更新 {_pretty(args.snapshot)}"
              f"（{len(live):,} 条）")
    # 写盘成功即代表本轮闭环，清掉进度文件；下次是新一轮探测，不该复用旧结果
    if args.state and os.path.exists(args.state):
        os.remove(args.state)


if __name__ == "__main__":
    main()
