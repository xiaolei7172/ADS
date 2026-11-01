# -*- coding: utf-8 -*-
"""
格式层：8 种派生产物的「写一行 / 读一行 / 来源 / 匹配语义」全部声明在这里。

为什么要把格式变成数据：
  原来 qx / surge / clash / smartdns / dnsmasq / domain_list / hosts / smartdns_whitelist
  是同一个循环抄了 8 遍；校验侧 check-quality 与 verify-fixes 又各写一套解析。
  于是「产品说它写了什么」和「校验器说它读到什么」可能不是一回事——
  历史上 qx 漏拦 1.4 万子域、hosts 漏拦 1.4 万、dnsmasq 不认 address= 全是这类漂移。

现在新增一种格式 = 往 FORMATS 里加一个 Format(...)，写、读、校验三处同时就有了。
"""
import hashlib
import re
from dataclasses import dataclass
from typing import Callable, Optional, Sequence, Tuple, Union


# ==============================================
# 读：一行产物 → 域名（校验器与一致性比对共用这一份）
# ==============================================
def read_csv_suffix(line):
    """DOMAIN-SUFFIX,domain[,reject]"""
    parts = line.split(",")
    if len(parts) >= 2 and parts[0].strip().upper() == "DOMAIN-SUFFIX":
        return parts[1].strip().lower() or None
    return None


def read_mihomo(line):
    """  - '+.domain'  →  domain"""
    s = line.strip()
    if not s.startswith("-"):
        return None
    s = s.lstrip("- ").strip().strip("'\"")
    if s.startswith("+."):
        s = s[2:]
    return s.lower() or None


def read_address(line):
    """smartdns: address /d/#   dnsmasq: address=/d/0.0.0.0"""
    m = re.match(r"^address\s*=?\s*/([^/]+)/", line.strip())
    return m.group(1).lower() if m else None


def read_bare(line):
    """纯域名清单（ad-domain.txt）"""
    s = line.strip()
    if not s or s.startswith(("#", "!", "[")):
        return None
    return s.lower()


def read_hosts(line):
    """0.0.0.0 domain（精确匹配）"""
    parts = line.split()
    if len(parts) == 2 and parts[0] in ("0.0.0.0", "127.0.0.1", "::1"):
        return parts[1].lower()
    return None


# ==============================================
# 表头：固定若干行，或用域名集算出来的动态行
# ==============================================
Reader = Callable[[str], Optional[str]]
Header = Union[Tuple[str, ...], Callable[[Sequence[str]], Sequence[str]]]


@dataclass(frozen=True)
class Format:
    name: str                     # 产物文件名
    header: Header                # 表头（每个元素一行，不含换行符）
    line: str                     # 正文模板，必须含一个 {}
    read: Reader                  # 一行 → 域名
    source: str = "block"         # 域名来源：block=dns.txt / unfolded=折叠前 / allow=白名单
    suffix: bool = True           # True=后缀匹配（覆盖子域），False=精确匹配（hosts）
    dedup: bool = True            # 保序去重

    def header_lines(self, domains):
        h = self.header
        return tuple(h(domains)) if callable(h) else tuple(h)

    def render(self, domain):
        return self.line.format(domain)


# ---- 表头常量（顺序与空行都要与既有产物逐字节一致）----
H_QX = (
    "# 天影规则聚合 · Quantumult X 拦截规则",
    "# Github: https://github.com/xiaolei7172/ADS",
    "# Format: DOMAIN-SUFFIX,domain,reject（后缀匹配，等价 AdGuard 的 ||domain^）",
    "",
)
H_SURGE = (
    "# 天影规则聚合 · Surge RULE-SET",
    "# 由 dns.txt（已去重）自动转换 | https://github.com/xiaolei7172/ADS | 每日自动更新",
)
H_MIHOMO = (
    "# 天影规则聚合 · Clash/Mihomo 域名集",
    "# 由 dns.txt（已去重）自动转换；behavior: domain",
    "# 📌 https://github.com/xiaolei7172/ADS | 🔄 每日自动更新",
    "payload:",
)
H_SMARTDNS = (
    "# 天影规则聚合 · SmartDNS rules",
    "# Homepage: https://github.com/xiaolei7172/ADS",
    "# Format: address /domain/#",
    "",
)
H_DNSMASQ = (
    "# 天影规则聚合 · dnsmasq rules",
    "# Homepage: https://github.com/xiaolei7172/ADS",
    "# Format: address=/domain/0.0.0.0（后缀匹配，连同子域一起拦截）",
    "",
)
H_ADDOMAIN = (
    "[Host]",
    "# 天影规则聚合 · 纯净域名黑名单",
    "# Github: https://github.com/xiaolei7172/ADS",
    "# 自动提取：只保留纯域名，适配 AdGuard Home / 路由器",
    "",
)
H_SMARTDNS_WHITE = (
    "# 天影规则聚合 · SmartDNS whitelist",
    "# Homepage: https://github.com/xiaolei7172/ADS",
    "# Format: address /domain/-",
    "",
)


def h_hosts(domains):
    """hosts 表头：条数 + 内容指纹（不能写时间戳）。

    以前这里写的是「⏰ 更新时间：{beijing_now()}」，而 h_hosts 每次运行都会重算，
    于是条数一条没变、整份 7 MB 文件也被重写一遍：
      · workflow 里 `git diff --cached --quiet` 的"无变化不提交"分支永远走不到；
      · 用户看 git log 会以为每天都在更新，其实可能一条规则都没动。
    改成域名集的内容指纹后，只有集合真的变了，文件才变。
    """
    digest = hashlib.sha256("\n".join(domains).encode("utf-8")).hexdigest()[:12]
    return (
        "# 天影规则聚合 · HOSTS 版",
        "# 由 dns.txt 折叠前的完整域名集转换，含全部子域，覆盖与 AdGuard 语义对齐",
        "# ⚠️ hosts 只能精确匹配，拦不到未列出的子域；需要完整子域覆盖请用 dns.txt / smartdns.conf / surge.list",
        "# 📌 项目地址：https://github.com/xiaolei7172/ADS",
        f"# 🔖 内容指纹：{digest} | 📊 有效规则：{len(domains)} 条"
        " | ⏰ 变更时间见 git 提交记录",
        "# 🔄 更新频率：每日自动更新（北京时间 08:00）",
    )


FORMATS = (
    Format("qx.list", H_QX, "DOMAIN-SUFFIX,{},reject\n", read_csv_suffix),
    Format("surge.list", H_SURGE, "DOMAIN-SUFFIX,{}\n", read_csv_suffix),
    Format("mihomo.yaml", H_MIHOMO, "  - '+.{}'\n", read_mihomo),
    Format("smartdns.conf", H_SMARTDNS, "address /{}/#\n", read_address),
    Format("dnsmasq.conf", H_DNSMASQ, "address=/{}/0.0.0.0\n", read_address),
    Format("ad-domain.txt", H_ADDOMAIN, "{}\n", read_bare),
    Format("smartdns-whitelist.conf", H_SMARTDNS_WHITE, "address /{}/-\n", read_address,
           source="allow"),
    Format("hosts.txt", h_hosts, "0.0.0.0 {}\n", read_hosts,
           source="unfolded", suffix=False),
)

BY_NAME = {f.name: f for f in FORMATS}
