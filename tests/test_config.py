"""config 模块的单测：env 文件加载 / 写开关 / 模型配置判定。"""
import os
import tempfile
import unittest
from unittest import mock

import feishu_bot.config as config


class TestLoadEnvFile(unittest.TestCase):
    def test_loads_values_into_environ(self):
        with tempfile.NamedTemporaryFile("w", suffix=".env", delete=False) as f:
            f.write("FEISHU_BOT_INTERVAL=7\n")
            f.write("# comment\n")
            f.write('FEISHU_BOT_LLM_KEY="sk-x"\n')
            path = f.name
        saved = {k: os.environ.pop(k, None) for k in ("FEISHU_BOT_INTERVAL", "FEISHU_BOT_LLM_KEY")}
        try:
            with mock.patch.object(config, "ENV_FILE", path):
                config.load_env_file()
            self.assertEqual(os.environ.get("FEISHU_BOT_INTERVAL"), "7")
            self.assertEqual(os.environ.get("FEISHU_BOT_LLM_KEY"), "sk-x")
        finally:
            os.unlink(path)
            for k, v in saved.items():
                os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)

    def test_missing_file_is_noop(self):
        with mock.patch.object(config, "ENV_FILE", "/nonexistent/path/.env"):
            # 不应抛异常
            config.load_env_file()


class TestAllowWrite(unittest.TestCase):
    def test_default_true(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("FEISHU_BOT_ALLOW_WRITE", None)
            self.assertTrue(config.allow_write())

    def test_zero_is_false(self):
        with mock.patch.dict(os.environ, {"FEISHU_BOT_ALLOW_WRITE": "0"}):
            self.assertFalse(config.allow_write())


class TestLlmConfigured(unittest.TestCase):
    def test_both_required(self):
        saved = {k: os.environ.pop(k, None) for k in ("FEISHU_BOT_LLM_BASE_URL", "FEISHU_BOT_LLM_KEY")}
        try:
            self.assertFalse(config.llm_configured())
            os.environ["FEISHU_BOT_LLM_BASE_URL"] = "u"
            self.assertFalse(config.llm_configured())
            os.environ["FEISHU_BOT_LLM_KEY"] = "k"
            self.assertTrue(config.llm_configured())
        finally:
            for k, v in saved.items():
                os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)


if __name__ == "__main__":
    unittest.main()
