from fractions import Fraction
import importlib.util
import tempfile
import unittest
from pathlib import Path
import wave
import xml.etree.ElementTree as ET

import numpy as np
from PIL import Image

from binding import vellum
from common.ciphers import decode_lifted_pen_svg
from common.illustrations.shader_plates import (
    godel_diophantine_geometry,
    verify_godel_singlefold_invariants,
    acoustic_resonator_geometry,
    solve_viol_acoustic_resonator,
    aperiodic_vault_geometry,
    build_3d_skew_vault_voxels,
    gauss_linking_number,
    hopf_fiber_s3,
    hopf_fibration_geometry,
    hotspots_neumann_geometry,
    hypercube_4d_vault,
    mobius_bipolar_point,
    solve_strict_hotspots_neumann,
)

REPO = Path(__file__).resolve().parents[3]
_spec = importlib.util.spec_from_file_location("tabulae_test_mod", REPO / "books" / "01_liber_primus" / "plates" / "tabulae.py")
tabulae = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tabulae)

_spec2 = importlib.util.spec_from_file_location("tabulae2_test_mod", REPO / "books" / "02_liber_secundus" / "plates" / "tabulae.py")
tabulae2 = importlib.util.module_from_spec(_spec2)
_spec2.loader.exec_module(tabulae2)

_cspec = importlib.util.spec_from_file_location("canon_test_mod", REPO / "books" / "01_liber_primus" / "canon" / "play_koopman_canon.py")
canon_mod = importlib.util.module_from_spec(_cspec)
_cspec.loader.exec_module(canon_mod)


_skew_spec = importlib.util.spec_from_file_location(
    "skew_canon_mod", REPO / "books" / "02_liber_secundus" / "canon" / "play_skew_vault_canon.py"
)
skew_canon_mod = importlib.util.module_from_spec(_skew_spec)
_skew_spec.loader.exec_module(skew_canon_mod)

class TestShaderPlatesAndVellum(unittest.TestCase):
    def test_hopf_s3_norm_and_unit_linking_invariant(self):
        q_a = hopf_fiber_s3(0.50 * np.pi, 0.28 * np.pi, steps=200)
        norms = np.linalg.norm(q_a, axis=-1)
        np.testing.assert_allclose(norms, 1.0, atol=1e-9)

        geom = hopf_fibration_geometry()
        link_a, link_b = geom["link_r3"]
        lk = abs(gauss_linking_number(link_a, link_b))
        self.assertAlmostEqual(lk, 1.0, delta=0.03)

    def test_conformal_mobius_orthogonality_and_4d_vault_topology(self):
        u0, v0 = 0.65, 1.05
        eps = 1e-5
        pu_p = mobius_bipolar_point(u0 + eps, v0)
        pu_m = mobius_bipolar_point(u0 - eps, v0)
        pv_p = mobius_bipolar_point(u0, v0 + eps)
        pv_m = mobius_bipolar_point(u0, v0 - eps)

        tu = np.array([(pu_p[0] - pu_m[0]) / (2 * eps), (pu_p[1] - pu_m[1]) / (2 * eps)])
        tv = np.array([(pv_p[0] - pv_m[0]) / (2 * eps), (pv_p[1] - pv_m[1]) / (2 * eps)])
        cos_ang = abs(float(np.dot(tu, tv)) / (np.linalg.norm(tu) * np.linalg.norm(tv)))
        self.assertLess(cos_ang, 1e-4)

        vault = hypercube_4d_vault()
        self.assertEqual(len(vault["verts_2d"]), 16)
        self.assertEqual(len(vault["edges"]), 32)

    def test_strict_hotspots_neumann_invariants(self):
        sol = solve_strict_hotspots_neumann(h_mm=1.0)
        self.assertGreater(sol["lambda_1"], 0.0)
        self.assertLess(abs(sol["mean_u1"]), 1e-6)
        self.assertTrue(sol["max_on_boundary"])
        self.assertTrue(sol["min_on_boundary"])
        self.assertGreater(sol["min_interior_grad"], 1e-4)

        geom = hotspots_neumann_geometry()
        self.assertGreater(len(geom["ink_strokes"]), 20)
        self.assertGreaterEqual(len(geom["red_strokes"]), 5)

    def test_koopman_bhairav_crab_canon_invariants_and_audio(self):
        info = canon_mod.verify_canon_invariants()
        self.assertEqual(info["steps"], 32)
        self.assertEqual(info["non_unison"], 30)

        score = canon_mod.build_canon_score()
        self.assertEqual(score[0]["dyad_ratio"], Fraction(1, 1))
        self.assertEqual(score[-1]["dyad_ratio"], Fraction(1, 1))

        with tempfile.TemporaryDirectory() as tmp:
            wav_p = Path(tmp) / "canon.wav"
            pd_p = Path(tmp) / "canon.pd"
            meta = canon_mod.render_canon_wav(wav_p)
            canon_mod.export_pure_data_patch(pd_p)
            self.assertTrue(wav_p.is_file() and pd_p.is_file())
            self.assertAlmostEqual(meta["peak_dbfs"], -1.4, delta=0.15)
            with wave.open(str(wav_p), "rb") as wf:
                self.assertEqual(wf.getnchannels(), 2)
                self.assertEqual(wf.getframerate(), 48000)
                self.assertGreater(wf.getnframes(), 48000 * 40)

    def test_3d_aperiodic_vault_disjoint_tiling_and_hidden_lines(self):
        # Verify zero-overlap 4-voxel monotile packing & non-periodic shear across 32 y-layers
        vdata = build_3d_skew_vault_voxels(nx=8, ny=32, nz=6)
        total_voxels = sum(len(cells) for cells in vdata["stone_voxels"].values())
        self.assertEqual(total_voxels, len(vdata["voxel_owner"]), "Translational monotiles must be strictly disjoint.")
        for cells in vdata["stone_voxels"].values():
            self.assertEqual(len(cells), 4)

        shears = vdata["y_shears"]
        for period in range(1, 16):
            is_per = all(shears[i] == shears[i + period] for i in range(len(shears) - period))
            self.assertFalse(is_per, f"y_shears unexpectedly periodic with period {period}!")

        geom = aperiodic_vault_geometry()
        self.assertGreater(geom["visible_triangles"], 80)
        self.assertGreater(len(geom["ink_strokes"]), 40)
        self.assertGreater(len(geom["red_strokes"]), 5)

    def test_svg_plotter_bounds_palette_and_lifted_pen(self):
        builders = [
            (tabulae.build_tabula_ii_hopf_svg, "EVERY CIRCLE LINKS EVERY OTHER"),
            (tabulae.build_tabula_iii_mobius_svg, "ANGLES SURVIVE INVERSION"),
            (tabulae.build_tabula_iv_hotspots_svg, "NO HOT SPOT HIDES WITHIN"),
            (tabulae.build_tabula_v_canon_svg, "READ BACKWARD FROM THE OCTAVE"),
            (tabulae2.build_tabula_vi_vault_svg, "THREE DIMENSIONS BREAK THE PERIOD"),
        ]
        allowed_strokes = {"#161918", "#a32b24"}
        with tempfile.TemporaryDirectory() as tmp:
            for idx, (fn, expected_lifted) in enumerate(builders, start=2):
                svg_path = Path(tmp) / f"tabula-{idx}.svg"
                plate = fn(svg_path)
                svg_txt = svg_path.read_text(encoding="utf-8")

                root = ET.fromstring(svg_txt)
                self.assertEqual(root.attrib.get("width"), "170.0mm")
                self.assertEqual(root.attrib.get("height"), "220.0mm")
                self.assertEqual(decode_lifted_pen_svg(svg_txt), expected_lifted)

                for st in plate.strokes:
                    for x, y in st["points"]:
                        self.assertTrue(8.0 <= x <= 162.0 and 10.0 <= y <= 210.0, f"Out-of-bounds stroke pt ({x}, {y})")

                for elem in root.iter():
                    sc = elem.attrib.get("stroke")
                    if sc and sc != "none":
                        self.assertIn(sc, allowed_strokes)

    def test_96dpi_vellum_shader_washes(self):
        with tempfile.TemporaryDirectory() as tmp:
            arrays = {}
            for mode in ("hopf", "mobius", "hotspots", "canon", "aperiodic"):
                out_p = Path(tmp) / f"wash-{mode}.png"
                vellum.export_wash_png(out_p, wash_mode=mode, seed=17, profile="full")
                with Image.open(out_p) as im:
                    self.assertEqual(im.size, (672, 960))
                    arr = np.asarray(im, dtype=np.float32)
                    arrays[mode] = arr
                    self.assertGreater(float(np.percentile(arr.mean(axis=2), 95)), 190.0)

            again = np.asarray(vellum.make_texture(0, seed=17, profile="full", wash_mode="aperiodic"), dtype=np.float32)
            np.testing.assert_array_equal(arrays["aperiodic"], again)
            self.assertGreater(float(np.mean(np.abs(arrays["aperiodic"] - arrays["canon"]))), 0.4)



    def test_skew_vault_polymetric_canon_invariants_and_audio(self):
        info = skew_canon_mod.verify_skew_canon_invariants()
        self.assertEqual(info["d2_minimal_period"], 12)
        self.assertEqual(info["d3_steps_verified"], 128)

        with tempfile.TemporaryDirectory() as tmp:
            wav_p = Path(tmp) / "skew_canon.wav"
            pd_p = Path(tmp) / "skew_canon.pd"
            meta = skew_canon_mod.render_skew_canon_wav(wav_p)
            skew_canon_mod.export_pure_data_patch(pd_p)
            self.assertTrue(wav_p.is_file() and pd_p.is_file())
            self.assertAlmostEqual(meta["peak_dbfs"], -1.4, delta=0.15)

            with wave.open(str(wav_p), "rb") as wf:
                self.assertEqual(wf.getnchannels(), 2)
                self.assertEqual(wf.getframerate(), 48000)
                self.assertGreater(wf.getnframes(), 48000 * 45)

            pd_lines = [ln.strip() for ln in pd_p.read_text(encoding="utf-8").splitlines() if ln.strip()]
            self.assertTrue(pd_lines[0].startswith("#N canvas "))
            obj_lines = [ln for ln in pd_lines[1:] if ln.startswith("#X ") and not ln.startswith("#X connect ")]
            conn_lines = [ln for ln in pd_lines[1:] if ln.startswith("#X connect ")]
            self.assertGreaterEqual(len(obj_lines), 45)
            self.assertGreaterEqual(len(conn_lines), 55)
            for cln in conn_lines:
                self.assertTrue(cln.endswith(";"))
                parts = cln[:-1].split()
                self.assertEqual(len(parts), 6)
                src_i, out_i, dst_i, in_i = map(int, parts[2:])
                self.assertTrue(0 <= src_i < len(obj_lines))
                self.assertTrue(0 <= dst_i < len(obj_lines))



    def test_viol_acoustic_resonator_strict_hotspots_and_overtones(self):
        sol = solve_viol_acoustic_resonator()
        self.assertAlmostEqual(sol["mean_u2"], 0.0, places=10)
        self.assertTrue(sol["max_on_boundary"], "Global maximum of u_2 must lie strictly on the non-convex viol boundary.")
        self.assertTrue(sol["min_on_boundary"], "Global minimum of u_2 must lie strictly on the non-convex viol boundary.")
        self.assertGreater(sol["min_interior_grad"], 1e-4, "Interior gradient must vanish nowhere on smooth simply connected viol plate.")
        self.assertAlmostEqual(sol["freq_ratios"][1], 2.0, delta=0.02, msg="Pinched C-bouts tune mode u_3 near 2:1 octave.")

        geom = acoustic_resonator_geometry()
        self.assertGreater(len(geom["ink_strokes"]), 50)
        self.assertGreater(len(geom["red_strokes"]), 6)
        self.assertGreater(len(geom["sand_dots"]), 10)



    def test_godel_singlefold_pell_diagonal_and_rigidity(self):
        inv = verify_godel_singlefold_invariants()
        self.assertEqual(inv["automorphism_count"], 1, "Finite Turing-degree poset foil must have trivial Aut={id}.")
        self.assertEqual(len(inv["anti_diagonal"]), 8)

        geom = godel_diophantine_geometry()
        self.assertGreater(len(geom["ink_strokes"]), 60)
        self.assertGreater(len(geom["red_strokes"]), 15)


if __name__ == "__main__":
    unittest.main()
