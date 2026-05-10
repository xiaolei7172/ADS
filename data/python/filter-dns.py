import os
import datetime

# 自动切换到脚本所在目录（最关键修复）
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# 确保目录存在
os.makedirs('./tmp', exist_ok=True)
os.makedirs('./data/rules', exist_ok=True)

print("正在从 adblock.txt 提取 DNS 规则...")

# 打开原始文件和目标文件
with open('./data/rules/adblock.txt', 'r', encoding='utf-8', errors='ignore') as input_file, \
     open('./data/rules/dns.txt', 'w', encoding='utf-8') as output_file:

    # 逐行读取原始文件内容
    for line in input_file:
        line = line.strip()

        # 提取 ||域名^ 格式的 DNS 规则
        if len(line) >= 2 and line.startswith("||") and line.endswith("^"):
            output_file.write(line + '\n')

print("✅ DNS 规则提取完成！已生成 dns.txt")
