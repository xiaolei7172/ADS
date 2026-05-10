import datetime
import pytz
import glob
import os

# ==========================================
# 强制定位到【仓库根目录】，全局统一
# ==========================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../.."))
os.chdir(REPO_ROOT)

# ==========================================
# 北京时间
# ==========================================
utc_time = datetime.datetime.now(pytz.timezone('UTC'))
beijing_time = utc_time.astimezone(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')

# ==========================================
# 只处理根目录 data/rules 下的文件
# ==========================================
target_files = {'adblock.txt', 'allow.txt', 'dns.txt'}
file_list = glob.glob(os.path.join(REPO_ROOT, "data", "rules", "*.txt"))

for file_path in file_list:
    filename = os.path.basename(file_path)
    if filename not in target_files:
        continue

    # 读取文件
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except:
        continue

    # 去除旧表头
    lines = content.splitlines()
    while lines and (lines[0].startswith('!') or lines[0].startswith('[') or lines[0].strip() == ''):
        lines.pop(0)
    content = '\n'.join(lines).strip()

    # 统计有效行数
    line_count = len([l for l in content.splitlines() if l.strip() != '' and not l.strip().startswith(('!', '#'))])

    # 新表头
    header = f"""[TianYing Adblock Plus 2.0]
! ======================================================================
! Title: 📌 天影自用规则（每12小时更新一次）
! Homepage:🌐 https://github.com/xiaolei7172/ADS
! Expires: ⏰ 每 12 小时自动更新
! Description: 📝 更新时间：{beijing_time}（北京时间）｜📝 当前规则总数：{line_count} 条｜
! Total count: {line_count}
! Version: {beijing_time}
! ======================================================================
"""

    # 写回【根目录 data/rules 下的原文件】
    final = header + content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(final)

print("✅ 所有规则文件已添加成功表头！")
