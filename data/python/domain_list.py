import os

# ==========================================
# 强制定位到 【仓库根目录】，永远不迷路
# ==========================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../.."))
os.chdir(REPO_ROOT)

# ==========================================
# 强制读写 【根目录/data/rules】
# ==========================================
def extract_domains(input_file, output_file):
    print("正在提取域名列表...")

    try:
        with open(input_file, 'r', encoding='utf-8', errors='ignore') as file:
            lines = file.readlines()
    except:
        print(f"❌ 无法读取文件：{input_file}")
        return

    count = 0
    try:
        with open(output_file, 'w', encoding='utf-8') as file:
            file.write("[Host]\n")
            file.write("# 天影 纯净域名黑名单\n")
            file.write("# Github: https://github.com/xiaolei7172/ADS\n")
            file.write("# 自动提取：只保留纯域名，适配 AdGuard Home / 路由器\n\n")

            for line in lines:
                line = line.strip()
                if line.startswith("||") and line.endswith("^"):
                    domain = line[2:-1].strip()
                    if domain and "." in domain and not " " in domain:
                        file.write(f"{domain}\n")
                        count += 1

        print(f"✅ 提取完成！共提取 {count} 个有效域名")
        print(f"📁 输出路径：{output_file}")

    except Exception as e:
        print(f"❌ 写入失败：{str(e)}")

# ==========================================
# 路径 100% 指向仓库根目录 data/rules
# ==========================================
input_file_path = os.path.join(REPO_ROOT, "data", "rules", "dns.txt")
output_file_path = os.path.join(REPO_ROOT, "data", "rules", "ad-domain.txt")

extract_domains(input_file_path, output_file_path)
