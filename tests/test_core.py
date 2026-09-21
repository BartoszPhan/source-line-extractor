import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from source_line_extractor import SourceLineExtractor
from source_line_extractor.core import ExtractedLine


class SourceLineExtractorTests(unittest.TestCase):
    def _make_extractor(self, content: str) -> SourceLineExtractor:
        temp_dir = TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        path = Path(temp_dir.name) / "sample.py"
        path.write_text(content, encoding="utf-8")
        return SourceLineExtractor(path)

    def test_extracts_single_line_without_context(self):
        extractor = self._make_extractor("one\ntwo\nthree\n")
        result = extractor.extract(2, 2)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], ExtractedLine(2, "two", True))

    def test_extracts_inclusive_range(self):
        extractor = self._make_extractor("one\ntwo\nthree\nfour\n")
        result = extractor.extract(2, 3)

        self.assertEqual(
            result,
            [
                ExtractedLine(2, "two", True),
                ExtractedLine(3, "three", True),
            ],
        )

    def test_context_adds_surrounding_lines_and_marks_them(self):
        extractor = self._make_extractor("one\ntwo\nthree\nfour\nfive\n")
        result = extractor.extract(3, 3, context=1)

        self.assertEqual(
            result,
            [
                ExtractedLine(2, "two", False),
                ExtractedLine(3, "three", True),
                ExtractedLine(4, "four", False),
            ],
        )

    def test_context_is_clamped_at_file_start(self):
        extractor = self._make_extractor("one\ntwo\nthree\n")
        result = extractor.extract(1, 1, context=2)

        self.assertEqual(
            result,
            [
                ExtractedLine(1, "one", True),
                ExtractedLine(2, "two", False),
                ExtractedLine(3, "three", False),
            ],
        )

    def test_context_is_clamped_at_file_end(self):
        extractor = self._make_extractor("one\ntwo\nthree\n")
        result = extractor.extract(3, 3, context=2)

        self.assertEqual(
            result,
            [
                ExtractedLine(1, "one", False),
                ExtractedLine(2, "two", False),
                ExtractedLine(3, "three", True),
            ],
        )

    def test_empty_file_returns_empty_list(self):
        extractor = self._make_extractor("")
        result = extractor.extract(1, 1)

        self.assertEqual(result, [])

    def test_range_completely_before_file_returns_empty(self):
        extractor = self._make_extractor("one\ntwo\n")
        with self.assertRaises(ValueError):
            extractor.extract(-2, -1)

    def test_range_completely_after_file_returns_empty(self):
        extractor = self._make_extractor("one\ntwo\n")
        result = extractor.extract(3, 4)

        self.assertEqual(result, [])

    def test_invalid_start_raises_value_error(self):
        extractor = self._make_extractor("one\ntwo\n")
        with self.assertRaises(ValueError):
            extractor.extract(0, 1)

    def test_end_before_start_raises_value_error(self):
        extractor = self._make_extractor("one\ntwo\n")
        with self.assertRaises(ValueError):
            extractor.extract(3, 2)

    def test_negative_context_raises_value_error(self):
        extractor = self._make_extractor("one\ntwo\n")
        with self.assertRaises(ValueError):
            extractor.extract(1, 1, context=-1)

    def test_extract_text_joins_with_newlines(self):
        extractor = self._make_extractor("one\ntwo\nthree\n")
        text = extractor.extract_text(2, 3)

        self.assertEqual(text, "two\nthree")

    def test_extract_text_empty_for_out_of_bounds_range(self):
        extractor = self._make_extractor("one\ntwo\n")
        text = extractor.extract_text(5, 6)

        self.assertEqual(text, "")

    def test_trailing_newline_does_not_add_empty_line(self):
        extractor = self._make_extractor("one\ntwo\n")
        result = extractor.extract(1, 3)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[-1].text, "two")


if __name__ == "__main__":
    unittest.main()
