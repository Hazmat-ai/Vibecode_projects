"""
core/yaml_loader.py — Minimal YAML subset parser (stdlib only).
Handles the exact YAML format used in REMNANT seed files.
Supports: key: scalar, key: [inline list], key: > block, key: | block,
          block sequences (- item), quoted strings, integers.
No third-party dependencies.
"""

import re
from typing import Any


def load(text: str) -> dict:
    """Parse a YAML string and return a dict. Handles seed-file format only."""
    if len(text) > 250000:
        raise ValueError("Knowledge file exceeds 250 KB.")
    lines = text.splitlines()
    return _parse_block(lines, 0, 0)[0]


def load_file(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return load(f.read(250001))


# ------------------------------------------------------------------ #
#  Internal parsers                                                    #
# ------------------------------------------------------------------ #

def _indent(line: str) -> int:
    return len(line) - len(line.lstrip())


def _is_blank(line: str) -> bool:
    return line.strip() == "" or line.strip().startswith("#")


def _unquote(s: str) -> str:
    s = s.strip()
    if (s.startswith('"') and s.endswith('"')) or \
       (s.startswith("'") and s.endswith("'")):
        return s[1:-1]
    return s


def _parse_scalar(s: str) -> Any:
    """Convert a string scalar to int/float/bool/None/str."""
    s = s.strip()
    if len(s) >= 2 and s[0] in ("'", '"') and s[-1] == s[0]:
        return _unquote(s)
    if s == "true":  return True
    if s == "false": return False
    if s == "null" or s == "~" or s == "": return None
    try:
        return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        pass
    return s


def _parse_inline_list(s: str) -> list:
    """Parse [a, b, c] into a Python list."""
    s = s.strip()
    if not (s.startswith("[") and s.endswith("]")):
        return [_parse_scalar(s)]
    inner = s[1:-1].strip()
    if not inner:
        return []
    # Split by comma, respecting quotes
    items = []
    current = ""
    depth = 0
    in_quote = None
    for ch in inner:
        if ch in ('"', "'") and in_quote is None:
            in_quote = ch
            current += ch
        elif ch == in_quote:
            in_quote = None
            current += ch
        elif ch == "[":
            depth += 1
            current += ch
        elif ch == "]":
            depth -= 1
            current += ch
        elif ch == "," and depth == 0 and in_quote is None:
            items.append(_parse_scalar(current.strip()))
            current = ""
        else:
            current += ch
    if current.strip():
        items.append(_parse_scalar(current.strip()))
    return items


def _parse_block(lines: list, start: int, base_indent: int):
    """
    Parse a YAML mapping starting at `start`.
    Returns (dict, next_line_index).
    """
    result = {}
    i = start

    while i < len(lines):
        line = lines[i]

        if _is_blank(line):
            i += 1
            continue

        indent = _indent(line)

        # Dedent means we've left this block
        if indent < base_indent:
            break

        stripped = line.strip()

        # Block sequence item at this level
        if stripped.startswith("- ") or stripped == "-":
            # This is a sequence — caller should handle via _parse_sequence
            break

        # Key: value line
        if ":" in stripped:
            # Find the first colon not inside brackets or quotes
            colon_pos = _find_colon(stripped)
            if colon_pos == -1:
                i += 1
                continue

            key = stripped[:colon_pos].strip()
            if key in result:
                raise ValueError("Duplicate YAML key: " + key)
            value_raw = stripped[colon_pos + 1:].strip()

            # Block scalar: > or |
            if value_raw in (">", "|"):
                scalar_type = value_raw
                i += 1
                text_lines = []
                block_indent = None
                while i < len(lines):
                    bline = lines[i]
                    if _is_blank(bline):
                        text_lines.append("")
                        i += 1
                        continue
                    bindent = _indent(bline)
                    if block_indent is None:
                        block_indent = bindent
                    if bindent < block_indent:
                        break
                    text_lines.append(bline[block_indent:])
                    i += 1
                # Trim trailing blanks
                while text_lines and text_lines[-1] == "":
                    text_lines.pop()
                if scalar_type == "|":
                    result[key] = "\n".join(text_lines)
                else:  # >  — folded: join paragraphs
                    result[key] = " ".join(t if t != "" else "\n" for t in text_lines).strip()
                continue

            # Inline list
            if value_raw.startswith("["):
                result[key] = _parse_inline_list(value_raw)
                i += 1
                continue

            # Empty value — look ahead for nested block or sequence
            if value_raw == "":
                i += 1
                if i < len(lines):
                    next_stripped = lines[i].strip()
                    if next_stripped.startswith("- ") or next_stripped == "-":
                        seq, i = _parse_sequence(lines, i, indent + 1)
                        result[key] = seq
                    elif not _is_blank(lines[i]) and _indent(lines[i]) > indent:
                        nested, i = _parse_block(lines, i, _indent(lines[i]))
                        result[key] = nested
                    # else: key maps to None
                continue

            # Simple scalar value
            result[key] = _parse_scalar(value_raw)
            i += 1
            continue

        i += 1

    return result, i


def _parse_sequence(lines: list, start: int, base_indent: int):
    """Parse a YAML block sequence starting at `start`. Returns (list, next_idx)."""
    result = []
    i = start

    while i < len(lines):
        line = lines[i]
        if _is_blank(line):
            i += 1
            continue
        indent = _indent(line)
        if indent < base_indent - 1:
            break
        stripped = line.strip()
        if stripped.startswith("- "):
            item = _parse_scalar(stripped[2:].strip())
            result.append(item)
            i += 1
        elif stripped == "-":
            result.append(None)
            i += 1
        else:
            break

    return result, i


def _find_colon(s: str) -> int:
    """Find index of first ':' that is a key separator (not inside brackets/quotes)."""
    in_quote = None
    depth = 0
    for idx, ch in enumerate(s):
        if ch in ('"', "'") and in_quote is None:
            in_quote = ch
        elif ch == in_quote:
            in_quote = None
        elif ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
        elif ch == ":" and in_quote is None and depth == 0:
            return idx
    return -1
