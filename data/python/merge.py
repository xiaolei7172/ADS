import os
import subprocess
import glob
import re
from pathlib import Path

os.chdir('tmp')

print("合并上游拦截规则")
file_list = glob.glob('adblock*.txt')
with open('combined_adblock.txt', 'w', encoding='utf-8') as outfile:
    for file in file_list:
        # 修复点：指定编码 + 忽略错误
        with open(file, 'r', encoding='utf-8', errors='ignore') as infile:
            outfile.write(infile.read())
            outfile.write('\n')
            
with open('combined_adblock.txt', 'r', encoding='utf-8') as f:
    content = f.read()
content = re.sub(r'^[!].*$\n', '', content, flags=re.MULTILINE)
content = re.sub(r'^#(?!\s*#).*\n?', '', content, flags=re.MULTILINE)

with open('cleaned_adblock.txt', 'w', encoding='utf-8') as f:
    f.write(content)
print("拦截规则合并完成")

print("合并上游白名单规则")
allow_file_list = glob.glob('allow*.txt')
with open('combined_allow.txt', 'w', encoding='utf-8') as outfile:
    for file in allow_file_list:
        # 修复点：指定编码 + 忽略错误
        with open(file, 'r', encoding='utf-8', errors='ignore') as infile:
            outfile.write(infile.read())
            outfile.write('\n')

with open('combined_allow.txt', 'r', encoding='utf-8') as f:
    content = f.read()
content = re.sub(r'^[!].*$\n', '', content, flags=re.MULTILINE)
content = re.sub(r'^#(?!\s*#).*\n?', '', content, flags=re.MULTILINE)

with open('cleaned_allow.txt', 'w', encoding='utf-8') as f:
    f.write(content)
print("白名单规则合并完成")

print("过滤白名单规则")
with open('cleaned_allow.txt', 'r', encoding='utf-8') as f:
    allow_lines = f.readlines()

with open('combined_adblock.txt', 'a', encoding='utf-8') as outfile:
    outfile.writelines(allow_lines)

with open('combined_adblock.txt', 'r', encoding='utf-8') as f:
    lines = f.readlines()
with open('allow.txt', 'w', encoding='utf-8') as f:
    for line in lines:
        if line.startswith('@'):
            f.write(line)
            
current_dir = os.getcwd()
adblock_file = os.path.join(current_dir, 'cleaned_adblock.txt')
allow_file = os.path.join(current_dir, 'allow.txt')
target_dir = os.path.join(current_dir, '.././data/rules/')
Path(target_dir).mkdir(parents=True, exist_ok=True)
adblock_file_new = os.path.join(target_dir, 'adblock.txt')
allow_file_new = os.path.join(target_dir, 'allow.txt')
os.rename(adblock_file, adblock_file_new) 
os.rename(allow_file, allow_file_new) 

print("规则去重中")
os.chdir(".././data/rules/")
files = os.listdir()
result = []
for file in files:
    if not os.path.isdir(file):
        if os.path.splitext(file)[1] == '.txt':
            # 修复点：统一 utf-8 读取，错误自动跳过
            f = open(file, encoding="utf-8", errors="ignore")
            result = list(set(f.readlines()))
            result.sort()
            fo = open('test' + (file), "w", encoding="utf-8")
            fo.writelines(result)
            f.close()
            fo.close()
            os.remove(file)
            os.rename('test' + (file), (file))
print("规则去重完成")
