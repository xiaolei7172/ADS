import datetime
import pytz
import os

# ==========================================
# 仓库根目录
# ==========================================
if "GITHUB_WORKSPACE" in os.environ:
    REPO_ROOT = os.environ["GITHUB_WORKSPACE"]
else:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
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
# 仅保留 3 个核心规则
# ==========================================
file_config = {
    "adblock.txt": {
        "title": "天影广告拦截规则",
        "desc": "屏蔽全网广告、弹窗、跟踪、恶意域名",
        "comment": "!"
    },
    "dns.txt": {
        "title": "天影DNS拦截规则",
        "desc": "DNS级广告域名屏蔽，支持AdGuard Home / OpenWrt",
        "comment": "!"
    },
    "allow.txt": {
        "title": "天影白名单规则",
        "desc": "误杀网址放行，保证正常网站正常访问",
        "comment": "!"
    }
}

# ==========================================
# 【精准计数函数】修复完成！
# ==========================================
def count_valid_lines(content):
    count = 0
    for line in content.splitlines():
        line = line.strip()
        # 跳过：空行、!注释、#注释
        if line and not line.startswith(("!", "#")):
            count += 1
    return max(count, 0)

# ==========================================
# 处理文件
# ==========================================
for filename, cfg in file_config.items():
    file_path = os.path.join(rules_dir, filename)

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

    # ======================
    # ✅ 这里现在 100% 精准
    # ======================
    line_count = count_valid_lines(clean_content)

    c = cfg["comment"]

    header = f"""[TianYing Adblock Project]
{c} ======================================================================
{c} 📌 规则名称：{cfg['title']}
{c} 📝 规则说明：{cfg['desc']}
{c} 🌐 项目地址：https://github.com/xiaolei7172/ADS
{c} ⏰ 更新时间：{beijing_time}（北京时间）
{c} 📊 有效规则：{line_count} 条
{c} 🔄 更新频率：每12小时自动更新
{c} ======================================================================
{c} Title: 📌 {cfg['title']} 📌
{c} Description: ⏰ 更新时间 {beijing_time} | ✅ 有效规则 {line_count} 条
{c} ======================================================================
"""

    final = header + clean_content + "\n"
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(final)
        print(f"✅ {filename} | 规则：{line_count} 条")
    except:
        print(f"❌ 写入失败：{filename}")

print("\n🎉 所有文件表头更新完成！")
