import os

# ==========================================
# 强制定位到【仓库根目录】，全局统一
# ==========================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../.."))
os.chdir(REPO_ROOT)

# 自动创建目录
os.makedirs(os.path.join(REPO_ROOT, "tmp"), exist_ok=True)

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
        file.write("# SmartDNS rules for 天影\n")
        file.write("# Homepage: https://github.com/xiaolei7172/ADS\n")
        file.write("# Format: address /domain/#\n\n")
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith("||") and line.endswith("^"):
                domain = line[2:-1].strip()
                if "*" in domain:
                    continue
                if domain and "." in domain:
                    file.write(f"address /{domain}/#\n")
                    count += 1
    
    print(f"✅ 生成完成！共 {count} 条 SmartDNS 规则")

# ==========================================
# 强制使用仓库根目录路径
# ==========================================
input_file_path = os.path.join(REPO_ROOT, "data", "rules", "dns.txt")
output_file_path = os.path.join(REPO_ROOT, "data", "rules", "smartdns.conf")

convert_to_smartdns_format(input_file_path, output_file_path)
