# -*- coding: utf-8 -*-
"""
公共下载模块：多通道镜像容灾 + 内容体检。
供 dl.py（正式管线）与 probe_source.py（新源探针）复用，
保证「接入前试下载」与「正式下载」走完全相同的通道与体检逻辑。
"""
import os
import re
import subprocess

# ==============================================
# 内容体检：拦住 404 页、Cloudflare 挑战页、空文件
# 注意：不能拿 "cloudflare" 当关键词——规则正文合法地含它（如
# @@||xx.cloudflare.com^），本文件就误杀过当初白名单。
# 判 HTML 要认结构标签，判挑战页要用完整短语。
# ==============================================
BAD_MARKERS = re.compile(
    r"<!doctype\s|<html[\s>]|</html>|<title>|just a moment|checking your browser"
    r"|enable javascript and cookies|attention required",
    re.IGNORECASE,
)


def content_ok(path):
    try:
        size = os.path.getsize(path)
        if size < 200:
            return False, f"文件过小({size}B)"
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            head = f.read(4096)
        if BAD_MARKERS.search(head):
            return False, "内容是HTML/挑战页，不是规则"
        if head.lstrip().startswith("{"):
            return False, "内容是JSON（API报错），不是规则"
        return True, ""
    except OSError as e:
        return False, str(e)


# ==============================================
# raw.githubusercontent.com → 多通道兜底
# 实测可用性（2026-10-27，国内网络）：raw 直连时断时续，
# API 匿名限额 60次/小时容易耗尽，cdn.jsdelivr.net 主域被重置，
# 但 fastly/testingcf/gcore 三个 jsDelivr 子域和 gh-proxy.com 稳定可用
# ==============================================
RE_RAW_URL = re.compile(
    r"^https://raw\.githubusercontent\.com/([^/]+)/([^/]+)/([^/]+)/(.+)$"
)


def mirror_urls(url):
    """返回 [(url, 是否API模式), ...]，按可靠性排序"""
    attempts = [(url, False)]
    m = RE_RAW_URL.match(url)
    if m:
        owner, repo, branch, path = m.groups()
        # GitHub Contents API（有令牌时限额 1000/小时）
        attempts.append(
            (f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={branch}", True)
        )
        # jsDelivr 三个可用子域（主域 cdn.jsdelivr.net 国内被重置，勿用）
        for cdn in ("fastly.jsdelivr.net", "testingcf.jsdelivr.net", "gcore.jsdelivr.net"):
            attempts.append((f"https://{cdn}/gh/{owner}/{repo}@{branch}/{path}", False))
        # gh-proxy 加速代理
        attempts.append((f"https://gh-proxy.com/{url}", False))
    # http 源补 https 变体（部分网络环境禁明文 http）
    if url.startswith("http://"):
        attempts.append((url.replace("http://", "https://", 1), False))
    return attempts


def download_file(url, save_path, token=None):
    """多通道下载 + 体检，任一通道成功即返回 (True, '', used_url)；全败返回 (False, err, '')"""
    last_err = "未知错误"
    for u, is_api in mirror_urls(url):
        cmd = [
            "curl", "-fsSL", "--retry", "3", "--retry-delay", "2",
            "--retry-all-errors", "--connect-timeout", "15", "--max-time", "180",
            "-A", "Mozilla/5.0 (compatible; TianYing-Rules/1.0)",
            "-o", save_path, u,
        ]
        if is_api:
            # API 要拿原始文件内容；有令牌时带上，避免匿名限额（60次/小时）
            cmd[cmd.index("-o"):cmd.index("-o")] = ["-H", "Accept: application/vnd.github.raw"]
            t = token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
            if t:
                cmd[cmd.index("-o"):cmd.index("-o")] = ["-H", f"Authorization: Bearer {t}"]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=200)
        except subprocess.TimeoutExpired:
            last_err = "下载超时"
            continue
        if result.returncode == 0 and os.path.exists(save_path):
            ok, err = content_ok(save_path)
            if ok:
                return True, "", u
            os.remove(save_path)
            last_err = err
        else:
            last_err = f"curl 退出码 {result.returncode}"
    if os.path.exists(save_path):
        os.remove(save_path)
    return False, last_err, ""
