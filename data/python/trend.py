# -*- coding: utf-8 -*-
"""
规则量趋势图：每次更新把条数追加到 data/stats/stats.csv，
并生成 SVG 折线图 data/stats/trend.svg 供 README 嵌入。
- 数据点超过 90 个时滚动保留最近 90 个（文件不无限膨胀）；
- 当天已有记录且数值未变时不追加（规则没变不产生新数据点）；
- 纯标准库画 SVG，无第三方依赖。
"""
import os
import csv
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys_paths = os.path.abspath(SCRIPT_DIR)
import sys
sys.path.insert(0, sys_paths)
from common import RULES_DIR, REPO_ROOT, count_valid_lines, beijing_now

STATS_DIR = os.path.join(REPO_ROOT, "data", "stats")
CSV_PATH = os.path.join(STATS_DIR, "stats.csv")
SVG_PATH = os.path.join(STATS_DIR, "trend.svg")
MAX_POINTS = 90

# ==========================================
# 1. 追加数据点
# ==========================================
now = beijing_now()
ts = now[:16]  # 2026-10-27 16:40
dns = count_valid_lines(os.path.join(RULES_DIR, "dns.txt"))
adblock = count_valid_lines(os.path.join(RULES_DIR, "adblock.txt"))
allow = count_valid_lines(os.path.join(RULES_DIR, "allow.txt"))

os.makedirs(STATS_DIR, exist_ok=True)
rows = []
if os.path.exists(CSV_PATH):
    with open(CSV_PATH, "r", encoding="utf-8", newline="") as f:
        rows = list(csv.reader(f))

header = ["time", "dns", "adblock", "allow"]
if rows and rows[0] == header:
    data = rows[1:]
else:
    data = []

# 当天已记录且数值未变 → 不追加（避免规则没变也堆数据点）
today = now[:10]
if data:
    last = data[-1]
    if last[0][:10] == today and last[1:] == [str(dns), str(adblock), str(allow)]:
        pass  # 已有当点，不重复
    else:
        data.append([ts, str(dns), str(adblock), str(allow)])
else:
    data.append([ts, str(dns), str(adblock), str(allow)])

if len(data) > MAX_POINTS:
    data = data[-MAX_POINTS:]

with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(header)
    w.writerows(data)

# ==========================================
# 2. 画 SVG 折线图（adblock 与 dns 两条线）
# ==========================================
W, H = 760, 280
L, R, T, B = 64, 24, 28, 42
PW, PH = W - L - R, H - T - B

COLORS = {"adblock": "#3fb950", "dns": "#58a6ff"}
TXT = "#7d8590"      # 中性灰：亮暗主题下都可读
GRID = "rgba(125,134,150,0.25)"

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def kfmt(v):
    return f"{v/1000:.0f}k" if v >= 1000 else str(v)

svg = []
if len(data) >= 2:
    n = len(data)
    dns_vals = [int(r[1]) for r in data]
    ad_vals = [int(r[2]) for r in data]
    ymax = max(max(dns_vals), max(ad_vals)) * 1.06
    ymin = min(min(dns_vals), min(ad_vals)) * 0.94

    def xy(i, v):
        x = L + PW * i / (n - 1)
        y = T + PH * (1 - (v - ymin) / (ymax - ymin))
        return x, y

    def polyline(vals, color):
        pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in (xy(i, v) for i, v in enumerate(vals)))
        return (f'<polyline fill="none" stroke="{color}" stroke-width="2.5" '
                f'stroke-linejoin="round" stroke-linecap="round" points="{pts}"/>')

    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="规则量趋势图">')
    # 标题与图例
    svg.append(f'<text x="{L}" y="18" font-family="sans-serif" font-size="14" fill="{TXT}">📊 规则量趋势（最近 {n} 次更新）</text>')
    svg.append(f'<rect x="{W-R-190}" y="8" width="14" height="4" rx="2" fill="{COLORS["adblock"]}"/>')
    svg.append(f'<text x="{W-R-170}" y="14" font-family="sans-serif" font-size="12" fill="{TXT}">拦截规则</text>')
    svg.append(f'<rect x="{W-R-100}" y="8" width="14" height="4" rx="2" fill="{COLORS["dns"]}"/>')
    svg.append(f'<text x="{W-R-80}" y="14" font-family="sans-serif" font-size="12" fill="{TXT}">DNS 域名</text>')
    # 横向网格 + Y 轴刻度
    for i in range(5):
        v = ymin + (ymax - ymin) * i / 4
        y = T + PH * (1 - i / 4)
        svg.append(f'<line x1="{L}" y1="{y:.1f}" x2="{W-R}" y2="{y:.1f}" stroke="{GRID}" stroke-width="1"/>')
        svg.append(f'<text x="{L-8}" y="{y+4:.1f}" text-anchor="end" font-family="sans-serif" font-size="11" fill="{TXT}">{kfmt(int(v))}</text>')
    # 折线 + 末点标注
    svg.append(polyline(ad_vals, COLORS["adblock"]))
    svg.append(polyline(dns_vals, COLORS["dns"]))
    for vals, color in ((ad_vals, COLORS["adblock"]), (dns_vals, COLORS["dns"])):
        x, y = xy(n - 1, vals[-1])
        svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="{color}"/>')
        svg.append(f'<text x="{x-6:.1f}" y="{y-8:.1f}" text-anchor="end" font-family="sans-serif" font-size="12" font-weight="bold" fill="{color}">{vals[-1]:,}</text>')
    # X 轴日期标签（首/中/尾）
    for idx in (0, (n - 1) // 2, n - 1):
        x, _ = xy(idx, 0)
        svg.append(f'<text x="{x:.1f}" y="{H-12}" text-anchor="middle" font-family="sans-serif" font-size="11" fill="{TXT}">{esc(data[idx][0][:10])}</text>')
    svg.append("</svg>")
else:
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="80" viewBox="0 0 {W} 80">'
               f'<text x="{W/2}" y="44" text-anchor="middle" font-family="sans-serif" font-size="14" fill="{TXT}">趋势图需要至少 2 次更新数据，将在下次更新后生成</text></svg>')

with open(SVG_PATH, "w", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(svg))

print(f"✅ 趋势数据已更新：{len(data)} 个数据点（最新 DNS {dns:,} / 拦截 {adblock:,} / 白名单 {allow:,}）")
print(f"✅ 趋势图已生成：{SVG_PATH}")
