"""
tests/test_aibox_adapter.py — Unit tests for AI-Box plugin client and adapter.
Mocks HTTP connection to prevent hitting real API endpoints.
"""

import unittest
from unittest.mock import patch, MagicMock
from app.core.contracts import SrtBlock
from modules.translation.plugins.aibox.adapter import AIBoxAdapter
from modules.translation.plugins.aibox.api_client import (
    build_system_prompt, build_user_content, parse_response
)


class TestAiBoxAdapter(unittest.TestCase):
    def test_prompt_builder(self):
        glossary = {"Konoha": "Làng Lá", "Sensei": "Thầy"}
        prompt = build_system_prompt("vietnamese", "anime", glossary)
        
        self.assertIn("Vietnamese", prompt)
        self.assertIn("anime", prompt)
        self.assertIn("GLOSSARY", prompt)
        self.assertIn("Konoha → Làng Lá", prompt)

    def test_user_content_formatter(self):
        blocks = [
            SrtBlock(1, "00:00:01,000 --> 00:00:02,000", "Subtitle content"),
            SrtBlock(2, "00:00:03,000 --> 00:00:04,000", "[Music]"),  # Should be skipped
        ]
        user_content = build_user_content(blocks)
        
        self.assertIn("<INPUT>", user_content)
        self.assertIn("1\n00:00:01,000 --> 00:00:02,000\nSubtitle content", user_content)
        self.assertNotIn("[Music]", user_content)  # verifying SKIP_RE block exclusion

    def test_parse_response_formats(self):
        # 1. Standard Tag format
        resp_tag = """Some thinking content...
<TRANSLATE_TEXT>
1
00:00:01,000 --> 00:00:02,000
Xin chào thế giới

2
00:00:03,000 --> 00:00:04,000
Dịch dòng hai
</TRANSLATE_TEXT>
"""
        res = parse_response(resp_tag)
        self.assertEqual(res.get(1), "Xin chào thế giới")
        self.assertEqual(res.get(2), "Dịch dòng hai")

        # 2. JSON Fallback
        resp_json = """
[
  {"idx": 1, "text": "Hello in JSON"},
  {"idx": 3, "text": "Another line"}
]
"""
        res_json = parse_response(resp_json)
        self.assertEqual(res_json.get(1), "Hello in JSON")
        self.assertEqual(res_json.get(3), "Another line")

        # 3. [N] Fallback
        resp_brackets = """
[1] Brackets format line
[2] Second line here
"""
        res_brackets = parse_response(resp_brackets)
        self.assertEqual(res_brackets.get(1), "Brackets format line")
        self.assertEqual(res_brackets.get(2), "Second line here")

    @patch("modules.translation.plugins.aibox.api_client.call_api")
    def test_adapter_translation(self, mock_call_api):
        # Mock API returns a valid tag-formatted SRT translation response
        mock_call_api.return_value = "<TRANSLATE_TEXT>\n1\n00:00:01,000 --> 00:00:02,000\nXin chào\n</TRANSLATE_TEXT>"
        
        adapter = AIBoxAdapter(api_key="mock_key")
        blocks = [SrtBlock(1, "00:00:01,000 --> 00:00:02,000", "Hello")]
        
        result = adapter.translate_batch(
            blocks=blocks,
            target_lang="vietnamese",
            content_type="auto",
            glossary={},
            model="deepseek-v4-flash"
        )
        
        mock_call_api.assert_called_once()
        self.assertEqual(result.get(1), "Xin chào")


if __name__ == "__main__":
    unittest.main()
