# -*- coding: utf-8 -*-
"""
生成 dnsmasq 拦截配置（dnsmasq.conf）。

为什么单独出一份：
  OpenWrt / Pi-hole / 家用软路由的 DNS 后端大多是 dnsmasq，
  之前的 hosts 方案靠 addn-hosts 引入，但没有「后缀」概念——
  0.0.0.0 a.b.com 拦不到 x.a.b.com，实测漏掉 1.4 万个被折叠的子域。
  address=/域名/ 是 dnsmasq 原生的后缀匹配语法，连同全部子域一起作答，
  所以这里直接用 dns.txt（已折叠）即可，不需要折叠前的域名集。

格式：address=/example.com/0.0.0.0
  · 显式给 0.0.0.0，兼容所有 dnsmasq 版本（OpenWrt 老固件也能吃）；
  · 想同时拦 IPv6：全局替换为 address=/example.com/#（需 dnsmasq ≥ 2.86），
    或换成 local=/example.com/ 直接答 NXDOMAIN。
"""
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from common import RULES_DIR, block_domain

input_file_path = os.path.join(RULES_DIR, "dns.txt")
output_file_path = os.path.join(RULES_DIR, "dnsmasq.conf")

kept, skipped = 0, 0
try:
    fin = open(input_file_path, "r", encoding="utf-8", errors="ignore")
except OSError:
    print(f"❌ 无法读取文件：{input_file_path}")
    sys.exit(1)

with fin, open(output_file_path, "w", encoding="utf-8", newline="\n") as fout:
    fout.write("# 天影规则聚合 · dnsmasq rules\n")
    fout.write("# Homepage: https://github.com/xiaolei7172/ADS\n")
    fout.write("# Format: address=/domain/0.0.0.0（后缀匹配，连同子域一起拦截）\n\n")
    for line in fin:
        line = line.strip()
        if not line or line.startswith(("!", "#", "[")):
            continue
        d = block_domain(line)
        if d is None:
            skipped += 1
            continue
        fout.write(f"address=/{d}/0.0.0.0\n")
        kept += 1

print(f"✅ 生成完成！共 {kept} 条 dnsmasq 规则（跳过非法 {skipped} 条）")
