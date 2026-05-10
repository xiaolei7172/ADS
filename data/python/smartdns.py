import os

# 自动定位脚本根目录 + 自动创建 tmp
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.makedirs('tmp', exist_ok=True)

def convert_to_smartdns_format(input_file, output_file):
    print("Generating SmartDNS rules...")
    
    try:
        with open(input_file, 'r', encoding='utf-8', errors='ignore') as file:
            lines = file.readlines()
    except:
        print(f"❌ 无法读取文件：{input_file}")
        return

    count = 0
    with open(output_file, 'w', encoding='utf-8') as file:
        # 标准表头
        file.write("# SmartDNS rules for 天影\n")
        file.write("# Homepage: https://github.com/xiaolei7172/ADS\n")
        file.write("# Format: address /domain/#\n\n")
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 匹配 ||域名^ 格式
            if line.startswith("||") and line.endswith("^"):
                domain = line[2:-1].strip()
                if "*" in domain:
                    continue
                if domain and "." in domain:
                    file.write(f"address /{domain}/#\n")
                    count += 1
    
    print(f"✅ 生成完成！共 {count} 条 SmartDNS 规则")

# 路径统一修复（绝对不会错）
input_file_path = "./data/rules/dns.txt"
output_file_path = "./data/rules/smartdns.conf"

# 开始生成
convert_to_smartdns_format(input_file_path, output_file_path)
