"""formatter 模块的单测（纯函数，不依赖飞书）。"""
from __future__ import annotations

import datetime
import unittest

from feishu_bot import formatter


class TestParseContent(unittest.TestCase):
    def test_plain_text(self):
        self.assertEqual(formatter.parse_content({"content": "你好"}), "你好")

    def test_json_text(self):
        self.assertEqual(formatter.parse_content({"content": '{"text":"hi"}'}), "hi")

    def test_empty(self):
        self.assertEqual(formatter.parse_content({}), "")

    def test_invalid_json_returns_raw(self):
        self.assertEqual(formatter.parse_content({"content": "{bad"}), "{bad")


class TestTsToHHMM(unittest.TestCase):
    def test_none(self):
        self.assertEqual(formatter.ts_to_hhmm(None), "?")
        self.assertEqual(formatter.ts_to_hhmm(""), "?")

    def test_valid(self):
        tz = formatter.config.TZ
        dt = datetime.datetime(2026, 9, 9, 23, 0, 0, tzinfo=tz)
        self.assertEqual(formatter.ts_to_hhmm(int(dt.timestamp())), "23:00")

    def test_bad_value(self):
        self.assertEqual(formatter.ts_to_hhmm("not-a-number"), "?")


class TestTimeHelpers(unittest.TestCase):
    def test_now_str(self):
        s = formatter.now_str()
        self.assertIsInstance(s, str)
        self.assertIn("-", s)

    def test_today_str_format(self):
        self.assertRegex(formatter.today_str(), r"^\d{4}-\d{2}-\d{2}$")


if __name__ == "__main__":
    unittest.main()
