import os
import subprocess
import glob
import re
from pathlib import Path

# 切换到脚本所在根目录，保证路径正确
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.chdir('tmp')

print("合并上游拦截规则")
file_list = glob.glob('adblock*.txt')
with open('combined_adblock.txt', 'w', encoding='utf-8') as outfile:
    for file in file_list:
        with open(file, 'r', encoding='utf-8', errors='ignore') as infile:
            outfile.write(infile.read())
            outfile.write('\n')

with open('combined_adblock.txt', 'r', encoding='utf-8') as f:
    content = f.read()
content = re.sub(r'^[!].*$\n', '', content, flags=re.MULTILINE)
content = re.sub(r'^#(?!\s*#).*\n?', '', content, flags=re.MULTILINE)
content = re.sub(r'\n+', '\n', content)  # 多余空行清理

with open('cleaned_adblock.txt', 'w', encoding='utf-8') as f:
    f.write(content)
print("✅ 拦截规则合并完成")

# ==================== 白名单合并 ====================
print("合并上游白名单规则")
allow_file_list = glob.glob('allow*.txt')
with open('combined_allow.txt', 'w', encoding='utf-8') as outfile:
    for file in allow_file_list:
        with open(file, 'r', encoding='utf-8', errors='ignore') as infile:
            outfile.write(infile.read())
            outfile.write('\n')

with open('combined_allow.txt', 'r', encoding='utf-8') as f:
    content = f.read()
content = re.sub(r'^[!].*$\n', '', content, flags=re.MULTILINE)
content = re.sub(r'^#(?!\s*#).*\n?', '', content, flags=re.MULTILINE)
content = re.sub(r'\n+', '\n', content)

with open('cleaned_allow.txt', 'w', encoding='utf-8') as f:
    f.write(content)
print("✅ 白名单规则合并完成")

# ==================== 提取白名单 @@ 开头 ====================
print("过滤白名单规则")
with open('cleaned_allow.txt', 'r', encoding='utf-8') as f:
    allow_lines = f.readlines()

with open('allow.txt', 'w', encoding='utf-8') as f:
    for line in allow_lines:
        line = line.strip()
        if line.startswith('@@'):
            f.write(line + '\n')

# ==================== 移动文件 ====================
current_dir = os.getcwd()
adblock_file = os.path.join(current_dir, 'cleaned_adblock.txt')
allow_file = os.path.join(current_dir, 'allow.txt')

target_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/rules/')
Path(target_dir).mkdir(parents=True, exist_ok=True)

adblock_file_new = os.path.join(target_dir, 'adblock.txt')
allow_file_new = os.path.join(target_dir, 'allow.txt')

os.replace(adblock_file, adblock_file_new)
os.replace(allow_file, allow_file_new)

# ==================== 去重（修复：不会删除白名单） ====================
print("规则去重中")
os.chdir(target_dir)

for file in os.listdir():
    if not os.path.isfile(file):
        continue
    if file not in ['adblock.txt', 'allow.txt', 'dns.txt']:
        continue

    try:
        with open(file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        # 去重 + 排序 + 去空行
        lines = [line.rstrip('\n') for line in lines if line.strip() != '']
        lines = sorted(list(set(lines)))

        with open(file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n')

    except Exception as e:
        print(f"⚠️ 处理 {file} 时出错: {e}")

print("✅ 规则去重完成")
