<div align="center">

<a id="top"></a>

# 🛸 天影规则聚合 · TianYing Rules Hub

**⚡ 强力去广告 · 每日自动更新 · 全平台适配 ⚡**

> 干净的网络，从一条订阅开始 —— 20 路数据源聚合 · 三层真实去重 · 每日自动更新，一套规则覆盖 11 种格式

[![CI 状态](https://github.com/xiaolei7172/ADS/actions/workflows/Update-Rules.yml/badge.svg)](https://github.com/xiaolei7172/ADS/actions/workflows/Update-Rules.yml)
[![最近提交](https://img.shields.io/github/last-commit/xiaolei7172/ADS/master?label=%E6%9C%80%E8%BF%91%E6%9B%B4%E6%96%B0&color=success)](https://github.com/xiaolei7172/ADS/commits/master)
[![License](https://img.shields.io/badge/License-MIT-blue)](LICENSE)

[📥 规则订阅](#-规则订阅中心) · [🚀 快速开始](#-快速开始) · [📦 客户端下载](#-客户端下载速查) · [📊 实时统计](#-实时项目统计) · [📚 上游数据源](#-上游规则数据源) · [🧪 拦截测试](#-拦截效果在线测试) · [📜 更新历史](#-更新历史)

---

## 📊 实时项目统计

### 🔮 天影规则聚合 · 实时规则规模


🕒 **更新时间**：2026-11-01 16:51:43（北京时间）


🚫 **广告拦截规则**：273466 条


🌐 **DNS 拦截域名**：242370 个


✅ **白名单放行规则**：6767 条（约半数可在 DNS 层直接生效，其余为浏览器版 AdGuard 的路径级 / `$domain=` 规则，DNS 层无效）

<!-- DL_STATUS_START -->
✅ **上游源状态**：20/20 全部下载成功
<!-- DL_STATUS_END -->

![规则量趋势](data/stats/trend.svg)

<!-- 🏷️ 动态徽章：① 在 gist.github.com 新建一个 Gist；② 仓库 Settings → Secrets 新建 GIST_SECRET（需 gist 权限的 Token）、Settings → Variables 新建 GIST_ID（填 Gist ID）；③ 取消下一行注释并把 <GIST_ID> 换成实际 ID
![天影规则](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/xiaolei7172/<GIST_ID>/raw/tianying-stats.json)
-->

---

## 🎯 九大保障

| 保障 | 说明 |
| :--- | :--- |
| 🧹 **真实去重** | 精确去重 + 大小写归一 + 父子域语义去重，0 冗余规则 |
| 🛡️ **质量闸门** | 每次发布前自检重复/冗余/计数自洽，不合格自动拦截 |
| 🔍 **格式一致** | 48 个用例 × 11 种产物逐格式比对同一域名的判定，任何格式走偏当场拦下（历史上的 qx / hosts / dnsmasq 三次漏拦都是它抓出来的） |
| 🚧 **发布护栏** | 规则量骤降 >10% 或低于 5 万条即中止发布，绝不带病上线 |
| 🧯 **投毒熔断** | 白名单移除拦截规则 >8%（正常 ≈2%）即判定投毒/黑白错配，中止发布；下载阶段同步做黑白方向体检 |
| 🎯 **精确剔除** | 上游把整个公司主域 / API 网关一锅端时，按域名逐条拆除，子域规则与白名单不受牵连 |
| 🪄 **可信通配** | 上游通配白名单（如 `v*.douyinvod.com`）经人工甄别后落地展开，广告混入的通配保持忽略 |
| 🌐 **多源容灾** | GitHub API + 3 个 jsDelivr 子域 + gh-proxy 共 6 通道下载兜底 |
| 🚨 **失败可见** | 更新失败自动开 issue + 写运行摘要 + 上传产物，规则不会静默停在几天前 |
| 📋 **来源可溯** | 每条规则标注所属上游来源，排查误杀一步定位 |

---

## 🚀 快速开始

> 💡 先把客户端装好，再贴订阅链接。下面全部为**官方来源**（链接已实测可达）；GitHub Releases 在国内不稳时，可在链接前加 `https://gh-proxy.com/` 加速。

### 📦 客户端下载速查

| 软件 | 适用平台 | 官方下载 | 备注 |
| :--- | :--- | :--- | :--- |
| **AdGuard** | Windows / macOS / Android | [官网下载](https://adguard.com/zh_cn/download.html) | 商业软件（有试用），系统级全局拦截 |
| **AdGuard Home** | Win / macOS / Linux / Docker | [GitHub Releases](https://github.com/AdguardTeam/AdGuardHome/releases) | 免费开源，自建 DNS 服务器 |
| **OpenWrt** | 路由器 | [固件选择器](https://firmware-selector.openwrt.org/) · [ImmortalWrt](https://github.com/immortalwrt/immortalwrt) | 免费开源路由系统，国内推荐后者 |
| **SmartDNS** | Linux / OpenWrt | [GitHub Releases](https://github.com/pymumu/smartdns/releases) | 免费开源，DNS 加速 + 拦截 |
| **Clash Verge Rev** | Win / macOS / Linux | [GitHub Releases](https://github.com/clash-verge-rev/clash-verge-rev/releases) | 免费开源图形客户端，最常用 |
| **Mihomo Party** | Win / macOS / Linux | [GitHub Releases](https://github.com/mihomo-party-org/mihomo-party/releases) | 免费开源，开箱即用 |
| **Mihomo 内核** | 全平台（命令行） | [GitHub Releases](https://github.com/MetaCubeX/mihomo/releases) | 进阶自建 / 软路由用 |
| **Quantumult X** | iOS / iPadOS | [App Store](https://apps.apple.com/app/quantumult-x/id1443988620) | 付费买断，需美区/港区账号 |
| **Surge** | iOS / macOS | [nssurge.com](https://nssurge.com) | 付费订阅；官网国内直连不稳，需自备网络 |

<details open>
<summary><b>🖥️ AdGuard（Windows / Mac / Android）</b></summary>
<br>

> 📥 下载：[Windows](https://adguard.com/zh_cn/adguard-windows/overview.html) · [macOS](https://adguard.com/zh_cn/adguard-mac/overview.html) · [Android](https://adguard.com/zh_cn/adguard-android/overview.html) · [全部平台](https://adguard.com/zh_cn/download.html)

1. 打开 AdGuard → 设置 → **内容拦截**（Windows 为「过滤器」）
2. 点击「添加过滤器」→「使用自定义过滤器」
3. 粘贴订阅链接（国内网络选加速列）：
   `https://testingcf.jsdelivr.net/gh/xiaolei7172/ADS@master/data/rules/adblock.txt`
4. 建议同时启用白名单：`https://testingcf.jsdelivr.net/gh/xiaolei7172/ADS@master/data/rules/allow.txt`

</details>

<details>
<summary><b>🌐 AdGuard Home</b></summary>
<br>

> 📥 下载：[GitHub Releases](https://github.com/AdguardTeam/AdGuardHome/releases) · 也支持 Docker（`docker run -p 53:53/tcp -p 53:53/udp -p 3000:3000 adguard/adguardhome`）

1. 管理后台 → 过滤器 → **DNS 拦截列表** → 添加拦截列表
2. 粘贴：`https://testingcf.jsdelivr.net/gh/xiaolei7172/ADS@master/data/rules/dns.txt`
3. 白名单（自定义过滤规则 → 放行）：`https://testingcf.jsdelivr.net/gh/xiaolei7172/ADS@master/data/rules/allow.txt`

</details>

<details>
<summary><b>📡 OpenWrt / dnsmasq 路由器</b></summary>
<br>

> 📥 固件：[官方固件选择器](https://firmware-selector.openwrt.org/) · [ImmortalWrt（国内源更全）](https://github.com/immortalwrt/immortalwrt) · OpenClash 插件：[Releases](https://github.com/vernesong/OpenClash/releases)

**方式一：dnsmasq 规则（推荐，后缀匹配，子域一起拦）**

1. SSH 登录路由器，把规则下到 dnsmasq 配置目录：
   `wget -O /etc/dnsmasq.d/tianying.conf https://testingcf.jsdelivr.net/gh/xiaolei7172/ADS@master/data/rules/dnsmasq.conf`
2. 让 dnsmasq 加载它：主配置 `/etc/dnsmasq.conf` 里若有 `conf-dir=/etc/dnsmasq.d` 即可直接生效；没有就追加一行
   `echo 'conf-file=/etc/dnsmasq.d/tianying.conf' >> /etc/dnsmasq.conf`
3. 重启服务：`/etc/init.d/dnsmasq restart`

> `address=/域名/0.0.0.0` 会连同该域名的全部子域一起作答。想顺带拦 IPv6，可把 `0.0.0.0` 全局替换为 `#`（需 dnsmasq ≥ 2.86），或改用 `local=/域名/` 直接答 NXDOMAIN。

**方式二：hosts（老固件兜底，无 conf-dir 时用）**

1. 下载 hosts 文件：`https://testingcf.jsdelivr.net/gh/xiaolei7172/ADS@master/data/rules/hosts.txt`
2. 覆盖到 `/etc/hosts` 末尾（或配合 dnsmasq 的 `addn-hosts` 引用）
3. 重启 dnsmasq：`/etc/init.d/dnsmasq restart`

> ⚠️ **hosts 只能精确匹配**：`0.0.0.0 a.b.com` 拦不到 `x.a.b.com`。本仓库的 hosts.txt 已把 dns.txt 折叠掉的 1.4 万个子域补回（比 dns.txt 多约 1.4 万条，含上游明确列出的全部域名），但上游没列出的子域仍然拦不到。要彻底覆盖子域，请优先用 **dns.txt（AdGuard Home）/ dnsmasq.conf / smartdns.conf / surge.list / mihomo.yaml / qx.list** 这些后缀匹配格式。

</details>

<details>
<summary><b>🔍 SmartDNS</b></summary>
<br>

> 📥 下载：[GitHub Releases](https://github.com/pymumu/smartdns/releases)（OpenWrt 可直接 `opkg install smartdns`）

1. 编辑 `smartdns.conf`，加入：`conf-file https://testingcf.jsdelivr.net/gh/xiaolei7172/ADS@master/data/rules/smartdns.conf`
   （或下载后 `include` 到主配置）
2. 误杀放行：`conf-file .../data/rules/smartdns-whitelist.conf`
3. 重启服务：`/etc/init.d/smartdns restart`

</details>

<details>
<summary><b>🧩 Clash / Mihomo</b></summary>
<br>

> 📥 客户端：[Clash Verge Rev](https://github.com/clash-verge-rev/clash-verge-rev/releases) · [Mihomo Party](https://github.com/mihomo-party-org/mihomo-party/releases) · [Mihomo 内核](https://github.com/MetaCubeX/mihomo/releases)

```yaml
rule-providers:
  tianying-ad:
    type: http
    behavior: domain
    url: "https://testingcf.jsdelivr.net/gh/xiaolei7172/ADS@master/data/rules/mihomo.yaml"
    path: ./rules/tianying-ad.yaml
    interval: 43200
rules:
  - RULE-SET,tianying-ad,REJECT
```

</details>

---

## 📥 规则订阅中心

> 💡 国内网络推荐优先使用「国内加速链接」（jsDelivr，实测可用）；GitHub 直连不稳时再换直链。
> PC 版 AdGuard 选 `adblock.txt`；AdGuard Home / OpenWrt 选 `dns.txt`。

<details open>
<summary><b>🚫 广告拦截规则</b></summary>
<br>

| 规则类型 | 适用平台 | 📥 GitHub直链 | 🚀 国内加速链接 |
| :---- | :---- | :---- | :---- |
| AdGuard 拦截规则 | AdGuard 全家桶 | [adblock.txt](https://raw.githubusercontent.com/xiaolei7172/ADS/master/data/rules/adblock.txt) | [adblock.txt](https://testingcf.jsdelivr.net/gh/xiaolei7172/ADS@master/data/rules/adblock.txt) |
| AdGuard Home DNS拦截规则 | AdGuard Home / OpenWrt | [dns.txt](https://raw.githubusercontent.com/xiaolei7172/ADS/master/data/rules/dns.txt) | [dns.txt](https://testingcf.jsdelivr.net/gh/xiaolei7172/ADS@master/data/rules/dns.txt) |

</details>


<details>
<summary><b>📋 仅域名规则</b></summary>
<br>

| 规则类型 | 适用平台 | 📥 GitHub直链 | 🚀 国内加速链接 |
| :---- | :---- | :---- | :---- |
| 黑名单域名列表 | 通用（可自行转换） | [ad-domain.txt](https://raw.githubusercontent.com/xiaolei7172/ADS/master/data/rules/ad-domain.txt) | [ad-domain.txt](https://testingcf.jsdelivr.net/gh/xiaolei7172/ADS@master/data/rules/ad-domain.txt) |

</details>


<details>
<summary><b>📱 Quantumult X 规则</b></summary>
<br>

> 📥 客户端：[Quantumult X（App Store，付费）](https://apps.apple.com/app/quantumult-x/id1443988620)　|　导入位置：配置文件 →「引用」的 `[filter_remote]` 段

| 规则类型 | 适用平台 | 📥 GitHub直链 | 🚀 国内加速链接 |
| :---- | :---- | :---- | :---- |
| Quantumult X 规则 | Quantumult X | [qx.list](https://raw.githubusercontent.com/xiaolei7172/ADS/master/data/rules/qx.list) | [qx.list](https://testingcf.jsdelivr.net/gh/xiaolei7172/ADS@master/data/rules/qx.list) |

</details>


<details>
<summary><b>🔍 SmartDNS 规则</b></summary>
<br>

| 规则类型 | 适用平台 | 📥 GitHub直链 | 🚀 国内加速链接 |
| :---- | :---- | :---- | :---- |
| SmartDNS 拦截规则 | SmartDNS | [smartdns.conf](https://raw.githubusercontent.com/xiaolei7172/ADS/master/data/rules/smartdns.conf) | [smartdns.conf](https://testingcf.jsdelivr.net/gh/xiaolei7172/ADS@master/data/rules/smartdns.conf) |
| SmartDNS 白名单 | SmartDNS | [smartdns-whitelist.conf](https://raw.githubusercontent.com/xiaolei7172/ADS/master/data/rules/smartdns-whitelist.conf) | [smartdns-whitelist.conf](https://testingcf.jsdelivr.net/gh/xiaolei7172/ADS@master/data/rules/smartdns-whitelist.conf) |

</details>


<details>
<summary><b>🛠 dnsmasq 规则（OpenWrt / Pi-hole / 软路由）</b></summary>
<br>

> 后缀匹配：`address=/域名/0.0.0.0` 连同该域名的全部子域一起拦截，比 hosts 的精确匹配更彻底，也是家用路由最省事的方案。

| 规则类型 | 适用平台 | 📥 GitHub直链 | 🚀 国内加速链接 |
| :---- | :---- | :---- | :---- |
| dnsmasq 拦截规则 | OpenWrt / Pi-hole / 梅林 / 爱快（dnsmasq 后端） | [dnsmasq.conf](https://raw.githubusercontent.com/xiaolei7172/ADS/master/data/rules/dnsmasq.conf) | [dnsmasq.conf](https://testingcf.jsdelivr.net/gh/xiaolei7172/ADS@master/data/rules/dnsmasq.conf) |

</details>


<details>
<summary><b>📛 HOSTS 拦截规则</b></summary>
<br>

| 规则类型 | 适用平台 | 📥 GitHub直链 | 🚀 国内加速链接 |
| :---- | :---- | :---- | :---- |
| HOSTS 格式（0.0.0.0） | 路由器 / 系统 hosts / 无 root 安卓 | [hosts.txt](https://raw.githubusercontent.com/xiaolei7172/ADS/master/data/rules/hosts.txt) | [hosts.txt](https://testingcf.jsdelivr.net/gh/xiaolei7172/ADS@master/data/rules/hosts.txt) |

</details>


<details>
<summary><b>✅ 白名单规则</b></summary>
<br>

| 规则类型 | 适用平台 | 📥 GitHub直链 | 🚀 国内加速链接 |
| :---- | :---- | :---- | :---- |
| 白名单规则（误杀放行） | AdGuard 全家桶 | [allow.txt](https://raw.githubusercontent.com/xiaolei7172/ADS/master/data/rules/allow.txt) | [allow.txt](https://testingcf.jsdelivr.net/gh/xiaolei7172/ADS@master/data/rules/allow.txt) |

</details>


<details>
<summary><b>🧩 Clash / Mihomo / Surge 规则</b></summary>
<br>

> 📥 客户端：[Clash Verge Rev](https://github.com/clash-verge-rev/clash-verge-rev/releases) · [Mihomo Party](https://github.com/mihomo-party-org/mihomo-party/releases) · [Surge](https://nssurge.com)（付费，官网需自备网络）

| 规则类型 | 适用平台 | 📥 GitHub直链 | 🚀 国内加速链接 |
| :---- | :---- | :---- | :---- |
| Mihomo 域名集 | Clash / Mihomo / Stash（behavior: domain） | [mihomo.yaml](https://raw.githubusercontent.com/xiaolei7172/ADS/master/data/rules/mihomo.yaml) | [mihomo.yaml](https://testingcf.jsdelivr.net/gh/xiaolei7172/ADS@master/data/rules/mihomo.yaml) |
| Surge 规则集 | Surge / Loon（RULE-SET） | [surge.list](https://raw.githubusercontent.com/xiaolei7172/ADS/master/data/rules/surge.list) | [surge.list](https://testingcf.jsdelivr.net/gh/xiaolei7172/ADS@master/data/rules/surge.list) |

</details>


<details>
<summary><b>🔄 公共 DNS 服务器节点</b></summary>
<br>

| 节点 | 地址 |
| :---- | :---- |
| 天影公共 DNS | `https://tianying.pub.xlxbk.cn/xlxbk/api` |
| 18bit DoH | `https://doh.18bit.cn/dns-query` |
| 360 DoH | `https://doh.360.cn/dns-query` |
| 阿里 DoH | `https://dns.alidns.com/dns-query` |
| 腾讯 DoH | `https://doh.pub/dns-query` |
| XLXBK API | `https://pub.xlxbk.cn/xlxbk/api` |

</details>

</div>


## 📚 上游规则数据源

> 管线实际下载 **20 路源**（14 个拦截 + 6 个白名单），另有 4 个本仓库自定义文件（黑名单 / 白名单 / 精确剔除表 / 可信通配表）。
> 其中「合并源」本身已聚合多个二级上游，因此实际覆盖的项目数量多于 19。
> 每个来源在成品中都有分区标注，误拦可直接定位到源。

<details>
<summary><b>点击查看全部数据来源</b></summary>
<br>

### 🔴 拦截规则（14 路）

| 来源 | 侧重 | 原始地址 |
| :--- | :--- | :--- |
| 📛 **1007-Hosts** | Hosts 混合源（已含其 reward 全部域名） | [10007_auto/all](https://raw.githubusercontent.com/lingeringsound/10007_auto/master/all) |
| 📛 **anti-AD 官方规则** | 命中率高、兼容性强 | [anti-ad.net/easylist.txt](https://anti-ad.net/easylist.txt) |
| 📛 **AdRules DNS List** | DNS 专用 | [gp.adrules.top/dns.txt](https://gp.adrules.top/dns.txt) |
| 📛 **AdGuard DNS Filter 官方** | DNS 专用（官方维护） | [AdGuardSDNSFilter](https://adguardteam.github.io/AdGuardSDNSFilter/Filters/filter.txt) |
| 📛 **OISD 拦截规则** | DNS 专用，低误杀 | [small.oisd.nl](https://small.oisd.nl/) |
| 📛 **个人合并规则** | 合并源（群主维护） | [666/rules.txt](https://raw.githubusercontent.com/qq5460168/666/master/rules.txt) |
| 📛 **酷安@大萌主** | 接口 / SDK 广告 | [banad/jiekouAD.txt](https://raw.githubusercontent.com/damengzhu/banad/main/jiekouAD.txt) |
| 📛 **浮风拦截规则** | 合并源 | [ad-rules-merged](https://raw.githubusercontent.com/Thelongdarkorg/ad-rules-merged/main/merged.txt) |
| 📛 **海哥规则** | 国内 App 专项（腾讯/字节/小米/番茄系） | [HG/hg1.txt 官方镜像](https://github.com/2771936993/HG/blob/main/hg1.txt) |
| 📛 **秋风广告规则** | 综合拦截 | [AWAvenue-Ads-Rule](https://raw.githubusercontent.com/TG-Twilight/AWAvenue-Ads-Rule/main/AWAvenue-Ads-Rule.txt) |
| 📛 **乘风视频规则** | 视频贴片广告 | [Adblock-Plus-Rule/mv.txt](https://raw.githubusercontent.com/xinggsf/Adblock-Plus-Rule/master/mv.txt) |
| 📛 **乘风通用规则** | 通用拦截 | [Adblock-Plus-Rule/rule.txt](https://raw.githubusercontent.com/xinggsf/Adblock-Plus-Rule/master/rule.txt) |
| 📛 **晴雅拦截规则** | 综合拦截 | [qy-Ads-Rule/black.txt](https://raw.githubusercontent.com/rssvcn/qy-Ads-Rule/main/black.txt) |
| 📛 **abclq Hosts 拦截规则** | Hosts 综合拦截 | [home-dns-adblock hosts](https://raw.githubusercontent.com/abclq/home-dns-adblock/refs/heads/main/dist/hosts.txt) |
| 🏠 **本仓库自定义** | 红果短剧 / 番茄小说专项等 | [data/mod/adblock.txt](https://raw.githubusercontent.com/xiaolei7172/ADS/master/data/mod/adblock.txt) |

### 🟢 白名单规则（6 路 + 自定义）

| 来源 | 侧重 | 原始地址 |
| :--- | :--- | :--- |
| ✅ **当初白名单** | 综合放行 | [dangchu/white.txt](https://raw.githubusercontent.com/qq5460168/dangchu/main/white.txt) |
| ✅ **李文杰白名单** | 中文站点放行 | [adg-rules/white.txt](https://raw.githubusercontent.com/liwenjie119/adg-rules/master/white.txt) |
| ✅ **AdGuard 中文白名单** | 官方中文放行 | [ChineseFilter/allowlist](https://raw.githubusercontent.com/AdguardTeam/AdguardFilters/master/ChineseFilter/sections/allowlist.txt) |
| ✅ **AdGuard 跟踪白名单** | 官方隐私放行 | [SpywareFilter/allowlist](https://raw.githubusercontent.com/AdguardTeam/AdguardFilters/master/SpywareFilter/sections/allowlist.txt) |
| ✅ **BlueSkyXN 白名单** | AdGuard Home 专用 | [AdGuardHomeRules/ok.txt](https://raw.githubusercontent.com/BlueSkyXN/AdGuardHomeRules/master/ok.txt) |
| ✅ **abclq 防误杀白名单** | 红果/抖音正片 CDN 防误杀（裸域名格式，自动转换） | [home-dns-adblock whitelist](https://raw.githubusercontent.com/abclq/home-dns-adblock/refs/heads/main/config/whitelist.txt) |
| 🏠 **本仓库自定义** | 误杀补救（优先级最高） | [data/mod/whitelist.txt](https://raw.githubusercontent.com/xiaolei7172/ADS/master/data/mod/whitelist.txt) |

> 📎 另有 6 条功能域手工摘录自 [lingeringsound/10007_auto 的 Adaway 白名单](https://raw.githubusercontent.com/lingeringsound/10007_auto/master/Adaway_white_list.prop)（DoH 端点 / 推送 HTTPDNS / 小米云 / 百度图床 / 淘宝鉴权 / Adobe 授权）。该源整包 331 条中 289 条已与现有白名单重合，剩余多为 `alimama`、`adnxs`、`ads.tiktok` 等纯广告域，**未作为自动源接入**，仅摘录不接会坏功能的几条。
>
> 📎 UC 浏览器改用 12 条功能子域点名放行（`u3` / `cms` / `ucsec` / `safe` / `wap3` / `kwurl` / `client.video` / `napi` 等），取代原来的 `@@||ucweb.com^` 整域放行——详见下方「精确剔除表」。

### 🎯 精确剔除表：拆掉过宽的那一条，不牵连子域

上游最常见的两种"一锅端"事故：把整个公司主域拦了，或者把整个域名放行了。白名单治不了前者（放行整域会连带废掉几十条子域拦截，副作用比问题本身还大），黑名单也治不了后者。

`data/mod/exclude.txt` 提供了第三条路——**按域名逐条对齐，只删这一条规则**：

| 场景 | 处理 | 效果 |
| :--- | :--- | :--- |
| 上游拦了 `\|bytedance.com^`（整公司主域） | 剔除该条 | 配置下发 `tnc3-*`、设备标识 `ttwid`、小程序容器 `microapp` 恢复；`mssdk`/`pitaya` 等埋点子域照旧拦 |
| 上游拦了 `\|api5-normal-lf.fqnovel.com^`（番茄内容 API） | 剔除整族 `api{3,5}-normal-*` | 番茄小说正文与章节恢复；`log*-applog`/`mon*-misc` 等埋点照旧拦 |
| 上游白名单放了 `@@\|ucweb.com^`（整域） | 同时剔除它与 `\|ucweb.com^` | UC 的 `adtrack`/`ucads`/`union`/`insight`/`utp` 等 18 条广告追踪域恢复拦截；`u3`/`cms`/`ucsec`/`safe` 等功能子域点名放行 |
| 上游拦了 `\|360.cn^` / `\|2345.com^` / `\|wechat.com^`（整公司主域） | 剔除主域三条 | 360 安全卫士、2345 导航、微信国际版恢复解析；同时上游单列的 107 条广告子域（`ad.360.cn`、`pop.360.cn`、`ssp.2345.com` …）从父子域折叠中露出、继续拦截 |
| 上游白名单放了 `@@\|ad.doubleclick.net^` / `@@\|qznovelvod.com^` | 剔除放行侧两条 | Google DART 展示广告、番茄小说阅读页 `vN-reading-ad` 共 7 条恢复拦截 |

> ⚠️ 剔除主域会带来一个连带效应：父子域去重此前把该域下的子域规则折叠了，主域一旦解除，这些子域规则会全部浮出。所以还要复查新露出的子域有没有误伤功能（本轮就因此补放了 `appstore.360.cn` / `jiagu.360.cn` / `mcloud.360.cn`，并把 `wechat.com` 改成整域放行）。

### 🪄 可信通配表：上游通配白名单的 DNS 层落地

上游白名单里 517 条 `@@||v*.douyinvod.com^` 这类**通配放行**在 DNS 层全部静默失效（域名集合只收纯域名），上游黑名单拦掉的节点无人兜底——抖音/B站/番茄的视频节点、腾讯下载 CDN、360 图片 CDN 就是这样被误伤的。

但**不能盲目展开**：实测展开全部 517 条会放行 76 条规则，其中近半是广告/埋点域（`ad.a.yximgs.com` 快手广告集群、`tipsdk.baidu.com` 百度推广追踪、`amdc.alipay.com` 调度埋点都在其中）。所以采用**可信模式表** `data/mod/wildcard_allow.txt`：只有整组确认都是功能/CDN 域的模式（抖音视频节点 `v*.douyinvod.com`、B站播放镜像 `upos-sz-*.bilivideo.com`、腾讯 hash 下载 CDN `*.dlied1.cdntips.net` 等 6 条）才会展开成具体放行条目；混着广告的通配继续忽略，改用白名单点名放行其中的功能域。展开结果写入 allow.txt 的「可信通配展开」独立分区，可溯源、可审计。

`verify-fixes.py` 已接进 CI（`Verify Format Consistency` 步骤），用 48 个用例把 dns / qx / surge / smartdns / dnsmasq / mihomo 六种后缀匹配格式逐个比对，状态必须完全一致，任何格式走偏直接让工作流红掉；hosts 因只能精确匹配单独核对（已补回折叠前的子域，上游未列出的子域仍拦不到），相关用例标 `†`。改 `common.py` 的域名词法后，另有一层纯函数单测：`python -m unittest discover -s tests -v`。

### 🧽 上游脏数据清洗

合并过程中会主动丢弃以下三类"看着像规则、实际有害或无效"的行：

| 类型 | 为例 | 为什么要丢 |
| :--- | :--- | :--- |
| `$badfilter` | `pl.ua^$badfilter` | AdGuard 里用于取消规则，留着等于反向放行广告 |
| 尾点多一个句点 | `advertising.civitai.` | 语法无效，纯废行 |
| 非回环 IP 映射行 | `110.43.121.13 bigota.d.miui.com` | 这是 hosts 加速映射而非拦截，会把域名强行指向某个 IP |

### 🔬 新源接入：先验证，后接入

收到一个新规则源 URL 时，不直接挂进管线，先用**源探针**验证：

```bash
python data/python/probe_source.py <规则源URL>          # 自动分辨黑白名单 + 冲突预演
python data/python/probe_source.py <规则源URL> allow    # 已知是白名单时强制按白名单分析
python data/python/probe_source.py <规则源URL> block    # 已知是黑名单时强制按黑名单分析
```

探针会输出四段报告：

| 环节 | 回答的问题 |
| :--- | :--- |
| 📥 试下载 | 六通道镜像能否拉到？是不是 404/挑战页冒充的规则？ |
| 🧭 黑白判定 | 放行(@@)/拦截(\|\|)/hosts 语法占比 + 文件名关键词，自动判定它是白名单还是黑名单 |
| ⚗️ 冲突预演 | 白名单：将解封现有多少条拦截规则（列出域名明细）；黑名单：与现有规则重叠多少、净新增多少 |
| 📌 接入建议 | 该进 `allow_rules` 还是 `adblock_rules`，后续验证跑哪些脚本 |

**黑白名单怎么分辨？** 核心看语法而非文件名：

| 特征 | 白名单 | 黑名单 |
| :--- | :--- | :--- |
| `@@\|\|domain^` | ✅ 主要成分 | 一般少量（上游自带防误杀） |
| `\|\|domain^` / `0.0.0.0 domain` | 一般少量 | ✅ 主要成分 |
| 裸域名（一行一个域名） | 看文件名：whitelist/allow 等 → 按 `@@\|\|domain^` 转换接入 | 看文件名：adblock/hosts 等 → 作拦截域名接入 |

**正式管线的双保险**（探针之外的自动防线）：

- **下载方向体检**（dl.py）：白名单文件里拦截语法占大头 / 黑名单文件里放行语法占大头，下载阶段当场报警；
- **白名单污染熔断**（merge.py）：若白名单放行移除的拦截规则超过 **8%**（正常水位 ≈2%），判定白名单被投毒或黑白错配，中止发布残缺规则。

</details>


<!-- CHANGELOG:START -->
## 📜 更新历史

> 仅收录**功能性变更**；CI 每日的例行规则更新（`✅ 规则自动更新` 提交）不列出。完整记录见 [Commits](https://github.com/xiaolei7172/ADS/commits/master)。

### 📅 2026-11-01

| 类型 | 变更内容 | 提交 |
| :--- | :--- | :--- |
| 💄 优化 | 表头统计块排版优化：修复 📈 在部分编辑器显示为破损占位框的问题 | [`2fbe718`](https://github.com/xiaolei7172/ADS/commit/2fbe718) |
| 🪄 新机制 | 可信通配表：修复 517 条上游通配白名单在 DNS 层静默失效的问题 | [`ed60a3e`](https://github.com/xiaolei7172/ADS/commit/ed60a3e) |
| 📊 功能 | 三个合并文件表头新增「规则来源统计」：打开规则页第一屏可见各上游条数 | [`100c714`](https://github.com/xiaolei7172/ADS/commit/100c714) |
| 🎬 修复 | 红果短剧 / 番茄小说播放链路修复：16+1 条视频节点从"通配失效"中救回 | [`95e23f8`](https://github.com/xiaolei7172/ADS/commit/95e23f8) |
| 🩺 修复 | 产物体检并修复：3 条大厂主域整杀 + 2 条白名单放行广告 | [`8e8c77a`](https://github.com/xiaolei7172/ADS/commit/8e8c77a) |
| 🎯 规则调优 | 修复三处过宽规则：字节整域拦截 / 番茄内容 API / UC 整域放行 | [`24b629e`](https://github.com/xiaolei7172/ADS/commit/24b629e) |
| 🧹 清理 | 移除冗余源 1007-reward：实测是 all 的严格子集，单独下载贡献 0 条 | [`5bf3caf`](https://github.com/xiaolei7172/ADS/commit/5bf3caf) |
| 📖 文档 | README 白名单段补注：6 条功能域为手工摘录，非自动源 | [`86e3843`](https://github.com/xiaolei7172/ADS/commit/86e3843) |
| 🩹 修复 | 白名单补 6 条功能域：DoH / 推送 HTTPDNS / 小米云 / 百度图床 / 淘宝鉴权 / Adobe 授权 | [`8d7cee8`](https://github.com/xiaolei7172/ADS/commit/8d7cee8) |
| 🎯 规则调优 | 腾讯广告精确拦截：134 条广告域绕过 qq.com 整域放行 | [`3cdff84`](https://github.com/xiaolei7172/ADS/commit/3cdff84) |
| 🔧 修复 | 修复海哥规则源：改用官方 GitHub 镜像 + 补齐国内 App 覆盖 | [`2a6cfff`](https://github.com/xiaolei7172/ADS/commit/2a6cfff) |

<details>
<summary><b>📅 2026-10-29</b> · 1 项变更</summary>

| 类型 | 变更内容 | 提交 |
| :--- | :--- | :--- |
| 🔕 变更 | 关闭自动发布：移除 CI 中的自动 Release 步骤 | [`669cc47`](https://github.com/xiaolei7172/ADS/commit/669cc47) |

</details>

<details>
<summary><b>📅 2026-10-28</b> · 8 项变更</summary>

| 类型 | 变更内容 | 提交 |
| :--- | :--- | :--- |
| 🔧 修复 | 仓库体检修复：探针重复条数统计 + 保障表收录投毒熔断 | [`2ccdb82`](https://github.com/xiaolei7172/ADS/commit/2ccdb82) |
| 🔧 修复 | API 推送行尾归一化（CRLF→LF），修复上一次 API 通道推入的 Windows 行尾 | [`0173282`](https://github.com/xiaolei7172/ADS/commit/0173282) |
| 🔬 新机制 | 新增源探针：先验证后接入 + 黑白名单自动分辨 | [`3817f79`](https://github.com/xiaolei7172/ADS/commit/3817f79) |
| ➕ 新增源 | 接入 abclq Hosts 拦截规则（第 21 路源） | [`147f5a6`](https://github.com/xiaolei7172/ADS/commit/147f5a6) |
| ➕ 新增源 | 接入 abclq 防误杀白名单（第 20 路源）+ 裸域名格式自动转换 | [`76d40ef`](https://github.com/xiaolei7172/ADS/commit/76d40ef) |
| 📋 文档 | 建立完整 Issue 反馈体系（误拦/漏拦/新源/其他四类） | [`8b3d70c`](https://github.com/xiaolei7172/ADS/commit/8b3d70c) |
| 🧽 清理 | 清洗上游脏规则 + 重写上游源表 + workflow 加固 | [`65e5358`](https://github.com/xiaolei7172/ADS/commit/65e5358) |
| 💄 优化 | 项目改名「天影规则聚合 Rules Hub」+ 快速开始补齐客户端下载地址 | [`73634af`](https://github.com/xiaolei7172/ADS/commit/73634af) |

</details>

<details>
<summary><b>📅 2026-10-27</b> · 12 项变更</summary>

| 类型 | 变更内容 | 提交 |
| :--- | :--- | :--- |
| ✨ 新增 | 新增 Clash/Surge 格式 + 下载并发 + README 快速开始教程 | [`cc43ecd`](https://github.com/xiaolei7172/ADS/commit/cc43ecd) |
| 💄 优化 | README 全面美化：徽章行/五大保障/平台适配列/修复公共DNS坏表格/上游来源表格化/页脚 | [`5af6104`](https://github.com/xiaolei7172/ADS/commit/5af6104) |
| ✨ 新增 | 新增规则量趋势图 + 自动 Release + 动态徽章（未配置时自动跳过） | [`8cdefc4`](https://github.com/xiaolei7172/ADS/commit/8cdefc4) |
| 🔗 优化 | 国内加速链接由 ghfast.top（当前不可达）切换为 jsDelivr testingcf（实测 2.3s 可用） | [`5b425fd`](https://github.com/xiaolei7172/ADS/commit/5b425fd) |
| ✨ 新增 | 修复 hosts 死链 + 新增质量自检闸门 + README 源健康度 | [`d3ef609`](https://github.com/xiaolei7172/ADS/commit/d3ef609) |
| 🐛 修复 | 修复大小写绕过去重 + 新增父子域语义去重 | [`0f4a50d`](https://github.com/xiaolei7172/ADS/commit/0f4a50d) |
| 🔍 修复 | 全面复查修复：计数偏差、空分区、仓库卫生、工作流 | [`2652a90`](https://github.com/xiaolei7172/ADS/commit/2652a90) |
| ➕ 新增源 | 新增 3 个规则源：AdGuard DNS Filter 官方 + OISD + BlueSkyXN 白名单 | [`2eb3c03`](https://github.com/xiaolei7172/ADS/commit/2eb3c03) |
| 🌐 格式 | dns.txt 增加规则来源分区标注（与 adblock.txt 一致） | [`8afc02b`](https://github.com/xiaolei7172/ADS/commit/8afc02b) |
| 🧹 清理 | 移除 data/tmp（本地下载缓存误入库，由 API 推送带入） | [`82d446a`](https://github.com/xiaolei7172/ADS/commit/82d446a) |
| 🛑 规则调优 | 红果短剧+番茄小说广告规则 v3（DNS兼容）+ 下载通道修复 | [`99b0761`](https://github.com/xiaolei7172/ADS/commit/99b0761) |
| 🧹 清理 | 仓库历史重建：单提交快照 | [`9495a7f`](https://github.com/xiaolei7172/ADS/commit/9495a7f) |

</details>

<!-- CHANGELOG:END -->

## 🧪 拦截效果在线测试

<div align="center">
  <p><b>🔗 点击以下链接测试广告拦截效果</b></p>

  <a href="https://adblock-tester.com">
    <img src="https://img.shields.io/badge/AdBlock%20Tester-专业测试-blue?style=for-the-badge" alt="AdBlock Tester"/>
  </a>

  <a href="https://blockads.fivefilters.org/">
    <img src="https://img.shields.io/badge/Block%20Ads!-深度测试-green?style=for-the-badge" alt="Block Ads!"/>
  </a>

  <a href="https://adblock.turtlecute.org/">
    <img src="https://img.shields.io/badge/Ad%20Blocker%20Test-全面测试-orange?style=for-the-badge" alt="Ad Blocker Test"/>
  </a>
</div>

---

<div align="center">

**⭐ 如果这个项目对你有帮助，欢迎点个 Star ⭐**

🙏 致敬 8680 大佬 · 各上游规则作者

💬 遇到 **误拦 / 漏拦**？[提交 Issue](https://github.com/xiaolei7172/ADS/issues/new/choose) 反馈，误拦会优先加白名单放行

📄 [MIT License](LICENSE) · 🔄 每日 08:00 自动更新 · [⬆ 返回顶部](#top)

</div>
