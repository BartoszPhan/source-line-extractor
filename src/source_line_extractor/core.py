"""Core extraction logic for Source Line Extractor.

The extractor returns numbered source lines from a text file given a start
line, end line, and an optional context window. Lines are 1-indexed, matching
what editors and tracebacks display. The context window adds extra lines
before and after the selected range to help readers orient themselves.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, List, Sequence


@dataclass(frozen=True)
class ExtractedLine:
    """A single numbered source line."""

    number: int
    text: str
    in_selection: bool


class SourceLineExtractor:
    """Extract and number lines from a source file.

    Args:
        path: Path to the source file.

    Lines are numbered starting at 1. The ``extract`` method returns a list of
    :class:`ExtractedLine` objects. Each object carries the original 1-based
    line number, the line text without its trailing newline, and a flag that
    indicates whether the line was part of the requested selection or only a
    surrounding context line.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._lines = self._read_lines()

    def _read_lines(self) -> List[str]:
        """Read the source file, removing trailing newlines.

        Keeping the whole file in memory is intentional. The target files are
        source listings that are typically small enough to fit comfortably in
        memory, and this makes repeated extractions from the same file cheap.
        """
        with self.path.open("r", encoding="utf-8") as handle:
            return [line.rstrip("\n") for line in handle]

    @property
    def line_count(self) -> int:
        """Number of lines in the source file."""
        return len(self._lines)

    def extract(
        self,
        start: int,
        end: int,
        context: int = 0,
    ) -> List[ExtractedLine]:
        """Extract a numbered line range with optional surrounding context.

        Args:
            start: First selected line, 1-based inclusive.
            end: Last selected line, 1-based inclusive.
            context: Number of extra lines to include before and after the
                selected range. Defaults to zero.

        Returns:
            A list of :class:`ExtractedLine` objects ordered by line number.
            The list is empty when the requested range does not intersect the
            file at all, for example when ``start`` is greater than
            ``line_count`` or ``end`` is less than 1.

        Raises:
            ValueError: If ``start`` is less than 1, ``end`` is less than
                ``start``, or ``context`` is negative.

        The selection is inclusive at both ends, so ``extract(2, 2)`` returns
        exactly line 2. Context is clamped to the file boundaries; requesting
        context near the top or bottom of a file will simply return fewer
        context lines rather than padding with blanks.
        """
        if start < 1:
            raise ValueError("start must be at least 1")
        if end < start:
            raise ValueError("end must be greater than or equal to start")
        if context < 0:
            raise ValueError("context must be non-negative")

        total = self.line_count
        if total == 0 or start > total or end < 1:
            return []

        first_selected = max(start, 1)
        last_selected = min(end, total)
        first_returned = max(first_selected - context, 1)
        last_returned = min(last_selected + context, total)

        extracted: List[ExtractedLine] = []
        for number in range(first_returned, last_returned + 1):
            in_selection = first_selected <= number <= last_selected
            extracted.append(
                ExtractedLine(
                    number=number,
                    text=self._lines[number - 1],
                    in_selection=in_selection,
                )
            )
        return extracted

    def extract_text(self, start: int, end: int, context: int = 0) -> str:
        """Extract just the text for a range, joined with newlines.

        This is a convenience wrapper around :meth:`extract` for callers that
        do not need line numbers or the in-selection flag. Empty ranges return
        an empty string.
        """
        return "\n".join(line.text for line in self.extract(start, end, context))
