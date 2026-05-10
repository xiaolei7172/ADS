import os
import subprocess
import time
import shutil

# 删除目录下所有的文件
directory = "./data/rules/"

# 确保目录存在并遍历删除其中的文件
if os.path.exists(directory):
    for file_name in os.listdir(directory):
        file_path = os.path.join(directory, file_name)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f"无法删除文件: {file_path}, 错误: {e}")
else:
    print(f"目录 {directory} 不存在")

# 删除目录本身
try:
    shutil.rmtree(directory)
    print(f"成功删除目录 {directory} 及其中的所有文件")
except Exception as e:
    print(f"无法删除目录 {directory}, 错误: {e}")

# 创建临时文件夹
os.makedirs("./tmp/", exist_ok=True)

# 复制补充规则到tmp文件夹
subprocess.run("cp ./data/mod/adblock.txt ./tmp/adblock01.txt", shell=True)
subprocess.run("cp ./data/mod/whitelist.txt ./tmp/allow01.txt", shell=True)


# 拦截规则
adblock = [
"https://raw.githubusercontent.com/AdguardTeam/FiltersRegistry/master/filters/filter_2_Base/filter.txt",  # AdguardTeam 官方基础广告拦截规则
"https://raw.githubusercontent.com/AdguardTeam/FiltersRegistry/master/filters/filter_224_Chinese/filter.txt",  # AdguardTeam 官方中文专属广告规则
"https://easylist-downloads.adblockplus.org/easyprivacy.txt",  # EasyPrivacy 隐私跟踪防护规则
"https://raw.githubusercontent.com/sjhgvr/oisd/main/abp_small.txt",  # sjhgvr OISD精简版广告规则
"https://raw.githubusercontent.com/TG-Twilight/AWAvenue-Ads-Rule/main/AWAvenue-Ads-Rule.txt",  # TG-Twilight 秋风广告规则
#"https://raw.githubusercontent.com/cjx82630/cjxlist/master/cjx-annoyance.txt",  # cjx82630 网页烦扰元素拦截规则
"https://raw.githubusercontent.com/afwfv/DD-AD/main/rule/DD-AD.txt",  # afwfv DD-AD 综合广告拦截规则
#"https://ghproxy.net/https://raw.githubusercontent.com/afwfv/DD-AD/main/rule/dns.txt",  # 消失的DD DNS精简版
"https://raw.githubusercontent.com/damengzhu/banad/main/jiekouAD.txt",  # damengzhu 广告接口拦截规则
"https://raw.githubusercontent.com/2771936993/HG/main/hg1.txt",  # HG 综合广告/弹窗拦截规则
"https://raw.githubusercontent.com/xiaolei7172/ADS/refs/heads/master/data/mod/adblock.txt",  # 天影自用补充规则
"https://anti-ad.net/easylist.txt",  # anti-AD 命中率高、兼容性强
#"https://raw.githubusercontent.com/qq5460168/dangchu/main/black.txt",  # 当初 综合黑名单
#"https://adguardteam.github.io/HostlistsRegistry/assets/filter_29.txt",  # CHN: AdRules DNS List
#"https://ghproxy.net/https://raw.githubusercontent.com/hagezi/dns-blocklists/main/adblock/light.txt",  # hagezi 轻量低误杀DNS规则
#"https://www.kbsml.com/wp-content/uploads/adblock/adguard/adg-kall-dns.txt",  # 极客 DNS专用规则
#"https://raw.gitmirror.com/Cats-Team/dns-filter/main/abp.txt",  # AdRules DNS Filter 国内优化
"https://raw.hellogithub.com/hosts",  # GitHub加速Hosts
#"https://raw.githubusercontent.com/entr0pia/fcm-hosts/fcm/fcm-hosts",  # FCM Hosts 隐私推送优化
"https://www.xlxbk.cn/dns.txt",  # xlxbj_dns 国内短视频APP广告域名
"https://raw.githubusercontent.com/Kuroba-Sayuki/FuLing-AdRules/Master/FuLingRules/FuLingBlockList.txt",  # 🌸茯苓广告规则
#"https://raw.githubusercontent.com/qq5460168/dangchu/main/adhosts.txt",  # 当初 adhosts 域名拦截
"https://mirror.ghproxy.com/raw.githubusercontent.com/qq5460168/666/master/rules.txt",  # 群主合并规则
"https://get.66a.vip/https://raw.githubusercontent.com/sccheng460/me/master/rules.txt"  # 知还管理 合并规则
]

# 白名单规则
allow = [
"https://hub.gitmirror.com/https://raw.githubusercontent.com/qq5460168/dangchu/main/white.txt",  # 个人自用白名单
"https://file-git.trli.club/file-hosts/allow/Domains",  # 冷漠白名单
"https://raw.githubusercontent.com/Kuroba-Sayuki/FuLing-AdRules/Master/FuLingRules/FuLingAllowList.txt",  # 茯苓允许规则
"https://mirror.ghproxy.com/raw.githubusercontent.com/qq5460168/666/master/allow.txt",  # 个人合并白名单
"https://raw.githubusercontent.com/qq5460168/dangchu/main/white.txt",  # 个人自定义白名单规则
"https://raw.githubusercontent.com/xiaolei7172/ADS/refs/heads/master/data/mod/whitelist.txt",  # 自用补充白名单规则
"https://raw.githubusercontent.com/liwenjie119/adg-rules/master/white.txt",  # 中文通用白名单
"https://raw.githubusercontent.com/AdguardTeam/AdguardFilters/master/ChineseFilter/sections/allowlist.txt",  # AdGuard 中文放行白名单
"https://raw.githubusercontent.com/AdguardTeam/AdguardFilters/master/SpywareFilter/sections/allowlist.txt"  # 隐私拦截放行白名单
]

# 下载
for i, adblock_url in enumerate(adblock):
    subprocess.Popen(f"curl -m 60 --retry-delay 2 --retry 5 -k -L -C - -o tmp/adblock{i}.txt --connect-timeout 60 -s {adblock_url} | iconv -t utf-8", shell=True).wait()
    time.sleep(1)

for j, allow_url in enumerate(allow):
    subprocess.Popen(f"curl -m 60 --retry-delay 2 --retry 5 -k -L -C - -o tmp/allow{j}.txt --connect-timeout 60 -s {allow_url} | iconv -t utf-8", shell=True).wait()
    time.sleep(1)
    
print('规则下载完成')


