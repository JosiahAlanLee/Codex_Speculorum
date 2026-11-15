from typing import Dict, List, Sequence, Tuple

SCALE_VOCAB = " ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.,;:-"


def text_to_bits(text: str) -> List[int]:
    bits: List[int] = []
    for ch in text.upper():
        idx = SCALE_VOCAB.index(ch) if ch in SCALE_VOCAB else 0
        for b in range(5, -1, -1):
            bits.append((idx >> b) & 1)
    return bits


def bits_to_text(bits: Sequence[int]) -> str:
    chars: List[str] = []
    for i in range(0, len(bits) - (len(bits) % 6), 6):
        val = 0
        for b in bits[i : i + 6]:
            val = (val << 1) | (1 if b else 0)
        chars.append(SCALE_VOCAB[val % len(SCALE_VOCAB)])
    return "".join(chars).rstrip()


def encode_falsifier_ticks(
    falsifier: str,
    x_mm: float = 12.0,
    y_mm: float = 14.0,
    w_mm: float = 146.0,
    h_mm: float = 192.0,
) -> Dict[str, List]:
    """
    Encodes a plate's falsifier proposition as biliteral border scale ticks
    clockwise from the top-left origin, adding:
      1. A rubricated (#a32b24) L-corner origin index mark at (x_mm, y_mm), and
      2. Subtle 6-bit character-grouping hairlines every 6 ticks
    so a human reader working from paper alone can recover bit 0 and group symbols.
    """
    bits = text_to_bits(falsifier)
    perimeter = 2.0 * (w_mm + h_mm)
    step = perimeter / max(len(bits) + 2, 48)

    ticks: List[Dict] = []
    group_hairlines: List[Tuple[Tuple[float, float], Tuple[float, float]]] = []

    # Rubricated origin index mark at top-left corner (bit 0 clockwise arrow cue)
    origin_mark = [
        ((x_mm - 2.2, y_mm), (x_mm, y_mm)),
        ((x_mm, y_mm - 2.2), (x_mm, y_mm)),
    ]

    for idx, bit in enumerate(bits):
        d = (idx + 1) * step
        if d <= w_mm:
            px, py, nx, ny = x_mm + d, y_mm, 0.0, 1.0
        elif d <= w_mm + h_mm:
            px, py, nx, ny = x_mm + w_mm, y_mm + (d - w_mm), -1.0, 0.0
        elif d <= 2.0 * w_mm + h_mm:
            px, py, nx, ny = x_mm + w_mm - (d - w_mm - h_mm), y_mm + h_mm, 0.0, -1.0
        else:
            px, py, nx, ny = x_mm, y_mm + h_mm - (d - 2.0 * w_mm - h_mm), 1.0, 0.0

        length = 2.4 if bit == 1 else 1.2
        ticks.append({
            "index": idx,
            "bit": bit,
            "red": bool(bit == 1),
            "p0": (px, py),
            "p1": (px + nx * length, py + ny * length),
        })

        if (idx + 1) % 6 == 0 and idx + 1 < len(bits):
            hd = d + 0.5 * step
            if hd <= w_mm:
                gx, gy, gnx, gny = x_mm + hd, y_mm, 0.0, -1.0
            elif hd <= w_mm + h_mm:
                gx, gy, gnx, gny = x_mm + w_mm, y_mm + (hd - w_mm), 1.0, 0.0
            elif hd <= 2.0 * w_mm + h_mm:
                gx, gy, gnx, gny = x_mm + w_mm - (hd - w_mm - h_mm), y_mm + h_mm, 0.0, 1.0
            else:
                gx, gy, gnx, gny = x_mm, y_mm + h_mm - (hd - 2.0 * w_mm - h_mm), -1.0, 0.0
            group_hairlines.append(((gx, gy), (gx + gnx * 0.9, gy + gny * 0.9)))

    return {
        "origin_mark": origin_mark,
        "ticks": ticks,
        "group_hairlines": group_hairlines,
        "bit_count": len(bits),
    }


def decode_falsifier_ticks(ticks: Sequence[Dict]) -> str:
    ordered = sorted(ticks, key=lambda t: t["index"])
    return bits_to_text([t["bit"] for t in ordered])
