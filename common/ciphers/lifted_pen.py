import re
from typing import List, Sequence, Tuple

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def encode_lifted_pen_ops(message: str, x0: float = 20.0, y0: float = 206.0, span: float = 130.0) -> List[Tuple]:
    """
    Encodes words into M/L/Q path commands matching Book IV's lifted-pen rule:
    - Each word begins with one 'M' command.
    - Each letter A..Z is represented by `k` (1..26) collinear 'L' commands,
      terminated by a tiny 'Q' (quadratic/cubic curve) cap.
    Visually renders as clean horizontal hairline dashes while preserving the
    hidden word/letter segmentation inside both SVG and PDF vector streams.
    """
    words = ["".join(ch for ch in w.upper() if ch in ALPHABET) for w in message.split()]
    words = [w for w in words if w]
    total_letters = max(1, sum(len(w) for w in words))
    letter_w = span / (total_letters + len(words))

    ops: List[Tuple] = []
    cursor = x0
    for word in words:
        ops.append(("M", round(cursor, 3), round(y0, 3)))
        for ch in word:
            count = ALPHABET.index(ch) + 1
            step = (letter_w * 0.85) / count
            for _ in range(count):
                cursor += step
                ops.append(("L", round(cursor, 3), round(y0, 3)))
            cx = round(cursor + letter_w * 0.07, 3)
            ex = round(cursor + letter_w * 0.15, 3)
            ops.append(("Q", cx, round(y0 + 0.05, 3), ex, round(y0, 3)))
            cursor = ex
        cursor += letter_w * 0.6
    return ops


def decode_lifted_pen_ops(ops: Sequence[Tuple]) -> str:
    words: List[str] = []
    cur_word: List[str] = []
    l_count = 0
    for op in ops:
        cmd = op[0]
        if cmd == "M":
            if cur_word:
                words.append("".join(cur_word))
                cur_word = []
            l_count = 0
        elif cmd == "L":
            l_count += 1
        elif cmd in ("Q", "C"):
            if l_count > 0:
                idx = (l_count - 1) % 26
                cur_word.append(ALPHABET[idx])
                l_count = 0
    if cur_word:
        words.append("".join(cur_word))
    return " ".join(words)


def encode_lifted_pen_svg(message: str, stroke: str = "#161918") -> str:
    ops = encode_lifted_pen_ops(message)
    parts: List[str] = []
    for op in ops:
        if op[0] in ("M", "L"):
            parts.append(f"{op[0]} {op[1]:.3f} {op[2]:.3f}")
        elif op[0] == "Q":
            parts.append(f"Q {op[1]:.3f} {op[2]:.3f} {op[3]:.3f} {op[4]:.3f}")
    d = " ".join(parts)
    return f'<path data-channel="lifted-pen" d="{d}" fill="none" stroke="{stroke}" stroke-width="0.18"/>'


def decode_lifted_pen_svg(svg_text: str) -> str:
    m = re.search(r'data-channel="lifted-pen"[^>]*\bd="([^"]+)"', svg_text)
    if not m:
        raise ValueError("No data-channel='lifted-pen' path found in SVG.")
    tokens = re.findall(r"[MLQ]|-?\d+(?:\.\d+)?", m.group(1))
    ops: List[Tuple] = []
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t in ("M", "L"):
            ops.append((t, float(tokens[i + 1]), float(tokens[i + 2])))
            i += 3
        elif t == "Q":
            ops.append(("Q", float(tokens[i + 1]), float(tokens[i + 2]), float(tokens[i + 3]), float(tokens[i + 4])))
            i += 5
        else:
            i += 1
    return decode_lifted_pen_ops(ops)
