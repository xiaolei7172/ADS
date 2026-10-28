# -*- coding: utf-8 -*-
"""输出动态徽章文案（供 workflow 的 Prepare Badge Message 步骤调用）"""
import os
import re
from datetime import datetime, timedelta, timezone

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
readme = open(os.path.join(REPO_ROOT, "README.md"), encoding="utf-8").read()
dns = re.search(r"DNS 拦截域名\*\*：(\d+)", readme)
ad = re.search(r"广告拦截规则\*\*：(\d+)", readme)
now = datetime.now(timezone.utc) + timedelta(hours=8)  # 北京时间（UTC+8，无夏令时）
print("DNS {} | 拦截 {} | {:%H:%M} 更新".format(
    dns.group(1) if dns else 0, ad.group(1) if ad else 0, now))
