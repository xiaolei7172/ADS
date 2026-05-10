import os

# ==========================================
# 强制定位到【仓库根目录】全局统一
# ==========================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../.."))
os.chdir(REPO_ROOT)

# 自动创建目录
os.makedirs(os.path.join(REPO_ROOT, "tmp"), exist_ok=True)

def replace_content_in_file(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8', errors='ignore') as file:
        lines = file.readlines()

    with open(output_file, 'w', encoding='utf-8') as file:
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if ':' in line or '.js' in line or '/' in line:
                continue
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
            if any(dom in line for dom in whitelist_domains):
                continue
            file.write(line + '\n')

# ==========================================
# 强制使用仓库根目录路径
# ==========================================
input_file_path = os.path.join(REPO_ROOT, "data", "rules", "dns.txt")
output_file_path = os.path.join(REPO_ROOT, "data", "rules", "qx.list")
whitelist_file_path = os.path.join(REPO_ROOT, "data", "mod", "whitelist.txt")

# 执行
replace_content_in_file(input_file_path, output_file_path)
remove_whitelist_domains(output_file_path, whitelist_file_path)

print("✅ Quantumult X 规则生成完成：qx.list")
