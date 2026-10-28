# -*- coding: utf-8 -*-
"""
原地更新 README 统计数字 + 发布前安全闸门。
改进点（相对旧版）：
  1. 计数没变化时不写 README——旧版每次都写新时间戳，规则没变也产生 diff；
  2. 去掉 pytz 依赖（固定 UTC+8）；
  3. 【关键新增】发布闸门：把当前规则条数与上一次已提交版本对比，
     总量骤降（>10%）或低于绝对下限 → exit 1 中止工作流。
     旧版上游挂掉时 25 万条会静默变成几千条照样发布，这道闸门就是防它。
     本脚本在 workflow 中位于 git commit/push 之前，exit 1 即可拦住发布，
     无需修改工作流文件。
"""
import os
import re
import json
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from common import RULES_DIR, TMP_DIR, count_valid_lines, beijing_now

REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../.."))
README_PATH = os.path.join(REPO_ROOT, "README.md")

# ==========================================
# 当前条数
# ==========================================
adblock = count_valid_lines(os.path.join(RULES_DIR, "adblock.txt"))
dns = count_valid_lines(os.path.join(RULES_DIR, "dns.txt"))
allow = count_valid_lines(os.path.join(RULES_DIR, "allow.txt"))
print(f"📊 当前统计：拦截 {adblock} | DNS {dns} | 白名单 {allow}")

# ==========================================
# 发布闸门：与上一次已提交版本对比
# ==========================================
ABSOLUTE_FLOOR = 50000   # dns.txt 绝对下限
DROP_RATIO = 0.90        # 不得低于上一版的 90%

def previous_count(path_in_repo):
    try:
        r = subprocess.run(
            ["git", "show", f"HEAD:{path_in_repo}"],
            cwd=REPO_ROOT, capture_output=True, text=True,
            encoding="utf-8", errors="ignore", timeout=60,
        )
        if r.returncode != 0:
            return None
        return count_valid_lines(r.stdout, is_path=False)
    except Exception:
        return None

def gate(name, current, prev):
    if prev is None:
        return  # 本地无 git 历史（首次运行），跳过
    if prev < ABSOLUTE_FLOOR:
        return  # 上一版本就很小，不适用比例判断
    if current < ABSOLUTE_FLOOR:
        print(f"🚫 闸门拦截：{name} 仅剩 {current} 条，低于绝对下限 {ABSOLUTE_FLOOR}。")
        sys.exit(1)
    if current < prev * DROP_RATIO:
        pct = (1 - current / prev) * 100
        print(f"🚫 闸门拦截：{name} 从 {prev} 条跌到 {current} 条（-{pct:.1f}%），疑似上游大面积故障。")
        sys.exit(1)

gate("adblock.txt", adblock, previous_count("data/rules/adblock.txt"))
gate("dns.txt", dns, previous_count("data/rules/dns.txt"))
gate("allow.txt", allow, previous_count("data/rules/allow.txt"))
print("✅ 发布闸门通过")

# ==========================================
# 更新 README（计数或时间确实变化才写）
# ==========================================
if not os.path.exists(README_PATH):
    print("⚠️ 未找到 README.md，跳过")
    sys.exit(0)

with open(README_PATH, "r", encoding="utf-8") as f:
    content = f.read()

now = beijing_now()
updated = content
updated = re.sub(r"🕒 \*\*更新时间\*\*：.*?（北京时间）", rf"🕒 **更新时间**：{now}（北京时间）", updated)
updated = re.sub(r"🚫 \*\*广告拦截规则\*\*：\d+ 条", rf"🚫 **广告拦截规则**：{adblock} 条", updated)
updated = re.sub(r"🌐 \*\*DNS 拦截域名\*\*：\d+ 个", rf"🌐 **DNS 拦截域名**：{dns} 个", updated)
updated = re.sub(r"✅ \*\*白名单放行规则\*\*：\d+ 条", rf"✅ **白名单放行规则**：{allow} 条", updated)

# ==========================================
# 源健康度：dl.py 落盘的下载状态渲染进 README
# ==========================================
def render_dl_status():
    status_path = os.path.join(TMP_DIR, "dl_status.json")
    if not os.path.exists(status_path):
        return None
    try:
        with open(status_path, "r", encoding="utf-8") as f:
            status = json.load(f)
    except (OSError, ValueError):
        return None
    if not status:
        return None
    total = len(status)
    ok_n = sum(1 for s in status if s.get("ok"))
    if ok_n == total:
        return f"✅ **上游源状态**：{total}/{total} 全部下载成功"
    failed_items = "、".join(
        f"{s['name']}（{s.get('err') or '未知错误'}）" for s in status if not s.get("ok")
    )
    return f"⚠️ **上游源状态**：{ok_n}/{total} 成功，失败：{failed_items}"

dl_line = render_dl_status()
MARK_S, MARK_E = "<!-- DL_STATUS_START -->", "<!-- DL_STATUS_END -->"
if dl_line and MARK_S in updated and MARK_E in updated:
    block = f"{MARK_S}\n{dl_line}\n{MARK_E}"
    updated = re.sub(re.escape(MARK_S) + r".*?" + re.escape(MARK_E), block, updated, flags=re.S)

# 判断"实质变化"：忽略时间戳行，其余内容必须有一处不同才写回
strip_ts = lambda s: re.sub(r"🕒 \*\*更新时间\*\*：.*?（北京时间）", "", s)
if strip_ts(updated) == strip_ts(content):
    print("⏭️  README 统计无变化，不写入（避免无意义 diff）")
else:
    with open(README_PATH, "w", encoding="utf-8", newline="\n") as f:
        f.write(updated)
    print("✅ README 原地替换更新成功")

print(f"🕒{now} | 🚫{adblock} | 🌐{dns} | ✅{allow}")
