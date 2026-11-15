from dataclasses import dataclass
import hashlib
from typing import Dict, List, Sequence, Tuple

# 64-symbol 6-bit sign table matching Nota Clausa conventions (0=space, 1..26=A-Z, 27..36=0-9, punct, ¶=newline)
CLAUSA_ALPHABET = (
    " ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789"
    '.,;:?!"-()/[]§¶*+=@#%&<>~^_`|' + chr(92) + '/$;'
)[:64]
assert len(CLAUSA_ALPHABET) == 64


class SplitMix64:
    """Deterministic 64-bit PRNG seeded per field from SHA-256(KEY + '/' + k)."""

    def __init__(self, seed: int):
        self.state = seed & 0xFFFFFFFFFFFFFFFF

    @classmethod
    def from_key(cls, key: str, field_index: int) -> "SplitMix64":
        digest = hashlib.sha256(f"{key}/{field_index}".encode("utf-8")).digest()
        seed = int.from_bytes(digest[:8], "big")
        return cls(seed)

    def next_u64(self) -> int:
        self.state = (self.state + 0x9E3779B97F4A7C15) & 0xFFFFFFFFFFFFFFFF
        z = self.state
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & 0xFFFFFFFFFFFFFFFF
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & 0xFFFFFFFFFFFFFFFF
        return (z ^ (z >> 31)) & 0xFFFFFFFFFFFFFFFF

    def randbelow(self, n: int) -> int:
        return self.next_u64() % n


@dataclass(frozen=True)
class ClausaConfig:
    grid_diameter: int = 89
    cell_mm: float = 1.4
    origin_x_mm: float = 22.7
    origin_y_mm: float = 48.0
    char_capacity: int = 240  # 240 chars * 6 bits = 1440 cells per specimen plate

    @property
    def bit_capacity(self) -> int:
        return self.char_capacity * 6


def encode_6bit(text: str, char_capacity: int) -> List[int]:
    normalized = text.upper().replace("\n", "¶")
    if len(normalized) > char_capacity:
        raise ValueError(f"Plaintext length {len(normalized)} exceeds field char_capacity {char_capacity}.")
    padded = normalized.ljust(char_capacity, " ")
    bits: List[int] = []
    for ch in padded:
        idx = CLAUSA_ALPHABET.index(ch) if ch in CLAUSA_ALPHABET else 0
        for b in range(5, -1, -1):
            bits.append((idx >> b) & 1)
    return bits


def decode_6bit(bits: Sequence[int]) -> str:
    chars: List[str] = []
    for i in range(0, len(bits) - (len(bits) % 6), 6):
        val = 0
        for b in bits[i : i + 6]:
            val = (val << 1) | (1 if b else 0)
        ch = CLAUSA_ALPHABET[val]
        chars.append("\n" if ch == "¶" else ch)
    return "".join(chars).rstrip()


class ClausaEngine:
    """
    Domain-agnostic Nota Clausa engine.
    Subclasses override `select_ordered_cells(rng, count)` with a deterministic
    integer simulation native to the volume's subject matter (e.g., coupled
    oscillators, Chladni nodal resonance, or geodesic ray-march).
    Emitted strokes are ALWAYS sorted in ground (y, x) order so SVG/PDF element
    order never leaks key-dependent permutation order.
    """

    def __init__(self, config: ClausaConfig = ClausaConfig()):
        self.config = config

    def arena_cells(self) -> List[Tuple[int, int]]:
        r = self.config.grid_diameter // 2
        cx, cy = r, r
        cells: List[Tuple[int, int]] = []
        for y in range(self.config.grid_diameter):
            for x in range(self.config.grid_diameter):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                    cells.append((x, y))
        return cells

    def select_ordered_cells(self, rng: SplitMix64, count: int) -> List[Tuple[int, int, int]]:
        """
        Default specimen simulation: deterministic integer 3-source standing-wave
        lattice scored and broken by keyed SplitMix64 permutation, returning
        `count` distinct (x, y, heading_idx_0_15) tuples in key-dependent order.
        """
        pool = list(self.arena_cells())
        if len(pool) < count:
            raise ValueError("Arena too small for requested bit capacity.")
        # Keyed integer wave sources
        sources = [
            (rng.randbelow(self.config.grid_diameter), rng.randbelow(self.config.grid_diameter), 3 + rng.randbelow(5))
            for _ in range(3)
        ]
        scored = []
        for (x, y) in pool:
            acc = 0
            for sx, sy, wavelen in sources:
                d2 = (x - sx) ** 2 + (y - sy) ** 2
                # Integer triangle-wave phase residue
                phase = (d2 % (wavelen * wavelen)) * 256 // max(1, wavelen * wavelen)
                acc += abs(phase - 128)
            tie = rng.next_u64()
            heading = rng.randbelow(16)
            scored.append((acc, tie, x, y, heading))
        scored.sort(key=lambda item: (item[0], item[1]))
        return [(x, y, h) for (_, _, x, y, h) in scored[:count]]

    def seal_field(self, key: str, field_index: int, plaintext: str) -> Dict:
        rng = SplitMix64.from_key(key, field_index)
        bits = encode_6bit(plaintext, self.config.char_capacity)
        keyed_cells = self.select_ordered_cells(rng, len(bits))

        marks: List[Dict] = []
        for bit, (gx, gy, heading) in zip(bits, keyed_cells):
            marks.append({
                "gx": gx,
                "gy": gy,
                "heading": heading,
                "bit": bit,
                "ink": "#a32b24" if bit == 1 else "#161918",
            })

        # MANDATORY ground (gy, gx) sort — prevents the agent-order SVG leak!
        marks.sort(key=lambda m: (m["gy"], m["gx"]))

        canonical_text = decode_6bit(bits)
        digest = hashlib.sha256(canonical_text.encode("utf-8")).hexdigest()
        return {
            "field_index": field_index,
            "marks": marks,
            "sha256": digest,
            "red_count": sum(m["bit"] for m in marks),
        }

    def unseal_field(self, key: str, field_index: int, ground_marks: Sequence[Dict]) -> str:
        rng = SplitMix64.from_key(key, field_index)
        keyed_cells = self.select_ordered_cells(rng, self.config.bit_capacity)
        lookup = {(m["gx"], m["gy"]): (1 if m["ink"].lower() == "#a32b24" else 0) for m in ground_marks}
        bits = [lookup[(gx, gy)] for (gx, gy, _) in keyed_cells]
        return decode_6bit(bits)
