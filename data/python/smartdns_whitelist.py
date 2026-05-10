import os
import re

# 自动定位脚本目录 + 自动创建 tmp（解决报错核心）
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.makedirs('tmp', exist_ok=True)

def convert_to_smartdns_whitelist(input_file, output_file):
    print("Generating SmartDNS whitelist rules...")
    
    try:
        with open(input_file, 'r', encoding='utf-8', errors='ignore') as file:
            lines = file.readlines()
    except:
        print(f"❌ 无法读取白名单文件：{input_file}")
        return

    domain_pattern = re.compile(r'@@\|\|([a-zA-Z0-9.-]+)\^')

    count = 0
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write("# SmartDNS whitelist rules for 天影\n")
        file.write("# Homepage: https://github.com/xiaolei7172/ADS\n")
        file.write("# Format: address /domain/-\n\n")

        for line in lines:
            line = line.strip()
            match = domain_pattern.search(line)
            if match:
                domain = match.group(1).strip()
                if domain and "." in domain:
                    file.write(f"address /{domain}/-\n")
                    count += 1

    print(f"✅ 生成完成！共 {count} 条 SmartDNS 白名单规则")

# 路径修复（永不报错）
input_file_path = "./data/rules/allow.txt"
output_file_path = "./data/rules/smartdns-whitelist.conf"

# 执行
convert_to_smartdns_whitelist(input_file_path, output_file_path)
