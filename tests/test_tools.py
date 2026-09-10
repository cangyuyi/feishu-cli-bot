"""tools 模块的单测：用 mock 隔离 lark-cli，验证解析/分支/写开关/注册表对齐。"""
from __future__ import annotations

import os
import unittest
from unittest import mock

from feishu_bot import schemas
from feishu_bot import tools


class TestAgenda(unittest.TestCase):
    def test_ok_parses_events(self):
        fake = {"ok": True, "data": [
            {"start_time": {"timestamp": 1700000000},
             "end_time": {"timestamp": 1700003600},
             "summary": "周会"}
        ]}
        with mock.patch.object(tools.cli, "run", return_value=fake):
            out = tools.t_agenda("2026-09-09")
        self.assertIn("周会", out)
        self.assertIn("1 项", out)

    def test_empty(self):
        with mock.patch.object(tools.cli, "run", return_value={"ok": True, "data": []}):
            out = tools.t_agenda()
        self.assertIn("没有日程", out)

    def test_fail(self):
        with mock.patch.object(tools.cli, "run", return_value={"ok": False, "error": {"message": "boom"}}):
            out = tools.t_agenda()
        self.assertIn("失败", out)


class TestWriteGuard(unittest.TestCase):
    def test_create_task_blocked_when_write_off(self):
        with mock.patch.dict(os.environ, {"FEISHU_BOT_ALLOW_WRITE": "0"}):
            out = tools.t_create_task("写周报")
        self.assertIn("关闭", out)

    def test_send_blocked_when_write_off(self):
        with mock.patch.dict(os.environ, {"FEISHU_BOT_ALLOW_WRITE": "0"}):
            out = tools.t_send_to("oc_x", "hi")
        self.assertIn("关闭", out)


class TestRenderMessages(unittest.TestCase):
    def test_mine_filter_marks_sender(self):
        scan = [("群A", [
            {"sender": {"id": "me", "name": "我"},
             "create_time": "2026-09-09T10:00:00+08:00",
             "content": '{"text":"hi"}'},
            {"sender": {"id": "other", "name": "小王"},
             "create_time": "2026-09-09T10:05:00+08:00",
             "content": '{"text":"在吗"}'},
        ])]
        with mock.patch.object(tools, "get_my_open_id", return_value="me"):
            out_mine = tools.render_messages(scan, "2026-09-09", whose="mine")
            out_all = tools.render_messages(scan, "2026-09-09", whose="all")
        self.assertIn("[我]", out_mine)
        self.assertNotIn("小王", out_mine)
        self.assertIn("小王", out_all)
        self.assertIn("共 2 条", out_all)


class TestToolRegistryConsistency(unittest.TestCase):
    def test_impl_keys_match_schema_names(self):
        schema_names = {s["function"]["name"] for s in schemas.TOOL_SCHEMA}
        impl_names = set(tools.TOOL_IMPL)
        self.assertEqual(impl_names, schema_names)
        self.assertEqual(len(impl_names), 18)

    def test_dispatch_roundtrip(self):
        # get_tasks 不应触发网络（mock 兜底抛错以验证逻辑短路）
        with mock.patch.object(tools.cli, "run", side_effect=AssertionError("不应调用")):
            # create_task 在写关闭时不调 cli
            with mock.patch.dict(os.environ, {"FEISHU_BOT_ALLOW_WRITE": "0"}):
                out = tools.TOOL_IMPL["create_task"]({"summary": "x"})
        self.assertIn("关闭", out)


class TestCreateBitable(unittest.TestCase):
    def test_ok_returns_token_and_url(self):
        fake = {"ok": True, "data": {"app_token": "appXXXX", "url": "https://feishu.cn/base/appXXXX"}}
        with mock.patch.object(tools.cli, "run", return_value=fake):
            out = tools.t_create_bitable("项目表")
        self.assertIn("已创建多维表格", out)
        self.assertIn("appXXXX", out)

    def test_workspace_from_env(self):
        fake = {"ok": True, "data": {"app": {"app_token": "appY"}}}
        with mock.patch.object(tools.cli, "run", return_value=fake) as m, \
             mock.patch.dict(os.environ, {"FEISHU_BOT_WORKSPACE_TOKEN": "wsZ"}):
            tools.t_create_bitable("表", workspace_token=None)
        sent = m.call_args.args[0]
        self.assertIn("/open-apis/bitable/v1/apps", sent)
        data_arg = sent[sent.index("--data") + 1]
        self.assertIn("wsZ", data_arg)

    def test_write_off(self):
        with mock.patch.dict(os.environ, {"FEISHU_BOT_ALLOW_WRITE": "0"}):
            out = tools.t_create_bitable("表")
        self.assertIn("关闭", out)

    def test_fail(self):
        with mock.patch.object(tools.cli, "run", return_value={"ok": False, "error": {"message": "no auth"}}):
            out = tools.t_create_bitable("表")
        self.assertIn("失败", out)


class TestCreateSpreadsheet(unittest.TestCase):
    def test_ok_returns_token_and_url(self):
        fake = {"ok": True, "data": {"spreadsheetToken": "shtXXXX"}}
        with mock.patch.object(tools.cli, "run", return_value=fake):
            out = tools.t_create_spreadsheet("报表")
        self.assertIn("已创建电子表格", out)
        self.assertIn("shtXXXX", out)

    def test_write_off(self):
        with mock.patch.dict(os.environ, {"FEISHU_BOT_ALLOW_WRITE": "0"}):
            out = tools.t_create_spreadsheet("报表")
        self.assertIn("关闭", out)


if __name__ == "__main__":
    unittest.main()
