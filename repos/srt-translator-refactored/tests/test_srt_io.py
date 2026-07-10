"""
tests/test_srt_io.py — Unit tests for SRT parser/writer utility.
"""

import os
import tempfile
import unittest
from app.core.contracts import SrtBlock
from app.utils.srt_io import read_srt, write_srt, get_output_path, lang_to_code, _repair


class TestSrtIo(unittest.TestCase):
    def setUp(self):
        # Create temp folder for files
        self.test_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.test_dir.cleanup()

    def test_repair_timestamp(self):
        # Test replacing dot with comma in timestamp
        bad_ts = "00:01:20.123 --> 00:01:23.456"
        fixed = _repair(bad_ts)
        self.assertEqual(fixed, "00:01:20,123 --> 00:01:23,456")

        # Test zero-width space deletion
        text_with_zwsp = "Hello\u200bWorld"
        self.assertEqual(_repair(text_with_zwsp), "HelloWorld")

    def test_read_write_srt(self):
        blocks = [
            SrtBlock(1, "00:00:01,000 --> 00:00:03,500", "Hello World"),
            SrtBlock(2, "00:00:04,100 --> 00:00:06,200", "Second line\nof subtitle"),
        ]

        filepath = os.path.join(self.test_dir.name, "test.srt")
        write_srt(blocks, filepath)

        # Read back and compare
        read_blocks = read_srt(filepath)
        self.assertEqual(len(read_blocks), 2)
        
        self.assertEqual(read_blocks[0].idx, 1)
        self.assertEqual(read_blocks[0].timestamp, "00:00:01,000 --> 00:00:03,500")
        self.assertEqual(read_blocks[0].text, "Hello World")
        
        self.assertEqual(read_blocks[1].idx, 2)
        self.assertEqual(read_blocks[1].timestamp, "00:00:04,100 --> 00:00:06,200")
        self.assertEqual(read_blocks[1].text, "Second line\nof subtitle")

    def test_lang_code_mapping(self):
        self.assertEqual(lang_to_code("Vietnamese"), "VI")
        self.assertEqual(lang_to_code("Indonesian"), "ID")
        self.assertEqual(lang_to_code("Thai"), "TH")
        self.assertEqual(lang_to_code("UnknownLang"), "UN")  # Uppercase first 2 letters fallback

    def test_output_path(self):
        source = os.path.join("C:\\folder\\sub", "sample.srt")
        output = get_output_path(source, "VI")
        # Assert format: <source_dir>/output dịch/<LANG_CODE>/<filename>
        self.assertTrue(output.endswith(os.path.join("output dịch", "VI", "sample.srt")))


if __name__ == "__main__":
    unittest.main()
