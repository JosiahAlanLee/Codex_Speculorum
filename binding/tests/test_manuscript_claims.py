"""
Holds the reading manuscripts to the solvers they describe.

Right of Reply entries O-003 and O-005 found [E]-tagged prose in Liber I and
Liber III that disagreed with the shipped generators. These tests parse the
bound manuscripts and fail the build if the printed score, node count, overtone
ratio, or port-coupling amplitudes ever drift from `build_canon_score()` and
`solve_viol_acoustic_resonator()` again.
"""

from fractions import Fraction
import importlib.util
from pathlib import Path
import re
import unittest

import numpy as np

from common.illustrations.shader_plates import solve_viol_acoustic_resonator

REPO = Path(__file__).resolve().parents[2]
LIBER_I = REPO / "books" / "01_liber_primus" / "manuscript" / "reading-edition.md"
LIBER_III = REPO / "books" / "03_liber_tertius" / "manuscript" / "reading-edition.md"
CANON = REPO / "books" / "01_liber_primus" / "canon" / "play_koopman_canon.py"


def _load_canon_module():
    spec = importlib.util.spec_from_file_location("play_koopman_canon", CANON)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def _printed_score(text: str):
    """Returns {('Recta'|'Cancri'): [32 swaras]} parsed from the Liber I score block."""
    voices = {"Recta": [], "Cancri": []}
    for m in re.finditer(r"^> `Bars \d-\d (Recta|Cancri)\s*: ([^`]+)`", text, flags=re.M):
        voice, body = m.group(1), m.group(2)
        for bar in body.split("|"):
            voices[voice].extend(bar.split())
    return voices


class TestLiberIScoreMatchesGenerator(unittest.TestCase):
    def test_printed_score_is_the_generator_table(self):
        pk = _load_canon_module()
        score = pk.build_canon_score()
        printed = _printed_score(LIBER_I.read_text(encoding="utf-8"))
        self.assertEqual(len(printed["Recta"]), 32)
        self.assertEqual(len(printed["Cancri"]), 32)
        self.assertEqual(printed["Recta"], [r["recta_swara"] for r in score])
        self.assertEqual(printed["Cancri"], [r["cancri_swara"] for r in score])

    def test_prose_dyad_set_matches_generator(self):
        pk = _load_canon_module()
        dyads = {r["dyad_ratio"] for r in pk.build_canon_score()}
        self.assertEqual(dyads, {Fraction(1, 1), Fraction(6, 5), Fraction(5, 4), Fraction(4, 3)})
        text = LIBER_I.read_text(encoding="utf-8")
        self.assertIn("exactly `1:1`, `6:5`, `5:4`, `4:3`", text)
        self.assertNotIn("thirds, fourths, and fifths", text)


class TestLiberIIIProseMatchesSolver(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sol = solve_viol_acoustic_resonator()
        cls.text = LIBER_III.read_text(encoding="utf-8")

    def test_node_count_and_octave_ratio(self):
        n_nodes = int(self.sol["inside"].sum())
        self.assertIn(f"{n_nodes:,} finite-volume nodes", self.text)
        ratio = self.sol["freq_ratios"][1]
        self.assertIn(f"√(μ₃ / μ₂) = {ratio:.4f}", self.text)
        self.assertNotIn("4,603", self.text)
        self.assertNotIn("2.0004", self.text)

    def test_port_coupling_amplitudes_support_section_iv(self):
        """Poles are u_2 antinodes and u_3 nodes; waist-rim endpoints are the reverse."""
        sol = self.sol
        inside = sol["inside"]
        u2, u3 = sol["field_u2"], sol["field_u3"]
        ny, nx = inside.shape
        boundary = np.zeros_like(inside)
        for j in range(ny):
            for i in range(nx):
                if not inside[j, i]:
                    continue
                deg = 0
                for dj, di in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nj, ni = j + dj, i + di
                    if 0 <= nj < ny and 0 <= ni < nx and inside[nj, ni]:
                        deg += 1
                boundary[j, i] = deg < 4

        # Poles: global extrema of u_2 (on the rim by Family 369) carry no u_3.
        for pole in (np.nanargmax(u2), np.nanargmin(u2)):
            j, i = np.unravel_index(pole, u2.shape)
            self.assertTrue(boundary[j, i])
            self.assertLess(abs(u3[j, i]), 0.01)

        # Waist-rim endpoints: the rim points where |u_2| is smallest carry |u_3| ~ 0.6.
        rim = np.argwhere(boundary)
        rim_u2 = np.array([abs(u2[j, i]) for j, i in rim])
        for k in np.argsort(rim_u2)[:4]:
            j, i = rim[k]
            self.assertLess(abs(u2[j, i]), 0.05)
            self.assertGreater(abs(u3[j, i]), 0.5)


if __name__ == "__main__":
    unittest.main()
