<div align="center">

# 🛸 天影自用规则合集

**⚡ 强力去广告 · 每 12 小时自动更新 · 全平台适配 ⚡**

> 多上游聚合 → 合并去重 → 派生 7 种格式，一条订阅覆盖 AdGuard / AdGuard Home / SmartDNS / Quantumult X / HOSTS

[![CI 状态](https://github.com/xiaolei7172/ADS/actions/workflows/Update-Rules.yml/badge.svg)](https://github.com/xiaolei7172/ADS/actions/workflows/Update-Rules.yml)
[![最近提交](https://img.shields.io/github/last-commit/xiaolei7172/ADS/master?label=%E6%9C%80%E8%BF%91%E6%9B%B4%E6%96%B0&color=success)](https://github.com/xiaolei7172/ADS/commits/master)
[![License](https://img.shields.io/badge/License-MIT-blue)](LICENSE)

[📥 规则订阅](#-规则订阅中心) · [📊 实时统计](#-实时项目统计) · [🚀 快速开始](#-快速开始) · [📚 上游数据源](#-上游规则数据源) · [🧪 拦截效果测试](#-拦截效果在线测试)

---

## 📊 实时项目统计

### 🔮 天影自用广告过滤规则集群


🕒 **更新时间**：2026-10-27 17:20:01（北京时间）


🚫 **广告拦截规则**：277273 条


🌐 **DNS 拦截域名**：245751 个


✅ **白名单放行规则**：6696 条

<!-- DL_STATUS_START -->
✅ **上游源状态**：19/19 全部下载成功
<!-- DL_STATUS_END -->

![规则量趋势](data/stats/trend.svg)

<!-- 🏷️ 动态徽章：① 在 gist.github.com 新建一个 Gist；② 仓库 Settings → Secrets 新建 GIST_SECRET（需 gist 权限的 Token）、Settings → Variables 新建 GIST_ID（填 Gist ID）；③ 取消下一行注释并把 <GIST_ID> 换成实际 ID
![天影规则](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/xiaolei7172/<GIST_ID>/raw/tianying-stats.json)
-->

---

## 🎯 五大保障

| 保障 | 说明 |
| :--- | :--- |
| 🧹 **真实去重** | 精确去重 + 大小写归一 + 父子域语义去重，0 冗余规则 |
| 🛡️ **质量闸门** | 每次发布前自检重复/冗余/计数自洽，不合格自动拦截 |
| 🚧 **发布护栏** | 规则量骤降 >10% 或低于 5 万条即中止发布，绝不带病上线 |
| 🌐 **多源容灾** | GitHub API + 3 个 jsDelivr 子域 + gh-proxy 共 6 通道下载兜底 |
| 📋 **来源可溯** | 每条规则标注所属上游来源，排查误杀一步定位 |

---

## 🚀 快速开始

<details open>
<summary><b>🖥️ AdGuard（Windows / Mac / Android）</b></summary>
<br>

1. 打开 AdGuard → 设置 → **内容拦截**（Windows 为「过滤器」）
2. 点击「添加过滤器」→「使用自定义过滤器」
3. 粘贴订阅链接（国内网络选加速列）：
   `https://testingcf.jsdelivr.net/gh/xiaolei7172/ADS@master/data/rules/adblock.txt`
4. 建议同时启用白名单：`https://testingcf.jsdelivr.net/gh/xiaolei7172/ADS@master/data/rules/allow.txt`

</details>

<details>
<summary><b>🌐 AdGuard Home</b></summary>
<br>

1. 管理后台 → 过滤器 → **DNS 拦截列表** → 添加拦截列表
2. 粘贴：`https://testingcf.jsdelivr.net/gh/xiaolei7172/ADS@master/data/rules/dns.txt`
3. 白名单（自定义过滤规则 → 放行）：`https://testingcf.jsdelivr.net/gh/xiaolei7172/ADS@master/data/rules/allow.txt`

</details>

<details>
<summary><b>📡 OpenWrt（hosts 方式）</b></summary>
<br>

1. 下载 hosts 文件：`https://testingcf.jsdelivr.net/gh/xiaolei7172/ADS@master/data/rules/hosts.txt`
2. 覆盖到 `/etc/hosts` 末尾（或配合 dnsmasq 的 `addn-hosts` 引用）
3. 重启 dnsmasq：`/etc/init.d/dnsmasq restart`

</details>

<details>
<summary><b>🔍 SmartDNS</b></summary>
<br>

1. 编辑 `smartdns.conf`，加入：`conf-file https://testingcf.jsdelivr.net/gh/xiaolei7172/ADS@master/data/rules/smartdns.conf`
   （或下载后 `include` 到主配置）
2. 误杀放行：`conf-file .../data/rules/smartdns-whitelist.conf`
3. 重启服务：`/etc/init.d/smartdns restart`

</details>

<details>
<summary><b>🧩 Clash / Mihomo</b></summary>
<br>

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

<details>
<summary><b>点击查看全部数据来源</b></summary>
<br>

### 🔴 拦截规则

| 来源 | 说明 |
| :---- | :---- |
| 📛 [AdguardTeam 官方基础广告拦截规则](https://raw.githubusercontent.com/AdguardTeam/FiltersRegistry/master/filters/filter_2_Base/filter.txt) | AdGuard 官方基础过滤 |
| 📛 [AdguardTeam 官方中文专属广告规则](https://raw.githubusercontent.com/AdguardTeam/FiltersRegistry/master/filters/filter_224_Chinese/filter.txt) | AdGuard 官方中文过滤 |
| 📛 [EasyPrivacy 隐私跟踪防护规则](https://easylist-downloads.adblockplus.org/easyprivacy.txt) | 隐私跟踪防护 |
| 📛 [sjhgvr OISD精简版广告规则](https://raw.githubusercontent.com/sjhgvr/oisd/main/abp_small.txt) | OISD 精简版 |
| 📛 [TG-Twilight 秋风广告规则](https://raw.githubusercontent.com/TG-Twilight/AWAvenue-Ads-Rule/main/AWAvenue-Ads-Rule.txt) | 秋风规则 |
| 📛 [cjx82630 网页烦扰元素拦截规则](https://raw.githubusercontent.com/cjx82630/cjxlist/master/cjx-annoyance.txt) | 烦扰元素拦截 |
| 📛 [afwfv DD-AD 综合广告拦截规则](https://raw.githubusercontent.com/afwfv/DD-AD/main/rule/DD-AD.txt) | DD-AD 综合 |
| 📛 [消失的DD DNS精简版](https://ghproxy.net/https://raw.githubusercontent.com/afwfv/DD-AD/main/rule/dns.txt) | DD-AD DNS 版 |
| 📛 [damengzhu 广告接口拦截规则](https://raw.githubusercontent.com/damengzhu/banad/main/jiekouAD.txt) | 接口拦截 |
| 📛 [HG 综合广告/弹窗拦截规则](https://raw.githubusercontent.com/2771936993/HG/main/hg1.txt) | 综合弹窗拦截 |
| 📛 [天影自用补充规则](https://raw.githubusercontent.com/xiaolei7172/ADS/refs/heads/master/data/mod/adblock.txt) | 本仓库自定义（优先级最高） |
| 📛 [anti-AD 命中率高、兼容性强](https://anti-ad.net/easylist.txt) | anti-AD 官方 |
| 📛 [当初 综合黑名单](https://raw.githubusercontent.com/qq5460168/dangchu/main/black.txt) | 当初黑名单 |
| 📛 [CHN: AdRules DNS List](https://adguardteam.github.io/HostlistsRegistry/assets/filter_29.txt) | AdRules DNS |
| 📛 [hagezi 轻量低误杀DNS规则](https://ghproxy.net/https://raw.githubusercontent.com/hagezi/dns-blocklists/main/adblock/light.txt) | hagezi 轻量版 |
| 📛 [极客 DNS专用规则](https://www.kbsml.com/wp-content/uploads/adblock/adguard/adg-kall-dns.txt) | 极客 DNS |
| 📛 [AdRules DNS Filter 国内优化](https://raw.gitmirror.com/Cats-Team/dns-filter/main/abp.txt) | Cats-Team 国内优化 |
| 📛 [GitHub加速Hosts](https://raw.hellogithub.com/hosts) | GitHub 加速 |
| 📛 [FCM Hosts 隐私推送优化](https://raw.githubusercontent.com/entr0pia/fcm-hosts/fcm/fcm-hosts) | FCM 推送优化 |
| 📛 [xlxbj_dns 国内短视频APP广告域名](https://www.xlxbk.cn/dns.txt) | 短视频 APP 广告 |
| 📛 [🌸茯苓广告规则](https://raw.githubusercontent.com/Kuroba-Sayuki/FuLing-AdRules/Master/FuLingRules/FuLingBlockList.txt) | 茯苓拦截 |
| 📛 [当初 adhosts 域名拦截](https://raw.githubusercontent.com/qq5460168/dangchu/main/adhosts.txt) | 当初 adhosts |
| 📛 [群主合并规则](https://mirror.ghproxy.com/raw.githubusercontent.com/qq5460168/666/master/rules.txt) | 群主合并 |
| 📛 [知还管理 合并规则](https://get.66a.vip/https://raw.githubusercontent.com/sccheng460/me/master/rules.txt) | 知还合并 |

### 🟢 白名单规则

| 来源 | 说明 |
| :---- | :---- |
| ✅ [个人自用白名单](https://hub.gitmirror.com/https://raw.githubusercontent.com/qq5460168/dangchu/main/white.txt) | 当初白名单 |
| ✅ [冷漠白名单](https://file-git.trli.club/file-hosts/allow/Domains) | 冷漠 |
| ✅ [茯苓允许规则](https://raw.githubusercontent.com/Kuroba-Sayuki/FuLing-AdRules/Master/FuLingRules/FuLingAllowList.txt) | 茯苓放行 |
| ✅ [个人合并白名单](https://mirror.ghproxy.com/raw.githubusercontent.com/qq5460168/666/master/allow.txt) | 群主合并白名单 |
| ✅ [个人自定义白名单规则](https://raw.githubusercontent.com/qq5460168/dangchu/main/white.txt) | 当初白名单 |
| ✅ [天影自用补充白名单规则](https://raw.githubusercontent.com/xiaolei7172/ADS/refs/heads/master/data/mod/whitelist.txt) | 本仓库自定义（优先级最高） |
| ✅ [中文通用白名单](https://raw.githubusercontent.com/liwenjie119/adg-rules/master/white.txt) | 李文杰白名单 |
| ✅ [AdGuard 中文放行白名单](https://raw.githubusercontent.com/AdguardTeam/AdguardFilters/master/ChineseFilter/sections/allowlist.txt) | AdGuard 官方中文 |
| ✅ [隐私拦截放行白名单](https://raw.githubusercontent.com/AdguardTeam/AdguardFilters/master/SpywareFilter/sections/allowlist.txt) | AdGuard 官方隐私 |

</details>


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

📄 [MIT License](LICENSE) · 🔄 每 12 小时自动更新 · [⬆ 返回顶部](#-天影自用规则合集)

</div>
