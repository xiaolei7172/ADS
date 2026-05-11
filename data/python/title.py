import datetime
import pytz
import glob
import os

# ==========================================
# 仓库根目录（绝对正确）
# ==========================================
if "GITHUB_WORKSPACE" in os.environ:
    REPO_ROOT = os.environ["GITHUB_WORKSPACE"]
else:
    SCRIPT_DIR = os.dirname(os.path.abspath(__file__))
    REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../.."))

# ==========================================
# 北京时间
# ==========================================
tz = pytz.timezone("Asia/Shanghai")
beijing_time = datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

# ==========================================
# 目录
# ==========================================
rules_dir = os.path.join(REPO_ROOT, "data", "rules")

# ==========================================
# 🎯 每个文件独立配置【不同表头 + 不同名称】
# ==========================================
file_config = {
    "adblock.txt": {
        "title": "天影广告拦截规则",
        "desc": "屏蔽全网广告、弹窗、跟踪、恶意域名",
        "comment": "!"
    },
    "dns.txt": {
        "title": "天影 DNS 拦截规则",
        "desc": "DNS 级广告域名屏蔽，支持 AdGuard Home / OpenWrt",
        "comment": "!"
    },
    "allow.txt": {
        "title": "天影白名单规则",
        "desc": "误杀网址放行，保证正常网站正常访问",
        "comment": "!"
    },
    "hosts_merged.txt": {
        "title": "天影 Hosts 拦截规则",
        "desc": "标准 Hosts 格式，屏蔽广告、跟踪、恶意域名",
        "comment": "#"
    },
    "hosts_dns.txt": {
        "title": "天影 Hosts 纯域名规则",
        "desc": "纯域名列表，适用于 DNS 服务器",
        "comment": "#"
    },
    "hosts_adblock.txt": {
        "title": "天影 Hosts 转换 AdBlock 规则",
        "desc": "由 Hosts 转换而来的广告拦截规则",
        "comment": "!"
    }
}

# ==========================================
# 处理所有文件
# ==========================================
for filename, cfg in file_config.items():
    file_path = os.path.join(rules_dir, filename)

    # 读取
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except:
        content = ""

    # 清理旧表头
    lines = content.splitlines()
    while lines:
        first = lines[0].strip()
        if first.startswith(("!", "[", "#")) or first == "":
            lines.pop(0)
        else:
            break
    clean_content = "\n".join(lines).strip()

    # 统计有效行数
    line_count = len([l for l in clean_content.splitlines() if l.strip() and not l.strip().startswith(("!", "#"))])

    # 空值保护
    if line_count < 0:
        line_count = 0

    c = cfg["comment"]

    # ==========================================
    # ✅ 自动生成对应格式表头
    # ==========================================
    header = f"""[{c} TianYing Adblock Project]
{c} ======================================================================
{c} 📌 规则名称：{cfg['title']}
{c} 📝 规则说明：{cfg['desc']}
{c} 🌐 项目地址：https://github.com/xiaolei7172/ADS
{c} ⏰ 更新时间：{beijing_time}（北京时间）
{c} 📊 有效规则：{line_count} 条
{c} 🔄 更新频率：每 12 小时自动更新
{c} Description: ⏰ 更新时间：{beijing_time}（北京时间）｜📊 当前规则总数：{line_count} 条｜
{c} ======================================================================
"""

    # 写入
    final = header + clean_content + "\n"
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(final)
        print(f"✅ {filename} | 规则：{line_count} 条")
    except:
        print(f"❌ 写入失败：{filename}")

print("\n🎉 所有文件表头更新完成（自动适配HOSTS格式）！")
