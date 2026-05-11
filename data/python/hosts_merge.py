import os
import re

# ==========================
# 路径配置（和你项目完全匹配）
# ==========================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TMP_DIR = os.path.join(BASE_DIR, "tmp")
OUT_DIR = os.path.join(BASE_DIR, "data", "rules")

os.makedirs(OUT_DIR, exist_ok=True)

# ==========================
# 排除列表（不会被收录）
# ==========================
EXCLUDE_DOMAINS = {
    "localhost", "localhost.localdomain", "local", "ip6-localhost",
    "ip6-loopback", "broadcasthost", "ip6-allnodes", "ip6-allrouters"
}

# ==========================
# 核心：清洗 Hosts 提取域名
# ==========================
def extract_hosts_domains(file_path):
    domains = set()
    pattern = re.compile(r"^\s*(0\.0\.0\.0|127\.0\.0\.1)\s+([^\s#]+)", re.IGNORECASE)
    
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith(("#", "!", "[", "//")):
                    continue

                match = pattern.match(line)
                if not match:
                    continue

                domain = match.group(2).strip().lower()
                if domain in EXCLUDE_DOMAINS:
                    continue
                if "." not in domain:
                    continue
                if domain.replace(".", "").isdigit():
                    continue

                domains.add(domain)
    except:
        pass
    return domains

# ==========================
# 扫描 tmp 目录所有文件
# ==========================
all_domains = set()

for filename in os.listdir(TMP_DIR):
    path = os.path.join(TMP_DIR, filename)
    if os.path.isfile(path):
        print(f"🔍 扫描：{filename}")
        domains = extract_hosts_domains(path)
        all_domains.update(domains)

# ==========================
# 排序
# ==========================
sorted_domains = sorted(all_domains)
total = len(sorted_domains)

# ==========================
# 输出 1：纯域名（dns.txt）
# ==========================
dns_path = os.path.join(OUT_DIR, "dns.txt")
with open(dns_path, "w", encoding="utf-8") as f:
    f.write("\n".join(sorted_domains))

# ==========================
# 输出 2：AdBlock 格式（adhosts.txt）
# ==========================
adblock_path = os.path.join(OUT_DIR, "adhosts.txt")
adblock_lines = [f"||{d}^" for d in sorted_domains]
with open(adblock_path, "w", encoding="utf-8") as f:
    f.write("\n".join(adblock_lines))

# ==========================
# 输出 3：标准合并 Hosts（hosts_merged.txt）
# ==========================
hosts_path = os.path.join(OUT_DIR, "hosts_merged.txt")
hosts_lines = [f"0.0.0.0 {d}" for d in sorted_domains]
with open(hosts_path, "w", encoding="utf-8") as f:
    f.write("\n".join(hosts_lines))

# ==========================
# 完成
# ==========================
print(f"\n✅ Hosts 智能合并完成！")
print(f"📦 有效域名总数：{total}")
print(f"📁 输出到：{OUT_DIR}")
