# Source Line Extractor

Source Line Extractor reads a text file and returns numbered lines from a requested range, optionally surrounded by context lines.

```python
from pathlib import Path
from source_line_extractor import SourceLineExtractor

Path("example.py").write_text("one\ntwo\nthree\nfour\nfive\n", encoding="utf-8")
extractor = SourceLineExtractor("example.py")
for line in extractor.extract(2, 4, context=1):
    marker = ">" if line.in_selection else " "
    print(f"{marker} {line.number:4d} {line.text}")
```

## Why this exists

When reporting errors, documentation tools, or code review helpers need to show a slice of a source file, they usually want three things: the exact selected lines, their original line numbers, and a little surrounding context so the reader can see where those lines sit. This library does that one job without pulling in a parser or formatter.

The main trade-off is that the whole file is held in memory. That is deliberate: source files are typically small, and keeping the lines loaded makes repeated extractions from the same file simple and fast. It is not the right tool for huge logs or generated files that cannot fit in memory.

## Edge cases

Line numbers are 1-based and inclusive at both ends. Context is clamped to the file boundaries, so requesting more context than exists near the top or bottom simply returns fewer lines. Ranges that do not intersect the file at all return an empty list. Invalid arguments such as a start below 1, an end before the start, or negative context raise `ValueError`.

## Exports

- `SourceLineExtractor` — the main class, importable from `source_line_extractor`
- `SourceLineExtractor.extract(start, end, context=0)` — returns a list of `ExtractedLine`
- `SourceLineExtractor.extract_text(start, end, context=0)` — returns just the joined text
- `ExtractedLine` — a frozen dataclass with `number`, `text`, and `in_selection`

`ExtractedLine` is available from `source_line_extractor.core`.

## Performance

The window keeps a bounded buffer, so `push` is constant time and memory does not
grow with the length of the stream. `peak` and `trough` are linear in the window
size, which is the trade that keeps `push` cheap.

