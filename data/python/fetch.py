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
    r"^https://raw\.githubusercontent\.com/([^/]+)/([^/]+)/(.+)$"
)


def split_raw_path(rest):
    """把 raw URL 的 owner/repo 之后那段拆成 (branch, path)。

    兼容两种写法：
      /owner/repo/main/path/to/file        ← 老写法
      /owner/repo/refs/heads/main/path/... ← GitHub 文件页「Raw」按钮现在给的就是这种

    历史 bug：旧正则把 refs/heads/main/... 整段当成"分支名=refs、路径=heads/main/..."，
    于是 API 兜底请求 .../contents/heads/main/...?ref=refs、
    jsDelivr 请求 ...@refs/heads/main/... 全部 404，
    这两个源实际只剩 raw 直连一条通道（raw 一抖就直接判死）。
    """
    if rest.startswith("refs/heads/"):
        rest = rest[len("refs/heads/"):]
    branch, _, path = rest.partition("/")
    return branch, path


def mirror_urls(url):
    """返回 [(url, 是否API模式), ...]，按可靠性排序"""
    attempts = [(url, False)]
    m = RE_RAW_URL.match(url)
    if m:
        owner, repo, rest = m.groups()
        branch, path = split_raw_path(rest)
        if branch and path:
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


# curl 的 SSL/TLS 类错误码：证书链不全、握手失败、协议不匹配等
# 国内小站（尤其自建 nginx）常见证书配置不全，但明文/内容本身是好的，
# 这一类错误值得用 -k 再来一次（规则是纯文本，内容另有 valid_domain 把关）
SSL_ERR_CODES = {35, 51, 58, 59, 60, 77, 83, 90, 91}

# curl 退出码的可读含义（诊断用，比裸数字有用得多）
CURL_MEANING = {
    6: "无法解析主机", 7: "连接失败", 22: "HTTP 错误码(4xx/5xx)",
    28: "超时", 35: "SSL 握手失败", 52: "服务器空响应",
    56: "接收数据失败", 60: "证书验证失败",
}


def _host_of(u):
    """取 URL 的 host 用于错误信息（完整 URL 太长）"""
    m = re.match(r"https?://([^/]+)", u)
    return m.group(1) if m else u[:24]


def _curl_once(u, save_path, is_api, token, insecure=False):
    """执行一次 curl，返回 (退出码, 错误说明)"""
    cmd = [
        "curl", "-fsSL", "--retry", "3", "--retry-delay", "2",
        "--retry-all-errors", "--connect-timeout", "15", "--max-time", "180",
        "-A", "Mozilla/5.0 (compatible; TianYing-Rules/1.0)",
        "-o", save_path, u,
    ]
    if insecure:
        cmd.insert(1, "-k")
    if is_api:
        # API 要拿原始文件内容；有令牌时带上，避免匿名限额（60次/小时）
        cmd[cmd.index("-o"):cmd.index("-o")] = ["-H", "Accept: application/vnd.github.raw"]
        t = token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        if t:
            cmd[cmd.index("-o"):cmd.index("-o")] = ["-H", f"Authorization: Bearer {t}"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=200)
    except subprocess.TimeoutExpired:
        return -1, "下载超时"
    if result.returncode != 0:
        meaning = CURL_MEANING.get(result.returncode, "")
        return result.returncode, f"curl {result.returncode}" + (f"({meaning})" if meaning else "")
    if not os.path.exists(save_path):
        return -2, "未产出文件"
    ok, err = content_ok(save_path)
    if ok:
        return 0, ""
    os.remove(save_path)
    return -3, err


def download_file(url, save_path, token=None):
    """多通道下载 + 体检，任一通道成功即返回 (True, '', used_url)；全败返回 (False, err, '')

    失败时把每个通道的原因都汇总，避免"只留最后一条错误"导致误诊
    （曾经因为这个，把「源站对海外 IP 返回 409」误判成「证书问题」）。
    """
    errors = []
    for u, is_api in mirror_urls(url):
        rc, err = _curl_once(u, save_path, is_api, token)
        if rc == 0:
            return True, "", u
        # SSL 类错误：降级跳过证书校验再试一次（部分国内站点证书链残缺）
        if rc in SSL_ERR_CODES:
            rc2, err2 = _curl_once(u, save_path, is_api, token, insecure=True)
            if rc2 == 0:
                print(f"   ⚠️ {_host_of(u)} 证书校验失败，已跳过校验取回内容（内容仍经语法体检）")
                return True, "", u + " (已跳过证书校验)"
            err = f"{err} / 跳过校验后仍失败: {err2}"
        errors.append(f"{_host_of(u)}: {err}")
    if os.path.exists(save_path):
        os.remove(save_path)
    # 只保留前 3 条通道原因，避免日志爆炸
    return False, "；".join(errors[:3]) if errors else "无可用通道"
