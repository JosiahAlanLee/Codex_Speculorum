import unittest
from common.illustrations.palette import Plate
from common.illustrations.guilloche import rosette
from common.ciphers import (
    write_twelve_mark_caption,
    decode_twelve_mark_caption,
    encode_falsifier_ticks,
    decode_falsifier_ticks,
    encode_lifted_pen_svg,
    decode_lifted_pen_svg,
    ClausaConfig,
    ClausaEngine,
)


class TestPaletteAndCiphers(unittest.TestCase):
    def test_twelve_mark_roundtrip(self):
        msg = "NO WOLF FIFTH IS HIDDEN."
        tokens = write_twelve_mark_caption(msg, shift=5)
        self.assertEqual(decode_twelve_mark_caption(tokens, shift=5), msg)

    def test_falsifier_scale_roundtrip_and_origin_mark(self):
        falsifier = "THE CIRCLE CLOSES WITHOUT REMAINDER"
        enc = encode_falsifier_ticks(falsifier)
        self.assertEqual(len(enc["origin_mark"]), 2)
        self.assertGreater(len(enc["group_hairlines"]), 4)
        self.assertEqual(decode_falsifier_ticks(enc["ticks"]), falsifier)

    def test_lifted_pen_svg_roundtrip(self):
        msg = "The file keeps the lifts"
        path_el = encode_lifted_pen_svg(msg)
        p = Plate("Test")
        for curve in rosette(85, 110, 32, 4, lobes=8, passes=3):
            p.add(curve)
        p.add_raw_svg_path(path_el)
        svg = p.svg()
        self.assertEqual(decode_lifted_pen_svg(svg), "THE FILE KEEPS THE LIFTS")

    def test_clausa_ground_order_and_key_sensitivity(self):
        cfg = ClausaConfig(grid_diameter=61, char_capacity=80)
        eng = ClausaEngine(cfg)
        secret = "OBJECTION I: A PURE FIFTH REPEATED TWELVE TIMES EXCEEDS SEVEN OCTAVES."
        sealed = eng.seal_field("KIRCHER KEPLER MERSENNE", 1, secret)
        coords = [(m["gy"], m["gx"]) for m in sealed["marks"]]
        self.assertEqual(coords, sorted(coords), "Marks must be sorted in ground (y, x) order.")
        recovered = eng.unseal_field("KIRCHER KEPLER MERSENNE", 1, sealed["marks"])
        self.assertEqual(recovered, secret)


if __name__ == "__main__":
    unittest.main()
