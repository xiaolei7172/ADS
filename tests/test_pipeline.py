# -*- coding: utf-8 -*-
"""语义层单测：不依赖任何产物文件，秒级可跑。

覆盖 common.py（整条管线的唯一语义来源）与 fetch.py 的镜像 URL 解析。
这两处一旦改错，产物不会报错、只会静默变少或某个客户端读不了——
所以用单测钉住，而不是靠跑完 40 分钟管线再肉眼比对。

跑法：python -m unittest discover -s tests -v
"""
import os
import pathlib
import re
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "data", "python"))
FIXTURES = os.path.join(ROOT, "tests", "fixtures")

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

    @classmethod
    def setUpClass(cls):
        # 放在 setUpClass 而不是类体：URLS 若在 import 阶段求值，dl.py 一旦换成
        # 单引号 / 改成从 YAML 读，整个测试文件会在 import 时就崩，
        # 报错指向"测试文件第 N 行"而不是"URL 解析失败"。
        src = pathlib.Path(ROOT, "data", "python", "dl.py").read_text(encoding="utf-8")
        cls.URLS = re.findall(r'"url":\s*"([^"]+)"', src)

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


class TestFormats(unittest.TestCase):
    """格式层自检：写进去的必须能原样读回来，表头不能被误认成规则。"""

    def setUp(self):
        from formats import FORMATS
        self.formats = FORMATS

    def test_write_read_roundtrip(self):
        for f in self.formats:
            line = f.render("ads.example.com").rstrip("\n")
            self.assertEqual(f.read(line), "ads.example.com",
                             f"{f.name} 写入后读不回同一个域名：{line!r}")

    def test_header_not_mistaken_for_rule(self):
        for f in self.formats:
            for h in f.header_lines(["a.com"]):
                if h.startswith(("#", "!", "[", "payload")):
                    self.assertIsNone(f.read(h), f"{f.name} 把表头当成规则：{h!r}")

    def test_expected_formats_present(self):
        names = {f.name for f in self.formats}
        for n in ("qx.list", "surge.list", "mihomo.yaml", "smartdns.conf",
                  "dnsmasq.conf", "ad-domain.txt", "hosts.txt", "smartdns-whitelist.conf"):
            self.assertIn(n, names)

    def test_only_hosts_is_exact_match(self):
        exact = [f.name for f in self.formats if not f.suffix]
        self.assertEqual(exact, ["hosts.txt"])


class TestGoldenFiles(unittest.TestCase):
    """产物字节锁 —— 这一层是"第二双眼睛"。

    为什么非要有：生成器用 fmt.render 写文件、校验器用 fmt.read 读文件，
    两边都错（比如 read_dnsmasq 少写了 `=`）会一致地错，verify-fixes 依然全绿、
    test_write_read_roundtrip 也依然通过，客户端却读不了。
    golden 里的字节是"上一次发布出去、被真实客户端读过"的那一版
    （tests/fixtures/expected/ 的正文行已逐字节对齐 data/rules/ 的线上产物），
    所以它测的是"产物有没有变"，而不是"代码自己认为对不对"。

    新增格式时必须同时补 expected/<name>，否则 test_every_format_has_golden 会红。
    """

    @classmethod
    def setUpClass(cls):
        from formats import FORMATS
        from pipeline import render_text
        cls.formats = FORMATS
        cls.render_text = staticmethod(render_text)
        with open(os.path.join(FIXTURES, "input.txt"), encoding="utf-8") as f:
            cls.domains = [ln.strip() for ln in f
                           if ln.strip() and not ln.startswith("#")]

    def test_every_format_has_golden(self):
        have = {p.name for p in pathlib.Path(FIXTURES, "expected").iterdir()}
        want = {f.name for f in self.formats}
        self.assertEqual(want - have, set(), "这些格式缺 golden 文件")
        self.assertEqual(have - want, set(), "这些 golden 已没有对应格式，删掉它")

    def test_golden_bytes(self):
        for fmt in self.formats:
            want = pathlib.Path(FIXTURES, "expected", fmt.name).read_text(encoding="utf-8")
            got = self.render_text(fmt, self.domains)
            if got == want:
                continue
            # 找出第一处不同，报错时直接指出来，不用人肉 diff
            g, w = got.splitlines(), want.splitlines()
            idx = next((i for i in range(min(len(g), len(w))) if g[i] != w[i]),
                       min(len(g), len(w)))
            raise AssertionError(
                f"{fmt.name} 产物字节变了（第 {idx + 1} 行）\n"
                f"  现在写：{g[idx] if idx < len(g) else '<文件提前结束>'!r}\n"
                f"  golden：{w[idx] if idx < len(w) else '<文件提前结束>'!r}\n"
                f"  若这是有意的格式变更，同步更新 tests/fixtures/expected/{fmt.name}，"
                f"并确认 data/python/formats.py 的 read() 也一起改了。")

    def test_hosts_header_has_no_timestamp(self):
        """hosts 表头不能带时间戳：带了就等于每天重写 7 MB 文件，
        `git diff --cached --quiet` 的"无变化不提交"永远走不到。"""
        hosts = next(f for f in self.formats if f.name == "hosts.txt")
        first = self.render_text(hosts, self.domains)
        self.assertNotIn("⏰ 更新时间", first)
        self.assertIn("内容指纹", first)
        self.assertEqual(first, self.render_text(hosts, self.domains),
                         "同样输入两次渲染必须完全一致")
        self.assertNotEqual(first, self.render_text(hosts, self.domains[:-1]),
                            "域名集变了，内容指纹必须跟着变")


if __name__ == "__main__":
    unittest.main(verbosity=2)
