from dataclasses import dataclass, field
import html
import re
from typing import List, Optional, Tuple


@dataclass
class InlineSegment:
    text: str
    tags: Tuple[str, ...] = ()
    href: Optional[str] = None


@dataclass
class Block:
    kind: str
    level: int = 0
    text: str = ""
    items: List[str] = field(default_factory=list)
    rows: List[List[str]] = field(default_factory=list)
    ordered: bool = False


@dataclass
class Document:
    title: str
    blocks: List[Block]
    headings: List[Tuple[int, str]]


INLINE_PATTERN = re.compile(r"(`[^`]+`|\*\*.+?\*\*|\*[^*]+\*|\[[^\]]+\]\([^)]+\))")
ORDERED_PATTERN = re.compile(r"^\d+\.\s+")


def parse_markdown(content: str, fallback_title: str = "Markdown Preview") -> Document:
    lines = content.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    blocks: List[Block] = []
    headings: List[Tuple[int, str]] = []
    paragraph: List[str] = []
    in_code = False
    code_lines: List[str] = []
    code_fence = ""
    i = 0

    def flush_paragraph() -> None:
        if paragraph:
            blocks.append(Block(kind="paragraph", text=" ".join(part.strip() for part in paragraph if part.strip())))
            paragraph.clear()

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if in_code:
            if stripped.startswith("```"):
                blocks.append(Block(kind="code", text="\n".join(code_lines)))
                code_lines = []
                in_code = False
                code_fence = ""
            else:
                code_lines.append(line)
            i += 1
            continue

        if stripped.startswith("```"):
            flush_paragraph()
            in_code = True
            code_fence = stripped[3:].strip()
            if code_fence:
                code_lines.append("# language: %s" % code_fence)
            i += 1
            continue

        if not stripped:
            flush_paragraph()
            i += 1
            continue

        if stripped == "---" or stripped == "***":
            flush_paragraph()
            blocks.append(Block(kind="rule"))
            i += 1
            continue

        if line.startswith("#"):
            flush_paragraph()
            level = len(line) - len(line.lstrip("#"))
            text = line[level:].strip()
            if text:
                blocks.append(Block(kind="heading", level=min(level, 6), text=text))
                headings.append((min(level, 6), text))
            i += 1
            continue

        if stripped.startswith(">"):
            flush_paragraph()
            quote_lines = [stripped[1:].strip()]
            j = i + 1
            while j < len(lines) and lines[j].strip().startswith(">"):
                quote_lines.append(lines[j].strip()[1:].strip())
                j += 1
            blocks.append(Block(kind="quote", text="\n".join(quote_lines)))
            i = j
            continue

        if stripped.startswith("- ") or stripped.startswith("* ") or ORDERED_PATTERN.match(stripped):
            flush_paragraph()
            ordered = bool(ORDERED_PATTERN.match(stripped))
            items: List[str] = []
            j = i
            while j < len(lines):
                current = lines[j].strip()
                if ordered and ORDERED_PATTERN.match(current):
                    items.append(ORDERED_PATTERN.sub("", current, count=1).strip())
                    j += 1
                    continue
                if not ordered and (current.startswith("- ") or current.startswith("* ")):
                    items.append(current[2:].strip())
                    j += 1
                    continue
                break
            blocks.append(Block(kind="list", items=items, ordered=ordered))
            i = j
            continue

        if "|" in line:
            flush_paragraph()
            table_lines = [line]
            j = i + 1
            while j < len(lines) and "|" in lines[j] and lines[j].strip():
                table_lines.append(lines[j])
                j += 1
            rows = [_split_table_row(table_line) for table_line in table_lines]
            if len(rows) >= 2 and _is_separator_row(rows[1]):
                blocks.append(Block(kind="table", rows=[rows[0]] + rows[2:]))
                i = j
                continue

        paragraph.append(line)
        i += 1

    flush_paragraph()

    if in_code:
        blocks.append(Block(kind="code", text="\n".join(code_lines)))

    title = headings[0][1] if headings else fallback_title
    return Document(title=title, blocks=blocks, headings=headings)


def parse_inline(text: str) -> List[InlineSegment]:
    segments: List[InlineSegment] = []
    last_index = 0
    for match in INLINE_PATTERN.finditer(text):
        if match.start() > last_index:
            segments.append(InlineSegment(text=text[last_index:match.start()]))
        token = match.group(0)
        if token.startswith("`") and token.endswith("`"):
            segments.append(InlineSegment(text=token[1:-1], tags=("inline_code",)))
        elif token.startswith("**") and token.endswith("**"):
            segments.append(InlineSegment(text=token[2:-2], tags=("bold",)))
        elif token.startswith("*") and token.endswith("*"):
            segments.append(InlineSegment(text=token[1:-1], tags=("italic",)))
        elif token.startswith("[") and "](" in token and token.endswith(")"):
            label, href = token[1:-1].split("](", 1)
            segments.append(InlineSegment(text=label, tags=("link",), href=href))
        else:
            segments.append(InlineSegment(text=token))
        last_index = match.end()
    if last_index < len(text):
        segments.append(InlineSegment(text=text[last_index:]))
    return _merge_segments(segments)


def table_to_text(rows: List[List[str]]) -> str:
    if not rows:
        return ""
    column_count = max(len(row) for row in rows)
    normalized_rows = [row + [""] * (column_count - len(row)) for row in rows]
    widths = [max(len(html.unescape(cell)) for cell in column) for column in zip(*normalized_rows)]
    rendered: List[str] = []
    for row_index, row in enumerate(normalized_rows):
        line = " | ".join(cell.ljust(widths[index]) for index, cell in enumerate(row))
        rendered.append(line)
        if row_index == 0:
            rendered.append("-+-".join("-" * width for width in widths))
    return "\n".join(rendered)


def _split_table_row(line: str) -> List[str]:
    text = line.strip().strip("|")
    return [html.unescape(cell.strip()) for cell in text.split("|")]


def _is_separator_row(row: List[str]) -> bool:
    if not row:
        return False
    for cell in row:
        candidate = cell.replace(":", "").replace("-", "").strip()
        if candidate:
            return False
    return True


def _merge_segments(segments: List[InlineSegment]) -> List[InlineSegment]:
    merged: List[InlineSegment] = []
    for segment in segments:
        if not segment.text:
            continue
        if merged and merged[-1].tags == segment.tags and merged[-1].href == segment.href:
            merged[-1].text += segment.text
        else:
            merged.append(segment)
    return merged
