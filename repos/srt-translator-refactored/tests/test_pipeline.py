"""
tests/test_pipeline.py — Unit tests for JSON checkpointing and pipeline structures.
"""

import os
import tempfile
import unittest
from app.core.pipeline import get_checkpoint_path, load_checkpoint, save_checkpoint, clear_checkpoint


class TestPipeline(unittest.TestCase):
    def test_checkpoint_naming(self):
        # Different paths must result in different checkpoint filenames
        path1 = os.path.abspath("C:/folder1/sub/sub2/file.srt")
        path2 = os.path.abspath("C:/folder2/sub/sub2/file.srt")
        
        cp_path1 = get_checkpoint_path(path1)
        cp_path2 = get_checkpoint_path(path2)
        
        self.assertNotEqual(cp_path1, cp_path2)
        self.assertTrue(cp_path1.endswith(".json"))
        self.assertTrue(cp_path2.endswith(".json"))

    def test_checkpoint_save_load_clear(self):
        filepath = os.path.abspath("C:/mock_project/subtitle.srt")
        data = {
            1: "Hello World",
            2: "This is a refactored app.",
            15: "Final block test."
        }
        
        # Ensure no residual checkpoint exists
        clear_checkpoint(filepath)
        
        # Load when empty
        self.assertEqual(load_checkpoint(filepath), {})
        
        # Save
        save_checkpoint(filepath, data)
        
        # Load and verify
        loaded = load_checkpoint(filepath)
        self.assertEqual(len(loaded), 3)
        self.assertEqual(loaded[1], "Hello World")
        self.assertEqual(loaded[2], "This is a refactored app.")
        self.assertEqual(loaded[15], "Final block test.")
        
        # Clear
        clear_checkpoint(filepath)
        
        # Verify empty
        self.assertEqual(load_checkpoint(filepath), {})


if __name__ == "__main__":
    unittest.main()
