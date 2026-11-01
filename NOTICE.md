# NOTICE

天影规则聚合（ADS）本身以 MIT 许可发布（见 LICENSE），
但 `data/rules/` 下的**规则内容**来自社区上游，版权归各上游作者，
分别遵循其自身许可。本项目只做格式转换、去重、合并与冲突消解，不改变规则的归属。

## 上游来源与许可

许可一栏为 GitHub API 实测结果（2026-11-01）：

| 来源 | 地址 | 许可 |
| :--- | :--- | :--- |
| 1007-Hosts | https://github.com/lingeringsound/10007_auto | 未声明 |
| anti-AD | https://anti-ad.net/easylist.txt | 未声明（以站内声明为准） |
| AdRules | https://gp.adrules.top/dns.txt | 未声明 |
| AdGuard DNS Filter | https://github.com/AdguardTeam/AdGuardSDNSFilter | **GPL-3.0** |
| OISD | https://oisd.nl | 未声明；官网写明个人使用免费 |
| 个人合并规则 | https://github.com/qq5460168/666 | 未声明 |
| 酷安 @大萌主 | https://github.com/damengzhu/banad | 未声明 |
| 浮风规则 | https://github.com/Thelongdarkorg/ad-rules-merged | 未声明 |
| 海哥规则 | https://github.com/2771936993/HG | 未声明 |
| 秋风广告规则 | https://github.com/TG-Twilight/AWAvenue-Ads-Rule | **GPL-3.0** |
| 乘风规则（通用 / 视频） | https://github.com/xinggsf/Adblock-Plus-Rule | 未声明 |
| 晴雅规则 | https://github.com/rssvcn/qy-Ads-Rule | 未声明 |
| abclq 规则 | https://github.com/abclq/home-dns-adblock | 未声明 |
| 当初白名单 | https://github.com/qq5460168/dangchu | 未声明 |
| 李文杰白名单 | https://github.com/liwenjie119/adg-rules | 未声明 |
| AdGuard 中文 / 跟踪白名单 | https://github.com/AdguardTeam/AdguardFilters | **GPL-3.0** |
| BlueSkyXN 规则 | https://github.com/BlueSkyXN/AdGuardHomeRules | 未声明 |

> 「未声明」不等于可以任意使用——只是上游仓库里没有 LICENSE 文件。
> 商业再分发前请直接联系作者确认，或只挑选许可明确的上游。

## 使用提醒

- **个人使用**没有问题。
- **商业再分发**（尤其内置进商业产品）前，请逐个核对上表，重点看 GPL-3.0 的三项：
  AdGuard DNS Filter、AdGuard Filters、秋风规则——GPL-3.0 对衍生分发有传染性要求。
- 若上游作者希望移除其规则，请提 issue，本项目会从 `data/python/dl.py` 摘除对应源并重新生成。
