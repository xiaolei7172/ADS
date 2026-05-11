import os
import re

# ==========================
# 路径配置
# ==========================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TMP_DIR = os.path.join(BASE_DIR, "tmp")
OUT_DIR = os.path.join(BASE_DIR, "data", "rules")
os.makedirs(OUT_DIR, exist_ok=True)

# ==========================
# 排除列表
# ==========================
EXCLUDE_DOMAINS = {
    "localhost", "localhost.localdomain", "local", "ip6-localhost",
    "ip6-loopback", "broadcasthost", "ip6-allnodes", "ip6-allrouters"
}

# ==========================
# 提取来源信息
# ==========================
def get_source_info(file_path):
    source_name = "未知HOSTS来源"
    source_url = "未知地址"
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for _ in range(20):
                line = f.readline().strip()
                if line.startswith("! 📋 规则来源："):
                    source_name = line.replace("! 📋 规则来源：", "").strip()
                if line.startswith("! 🔗 原始地址："):
                    source_url = line.replace("! 🔗 原始地址：", "").strip()
    except:
        pass
    return source_name, source_url

# ==========================
# 提取HOSTS域名
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
                if domain in EXCLUDE_DOMAINS or "." not in domain:
                    continue
                if domain.replace(".", "").isdigit():
                    continue
                domains.add(domain)
    except:
        pass
    return domains

# ==========================
# 合并（标准 # 注释）
# ==========================
final_lines = []
global_domains = set()

files = sorted(os.listdir(TMP_DIR))
for fname in files:
    path = os.path.join(TMP_DIR, fname)
    if not os.path.isfile(path):
        continue

    s_name, s_url = get_source_info(path)
    domains = extract_hosts_domains(path)
    new_domains = domains - global_domains

    if new_domains:
        # 标准 Hosts 注释，全部用 #
        final_lines.append("# ==============================================")
        final_lines.append(f"# 📋 HOSTS来源：{s_name}")
        final_lines.append(f"# 🔗 原始地址：{s_url}")
        final_lines.append("# ==============================================")
        for d in sorted(new_domains):
            final_lines.append(f"0.0.0.0 {d}")
            global_domains.add(d)
        print(f"✅ HOSTS：{s_name} | 新增 {len(new_domains)} 条")

# ==========================
# 输出（不冲突、标准格式）
# ==========================
# 1. 标准格式带分段来源
with open(os.path.join(OUT_DIR, "hosts_merged.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(final_lines) + "\n")

# 2. HOSTS 专用纯域名
with open(os.path.join(OUT_DIR, "hosts_dns.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(sorted(global_domains)) + "\n")

# 3. HOSTS 专用 AdBlock 规则
ad_lines = [f"||{d}^" for d in sorted(global_domains)]
with open(os.path.join(OUT_DIR, "hosts_adblock.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(ad_lines) + "\n")

# ==========================
# 完成
# ==========================
print("\n🎉 标准格式 HOSTS 合并完成！")
print(f"📦 总域名数量：{len(global_domains)}")
