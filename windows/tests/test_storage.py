"""storage / formatter 中历史截断相关逻辑的纯函数单测。"""
import unittest
from unittest import mock

from feishu_bot import config, formatter, storage


class TestEstimateTokens(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(formatter.estimate_tokens(""), 0)
        self.assertEqual(formatter.estimate_tokens(None), 0)

    def test_cjk_counts(self):
        # 中文应按 ~1.6 token/字估算，10 个汉字应明显 > 1
        self.assertGreater(formatter.estimate_tokens("你好世界这是一个测试"), 1)

    def test_ascii_smaller(self):
        # 同样长度英文估算值应小于中文（英文约 0.3/字符）
        cjk = formatter.estimate_tokens("字" * 20)
        eng = formatter.estimate_tokens("a" * 20)
        self.assertGreater(cjk, eng)


class TestTrimHistory(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(storage.trim_history([]), [])

    def test_within_budget_keeps_order(self):
        hist = [
            {"role": "user", "content": "早"},
            {"role": "assistant", "content": "你好"},
            {"role": "user", "content": "在吗"},
        ]
        with mock.patch.object(config, "HISTORY_TOKEN_BUDGET", 100000), \
             mock.patch.object(config, "HISTORY_MAX", 5000):
            self.assertEqual(storage.trim_history(hist), hist)

    def test_over_budget_keeps_most_recent(self):
        # 每条约 7 token（4 个汉字）；预算 16 仅够保留最近 2 条 -> 丢弃最旧
        hist = [
            {"role": "user", "content": "老消息一"},
            {"role": "assistant", "content": "老消息二"},
            {"role": "user", "content": "新消息三"},
        ]
        with mock.patch.object(config, "HISTORY_TOKEN_BUDGET", 16), \
             mock.patch.object(config, "HISTORY_MAX", 5000):
            kept = storage.trim_history(hist)
        self.assertEqual(
            [m["content"] for m in kept], ["老消息二", "新消息三"]
        )

    def test_message_hard_cap(self):
        hist = [{"role": "user", "content": "x"} for _ in range(10)]
        with mock.patch.object(config, "HISTORY_TOKEN_BUDGET", 100000), \
             mock.patch.object(config, "HISTORY_MAX", 3):
            kept = storage.trim_history(hist)
        self.assertEqual(len(kept), 3)
        # 保留的是最近 3 条（顺序不变）
        self.assertEqual([m["content"] for m in kept], ["x", "x", "x"])

    def test_does_not_mutate_input(self):
        hist = [{"role": "user", "content": "a"}, {"role": "assistant", "content": "b"}]
        with mock.patch.object(config, "HISTORY_TOKEN_BUDGET", 1), \
             mock.patch.object(config, "HISTORY_MAX", 5000):
            kept = storage.trim_history(hist)
        self.assertEqual(len(hist), 2)
        self.assertEqual(len(kept), 1)


if __name__ == "__main__":
    unittest.main()
