# -*- coding: utf-8 -*-
"""语义层单测：不依赖任何产物文件，秒级可跑。

覆盖 common.py（整条管线的唯一语义来源）与 fetch.py 的镜像 URL 解析。
这两处一旦改错，产物不会报错、只会静默变少或某个客户端读不了——
所以用单测钉住，而不是靠跑完 40 分钟管线再肉眼比对。

跑法：python -m unittest discover -s tests -v
"""
import os
import re
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "data", "python"))

from common import (  # noqa: E402
    valid_domain, block_domain, allow_domain, hosts_target,
    is_junk_hosts_line, is_allowed,
)
from fetch import mirror_urls, split_raw_path  # noqa: E402


class TestValidDomain(unittest.TestCase):
    def test_ascii(self):
        for d in ("a.com", "ads.example.com", "x-y.example.co.uk", "a1.b2.cn"):
            self.assertTrue(valid_domain(d), d)

    def test_punycode_tld(self):
        # .中国 = xn--fiqs8s，.рф = xn--p1ai：旧规则只认 [a-z]{2,24}，这些域名被整条丢弃
        for d in ("tencent.xn--fiqs8s", "xn--2qu92fhtxsxexqab.xn--fiqs8s",
                  "example.xn--p1ai", "xn--wxtr9fwyxk9c.xn--io0a7i"):
            self.assertTrue(valid_domain(d), d)

    def test_invalid(self):
        for d in ("", "localhost", "a", "a..com", ".a.com", "a.com.", "-a.com",
                  "a-.com", "a b.com", "a.com/path", "a.com:8080", "||a.com^"):
            self.assertFalse(valid_domain(d), d)

    def test_uppercase_ok(self):
        self.assertTrue(valid_domain("ADS.Example.COM"))


class TestRuleParsing(unittest.TestCase):
    def test_block(self):
        self.assertEqual(block_domain("||ads.example.com^"), "ads.example.com")
        self.assertEqual(block_domain("  ||ADS.Example.com^  "), "ads.example.com")
        self.assertIsNone(block_domain("||ads.example.com/path^"))
        self.assertIsNone(block_domain("0.0.0.0 ads.example.com"))
        self.assertIsNone(block_domain("@@||ads.example.com^"))

    def test_allow(self):
        self.assertEqual(allow_domain("@@||ok.example.com^"), "ok.example.com")
        # 路径级 / $domain= 规则不是纯域名语义，不能进域名集合
        self.assertIsNone(allow_domain("@@||ok.example.com/tag/js$domain=a.com"))
        self.assertIsNone(allow_domain("||ok.example.com^"))

    def test_hosts(self):
        self.assertEqual(hosts_target("0.0.0.0 ads.example.com"), "ads.example.com")
        self.assertEqual(hosts_target("127.0.0.1 ads.example.com"), "ads.example.com")
        self.assertEqual(hosts_target("::1 ads.example.com"), "ads.example.com")
        self.assertIsNone(hosts_target("0.0.0.0 localhost"))

    def test_junk_hosts(self):
        self.assertTrue(is_junk_hosts_line("127.0.0.1 localhost"))
        self.assertTrue(is_junk_hosts_line("0.0.0.0 0.0.0.0"))
        self.assertFalse(is_junk_hosts_line("0.0.0.0 ads.example.com"))


class TestAllowSemantics(unittest.TestCase):
    def test_parent_covers_subdomain(self):
        allows = {"example.com"}
        self.assertTrue(is_allowed("example.com", allows))
        self.assertTrue(is_allowed("a.b.example.com", allows))
        self.assertFalse(is_allowed("example.com.cn", allows))

    def test_exact_only(self):
        self.assertTrue(is_allowed("ads.example.com", {"ads.example.com"}))
        self.assertFalse(is_allowed("x.ads.example.com", {"other.com"}))


class TestMirrorUrls(unittest.TestCase):
    """镜像兜底是 raw 抖动时的唯一活路，断言每个通道的 URL 都拼得对。"""

    URLS = re.findall(r'"url":\s*"([^"]+)"',
                      open(os.path.join(ROOT, "data", "python", "dl.py"),
                           encoding="utf-8").read())

    def test_split_raw_path(self):
        self.assertEqual(split_raw_path("main/dist/hosts.txt"), ("main", "dist/hosts.txt"))
        # GitHub 文件页 Raw 按钮现在给的是 refs/heads/ 形式
        self.assertEqual(split_raw_path("refs/heads/main/dist/hosts.txt"),
                         ("main", "dist/hosts.txt"))
        self.assertEqual(split_raw_path("master/rule.txt"), ("master", "rule.txt"))

    def test_sources_have_mirrors(self):
        self.assertGreaterEqual(len(self.URLS), 15, "dl.py 源列表解析异常")

    def test_every_mirror_url_wellformed(self):
        for url in self.URLS:
            if "raw.githubusercontent.com" not in url:
                continue
            attempts = mirror_urls(url)
            self.assertGreaterEqual(len(attempts), 5, url)
            for u, is_api in attempts:
                if is_api:
                    m = re.search(r"\?ref=([^&]+)$", u)
                    self.assertIsNotNone(m, f"API 兜底缺 ref：{u}")
                    self.assertNotIn("/", m.group(1), f"API ref 含斜杠（分支解析错）：{u}")
                elif "jsdelivr" in u:
                    self.assertIn("@", u, f"jsDelivr 缺分支：{u}")
                    ref = u.split("@", 1)[1].split("/", 1)[0]
                    self.assertTrue(ref and "/" not in ref,
                                    f"jsDelivr 分支解析错（会 404）：{u}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
