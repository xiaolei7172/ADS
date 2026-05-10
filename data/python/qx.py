import os

# 自动定位脚本目录 + 确保 tmp 存在
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.makedirs('tmp', exist_ok=True)

def replace_content_in_file(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8', errors='ignore') as file:
        lines = file.readlines()

    with open(output_file, 'w', encoding='utf-8') as file:
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # 过滤掉带特殊符号的非域名行
            if ':' in line or '.js' in line or '/' in line:
                continue
            # 转换格式 ||domain^ → DOMAIN,domain,reject
            if line.startswith("||") and line.endswith("^"):
                line = line.replace("||", "DOMAIN,").replace("^", ",reject")
            file.write(line + '\n')

def remove_whitelist_domains(input_file, whitelist_file):
    whitelist_domains = []
    try:
        with open(whitelist_file, 'r', encoding='utf-8', errors='ignore') as whitelist:
            for entry in whitelist:
                entry = entry.strip()
                if entry.startswith('@@||') and entry.endswith('^'):
                    dom = entry[4:-1]
                    whitelist_domains.append(dom)
    except:
        pass

    with open(input_file, 'r', encoding='utf-8', errors='ignore') as file:
        lines = file.readlines()

    with open(input_file, 'w', encoding='utf-8') as file:
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # 白名单域名不写入
            if any(dom in line for dom in whitelist_domains):
                continue
            file.write(line + '\n')

# 路径统一修正
input_file_path = "./data/rules/dns.txt"
output_file_path = "./data/rules/qx.list"
whitelist_file_path = "./data/mod/whitelist.txt"

# 执行
replace_content_in_file(input_file_path, output_file_path)
remove_whitelist_domains(output_file_path, whitelist_file_path)

print("✅ Quantumult X 规则生成完成：qx.list")
