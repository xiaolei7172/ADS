# -*- coding: utf-8 -*-
"""
公共工具库：域名校验、白名单父子域匹配、路径定位。
供 data/python 下各脚本复用，保证「白名单判定」全流程只有一套逻辑。
"""
import os
import re
import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../.."))
RULES_DIR = os.path.join(REPO_ROOT, "data", "rules")
TMP_DIR = os.path.join(REPO_ROOT, "data", "tmp")
MOD_DIR = os.path.join(REPO_ROOT, "data", "mod")

# 合法域名：字母数字连字符标签 + 2~24 位字母 TLD
RE_DOMAIN = re.compile(
    r"^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,24}$", re.IGNORECASE
)
# ||domain^
RE_BLOCK_DOMAIN = re.compile(r"^\|\|([a-zA-Z0-9.-]+)\^$")
# @@||domain^（含子域语义）
RE_ALLOW_DOMAIN = re.compile(r"^@@\|\|([a-zA-Z0-9.-]+)\^")

# 回环/本地主机名：混进拦截列表只会造成误杀
LOOPBACK_HOSTS = {
    "localhost", "localhost.localdomain", "local", "ip6-localhost",
    "ip6-loopback", "broadcasthost", "ip6-allnodes", "ip6-allrouters",
    "ip6-mcastprefix", "ip6-localnet",
}
RE_HOSTS_LINE = re.compile(r"^(?:0\.0\.0\.0|127\.0\.0\.\d+|::1?|fe80::)\s+(\S+)", re.I)


def valid_domain(d):
    """合法域名（不含通配符/端口/路径）"""
    return bool(d) and bool(RE_DOMAIN.match(d))


def block_domain(line):
    """||domain^ → 合法域名；其余返回 None"""
    m = RE_BLOCK_DOMAIN.match(line.strip())
    if not m:
        return None
    d = m.group(1).lower().strip(".")
    return d if valid_domain(d) else None


def allow_domain(line):
    """@@||domain^ → 合法域名；其余返回 None"""
    m = RE_ALLOW_DOMAIN.match(line.strip())
    if not m:
        return None
    d = m.group(1).lower().strip(".")
    return d if valid_domain(d) else None


def is_junk_hosts_line(line):
    """hosts 格式行：回环/本地主机名判为垃圾；指向正常域名的返回 False（保留）"""
    m = RE_HOSTS_LINE.match(line.strip())
    if not m:
        return False
    target = m.group(1).lower()
    if target in LOOPBACK_HOSTS:
        return True
    if "." not in target or target.replace(".", "").isdigit():
        return True  # localhost / 纯 IP 目标
    return False


def hosts_target(line):
    """
    hosts 拦截行（0.0.0.0 domain / 127.0.0.1 domain）→ 合法域名；否则 None。
    回环/本地主机名返回 None（is_junk_hosts_line 已处理，这里不重复）。
    """
    m = RE_HOSTS_LINE.match(line.strip())
    if not m:
        return None
    target = m.group(1).lower()
    if valid_domain(target):
        return target
    return None


def is_allowed(domain, allow_set):
    """
    白名单父子域匹配：@@||a.com^ 覆盖 a.com 及其全部子域。
    （原脚本只做全等匹配，不符合 AdGuard 白名单语义。）
    """
    parts = domain.split(".")
    for i in range(len(parts)):
        if ".".join(parts[i:]) in allow_set:
            return True
    return False


def build_allow_domains():
    """
    收集全部白名单域名：data/rules/allow.txt（远程合并结果）+ data/mod/whitelist.txt（本地）。
    供 filter-dns / qx / smartdns 等派生脚本统一使用。
    """
    allow = set()
    for path in (os.path.join(RULES_DIR, "allow.txt"),
                 os.path.join(MOD_DIR, "whitelist.txt")):
        if not os.path.exists(path):
            continue
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                d = allow_domain(line)
                if d:
                    allow.add(d)
    return allow


def count_valid_lines(path_or_text, is_path=True):
    """有效规则行数（跳过空行和 !/# 注释）"""
    if is_path:
        try:
            with open(path_or_text, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        except OSError:
            return 0
    else:
        text = path_or_text
    n = 0
    for line in text.splitlines():
        s = line.strip()
        if s and not s.startswith(("!", "#")):
            n += 1
    return n


def beijing_now():
    """北京时间（固定 UTC+8，无夏令时；不依赖 pytz）"""
    tz = datetime.timezone(datetime.timedelta(hours=8))
    return datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
