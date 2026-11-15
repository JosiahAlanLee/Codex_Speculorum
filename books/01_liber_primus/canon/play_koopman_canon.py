#!/usr/bin/env python3
"""
books/01_liber_primus/canon/play_koopman_canon.py
=================================================
Playable Koopman / Raag Bhairav Crab Canon (`Canon Cancrizans Koopmanianus`):
  1. Verifies in exact `fractions.Fraction` arithmetic that Raag Bhairav's
     Just Intonation scale `(1/1, 16/15, 5/4, 4/3, 3/2, 8/5, 15/8, 2/1)` is
     strictly closed under multiplicative octave inversion `I(r) = 2 / r`, and
     that every vertical dyad in the 32-pulse Crab Canon is a pure 5-limit
     consonance (`1:1, 6:5, 5:4, 4:3, 3:2`).
  2. Synthesizes a 48.0-second `48 kHz` stereo WAV realization
     (`canon_cancrizans_bhairav_koopman.wav`) pairing a Jawari Rudra-Veena
     waveguide (`Vox Recta`, left-center) against a bowed/plucked phase-mirror
     voice (`Vox Cancrizans`, right-center) over an 8-mode Koopman spatial
     resonator drone (`Sa = C3 = 130.8128 Hz`, sub `C2 = 65.4064 Hz`).
  3. Exports a standalone Pure Data Vanilla patch (`koopman_raag_crab_canon.pd`)
     for live modular / VCV / Eurorack patching.
"""

from fractions import Fraction
import math
from pathlib import Path
from typing import Dict, List, Tuple
import wave

import numpy as np

SR = 48000
SA_HZ = 130.8127826502993  # C3 tonic (with C2 = 65.4064 Hz tambura sub)

BHAIRAV_DEGREES: List[Tuple[str, Fraction, Tuple[int, int]]] = [
    ("Sa",  Fraction(1, 1),   (1, 1)),  # 0: Fundamental breath mode
    ("r",   Fraction(16, 15), (1, 2)),  # 1: komal Re (boundary dipole + slow andolan)
    ("G",   Fraction(5, 4),   (2, 3)),  # 2: shuddha Ga (2:3 Chladni cross)
    ("m",   Fraction(4, 3),   (3, 4)),  # 3: shuddha Ma (3:4 nodal fourth)
    ("P",   Fraction(3, 2),   (3, 5)),  # 4: Pancham (3:5 anchor fifth)
    ("d",   Fraction(8, 5),   (4, 5)),  # 5: komal Dha (4:5 minor sixth + slow andolan)
    ("N",   Fraction(15, 8),  (5, 8)),  # 6: shuddha Ni (5:8 leading edge)
    ("S'",  Fraction(2, 1),   (2, 2)),  # 7: tar Sa (upper octave mirror)
]

SWARA_BY_RATIO: Dict[Fraction, str] = {r: name for name, r, _ in BHAIRAV_DEGREES}
DEGREE_INDEX_BY_RATIO: Dict[Fraction, int] = {r: i for i, (_, r, _) in enumerate(BHAIRAV_DEGREES)}
RATIO_BY_SWARA: Dict[str, Fraction] = {name: r for name, r, _ in BHAIRAV_DEGREES}

# 32-pulse (8 bars x 4 beats) contrapuntal Raag Bhairav Vox Recta:
# Opens on unison Sa (1:1), weaves independent 3rds/4ths against its own retrograde
# octave-inversion across Bars 1..8, and closes with the full 8-swara Bhairav arohana
# (`Sa - r - G - m - P - d - N - S'`) into upper-octave unison S' (2:1).
VOX_RECTA_SWARAS: List[str] = [
    # Bar 1: Poorvang call
    "Sa", "m",  "P",  "r",
    # Bar 2: Rising arch to komal Dha
    "G",  "m",  "P",  "d",
    # Bar 3: Symmetric Poorvang descent
    "P",  "m",  "G",  "r",
    # Bar 4: Approach to central mirror fold
    "Sa", "G",  "m",  "P",
    # Bar 5: Crossing the mirror axis (komal Dha -> Ga meend)
    "d",  "G",  "m",  "P",
    # Bar 6: Answering Poorvang descent
    "P",  "m",  "G",  "r",
    # Bar 7: Full Bhairav Arohana Part I
    "Sa", "r",  "G",  "m",
    # Bar 8: Full Bhairav Arohana Part II to tar Sa
    "P",  "d",  "N",  "S'",
]

ALLOWED_CONSONANCES = {
    Fraction(1, 1),
    Fraction(6, 5),
    Fraction(5, 4),
    Fraction(4, 3),
    Fraction(3, 2),
    Fraction(8, 5),
    Fraction(5, 3),
    Fraction(2, 1),
}


def build_canon_score() -> List[Dict]:
    """Returns the verified 32-step score table for Vox Recta and Vox Cancrizans."""
    recta_ratios = [RATIO_BY_SWARA[s] for s in VOX_RECTA_SWARAS]
    cancri_ratios = [Fraction(2, 1) / r for r in reversed(recta_ratios)]

    rows: List[Dict] = []
    for k in range(len(recta_ratios)):
        r_f = recta_ratios[k]
        r_c = cancri_ratios[k]
        hi = max(r_f, r_c)
        lo = min(r_f, r_c)
        dyad = hi / lo
        rows.append({
            "step": k,
            "bar": (k // 4) + 1,
            "beat": (k % 4) + 1,
            "recta_swara": SWARA_BY_RATIO[r_f],
            "recta_ratio": r_f,
            "recta_deg": DEGREE_INDEX_BY_RATIO[r_f],
            "cancri_swara": SWARA_BY_RATIO[r_c],
            "cancri_ratio": r_c,
            "cancri_deg": DEGREE_INDEX_BY_RATIO[r_c],
            "dyad_ratio": dyad,
        })
    return rows


def verify_canon_invariants() -> Dict:
    """Asserts exact Bhairav involution closure, crab-mirror symmetry, and 5-limit dyad purity."""
    bhairav_set = set(RATIO_BY_SWARA.values())
    for r in bhairav_set:
        inv = Fraction(2, 1) / r
        assert inv in bhairav_set, f"Octave inverse {inv} of {r} leaves Raag Bhairav!"

    score = build_canon_score()
    n = len(score)
    assert n == 32
    non_unison = 0
    for k, row in enumerate(score):
        mirror_row = score[n - 1 - k]
        prod = row["recta_ratio"] * mirror_row["cancri_ratio"]
        assert prod == Fraction(2, 1), f"Step {k}: mirror product {prod} != 2/1"
        assert row["dyad_ratio"] in ALLOWED_CONSONANCES, (
            f"Step {k} ({row['recta_swara']} vs {row['cancri_swara']}): "
            f"vertical dyad {row['dyad_ratio']} not in 5-limit consonance set!"
        )
        if row["dyad_ratio"] != Fraction(1, 1):
            non_unison += 1
    assert non_unison == 30, f"Expected 30 contrapuntal non-unison interior beats, got {non_unison}"
    return {"steps": n, "non_unison": non_unison, "consonances": sorted({str(r["dyad_ratio"]) for r in score})}


def _synth_jawari_pluck(freq_hz: float, dur_s: float, andolan: bool = False, bright: float = 1.0) -> np.ndarray:
    n = int(round(dur_s * SR))
    t = np.arange(n, dtype=np.float64) / SR
    if andolan:
        f_inst = freq_hz * (1.0 + 0.0085 * np.sin(2.0 * math.pi * 2.15 * t) * (1.0 - np.exp(-t / 0.18)))
    else:
        f_inst = np.full_like(t, freq_hz)

    ph = np.cumsum(2.0 * math.pi * f_inst / SR)
    env_body = (1.0 - np.exp(-t / 0.006)) * np.exp(-t / (dur_s * 0.78))
    env_jawari = (1.0 - np.exp(-t / 0.015)) * np.exp(-t / (dur_s * 0.48))

    raw = (
        0.62 * np.sin(ph)
        + 0.24 * bright * np.sin(2.0 * ph + 0.35 * env_jawari * np.sin(ph))
        + 0.13 * bright * np.sin(3.0 * ph)
        + 0.07 * bright * np.sin(4.0 * ph) * env_jawari
        + 0.04 * bright * np.sin(5.0 * ph) * env_jawari
    )
    jawari = np.tanh(1.45 * raw) * env_body
    tail = min(n // 4, int(0.014 * SR))
    if tail > 1:
        jawari[-tail:] *= np.linspace(1.0, 0.0, tail)
    return jawari.astype(np.float32)


def _synth_cancri_mirror_voice(freq_hz: float, dur_s: float, andolan: bool = False) -> np.ndarray:
    n = int(round(dur_s * SR))
    t = np.arange(n, dtype=np.float64) / SR
    if andolan:
        f_inst = freq_hz * (1.0 - 0.0080 * np.sin(2.0 * math.pi * 2.15 * t) * (1.0 - np.exp(-t / 0.18)))
    else:
        f_inst = np.full_like(t, freq_hz)

    ph = np.cumsum(2.0 * math.pi * f_inst / SR)
    env = (1.0 - np.exp(-t / 0.024)) * np.exp(-t / (dur_s * 0.84))
    idx_mod = 0.85 * np.exp(-t / (dur_s * 0.42))
    sig = (0.68 * np.sin(ph + idx_mod * np.sin(2.0 * ph)) + 0.22 * np.sin(3.0 * ph) * np.exp(-t / 0.35)) * env
    tail = min(n // 4, int(0.016 * SR))
    if tail > 1:
        sig[-tail:] *= np.linspace(1.0, 0.0, tail)
    return sig.astype(np.float32)


def render_canon_wav(out_wav: Path, bpm: float = 88.0) -> Dict:
    """
    Renders a 48.0-second stereo 48 kHz WAV realization of the Koopman/Bhairav Crab Canon:
      - Pass I  (Beats 0..31):  Vox Recta exposition + Koopman modal shimmer over Sa-Pa tambura.
      - Turnaround Bell:        Octave-axis bronze bell marking the retrograde inversion fold.
      - Pass II (Beats 32..63): Simultaneous 2-voice Crab Canon (Vox Recta + Vox Cancrizans).
      - Coda:                   Pure 1:1 / 3:2 / 2:1 Sa-Pa-Sa' resolution decaying cleanly.
    """
    verify_canon_invariants()
    score = build_canon_score()

    beat_s = 60.0 / bpm
    pass_beats = len(score)
    coda_s = 4.363636
    total_s = 2 * pass_beats * beat_s + coda_s
    n_samp = int(round(total_s * SR))

    mix_l = np.zeros(n_samp, dtype=np.float32)
    mix_r = np.zeros(n_samp, dtype=np.float32)

    t_all = np.arange(n_samp, dtype=np.float64) / SR
    sa_sub = SA_HZ * 0.5
    pa_sub = sa_sub * 1.5
    breath_l = 0.5 + 0.5 * np.sin(2.0 * math.pi * 0.11 * t_all)
    breath_r = 0.5 + 0.5 * np.cos(2.0 * math.pi * 0.09 * t_all)
    drone_sa = np.tanh(1.3 * (0.70 * np.sin(2 * math.pi * sa_sub * t_all) + 0.22 * np.sin(4 * math.pi * sa_sub * t_all)))
    drone_pa = np.tanh(1.2 * (0.55 * np.sin(2 * math.pi * pa_sub * t_all) + 0.18 * np.sin(4 * math.pi * pa_sub * t_all)))

    drone_env = np.ones(n_samp, dtype=np.float64)
    fade_in = int(1.4 * SR)
    fade_out = int(3.6 * SR)
    drone_env[:fade_in] = np.linspace(0.0, 1.0, fade_in)
    drone_env[-fade_out:] = np.linspace(1.0, 0.0, fade_out) ** 1.4

    mix_l += (0.13 * drone_sa * (0.7 + 0.3 * breath_l) + 0.08 * drone_pa * breath_r).astype(np.float32) * drone_env.astype(np.float32)
    mix_r += (0.13 * drone_sa * (0.7 + 0.3 * breath_r) + 0.08 * drone_pa * breath_l).astype(np.float32) * drone_env.astype(np.float32)

    def place_stereo(i0: int, sig: np.ndarray, gain: float, pan: float) -> None:
        end = min(n_samp, i0 + len(sig))
        if end <= i0:
            return
        seg = sig[: end - i0]
        ang = (pan + 1.0) * (math.pi * 0.25)
        gl, gr = gain * math.cos(ang), gain * math.sin(ang)
        mix_l[i0:end] += seg * gl
        mix_r[i0:end] += seg * gr

    for row in score:
        k = row["step"]
        i0 = int(round(k * beat_s * SR))
        f_r = SA_HZ * float(row["recta_ratio"])
        note_r = _synth_jawari_pluck(f_r, beat_s * 1.35, andolan=(row["recta_swara"] in ("r", "d")), bright=0.92)
        place_stereo(i0, note_r, gain=0.40, pan=-0.28)

        f_k = SA_HZ * float(row["cancri_ratio"]) * 2.0
        n_sh = int(round(beat_s * 0.9 * SR))
        ts = np.arange(n_sh, dtype=np.float64) / SR
        shimmer = (np.sin(2.0 * math.pi * f_k * ts) * np.exp(-ts / 0.26) * (1.0 - np.exp(-ts / 0.02))).astype(np.float32)
        place_stereo(i0, shimmer, gain=0.045, pan=0.45)

    i_turn = int(round(pass_beats * beat_s * SR))
    tb = np.arange(int(2.4 * SR), dtype=np.float64) / SR
    bell = (
        0.55 * np.sin(2.0 * math.pi * (SA_HZ * 2.0) * tb) * np.exp(-tb / 0.85)
        + 0.30 * np.sin(2.0 * math.pi * (SA_HZ * 3.0) * tb) * np.exp(-tb / 0.50)
        + 0.15 * np.sin(2.0 * math.pi * (SA_HZ * 4.0) * tb) * np.exp(-tb / 0.28)
    ).astype(np.float32)
    place_stereo(i_turn, bell, gain=0.22, pan=0.0)

    for row in score:
        k = row["step"]
        i0 = int(round((pass_beats + k) * beat_s * SR))
        f_r = SA_HZ * float(row["recta_ratio"])
        f_c = SA_HZ * float(row["cancri_ratio"])
        note_r = _synth_jawari_pluck(f_r, beat_s * 1.40, andolan=(row["recta_swara"] in ("r", "d")), bright=1.0)
        note_c = _synth_cancri_mirror_voice(f_c, beat_s * 1.42, andolan=(row["cancri_swara"] in ("r", "d")))
        place_stereo(i0, note_r, gain=0.38, pan=-0.46)
        place_stereo(i0, note_c, gain=0.38, pan=+0.46)

    i_coda = int(round(2 * pass_beats * beat_s * SR))
    dur_rem = max(0.5, (n_samp - i_coda) / SR)
    place_stereo(i_coda, _synth_jawari_pluck(SA_HZ, dur_rem, False, 0.8), gain=0.32, pan=-0.25)
    place_stereo(i_coda, _synth_cancri_mirror_voice(SA_HZ * 1.5, dur_rem, False), gain=0.24, pan=0.0)
    place_stereo(i_coda, _synth_cancri_mirror_voice(SA_HZ * 2.0, dur_rem, False), gain=0.30, pan=+0.25)

    d_l = int(0.341 * SR)
    d_r = int(0.454 * SR)
    wet_l = np.zeros_like(mix_l)
    wet_r = np.zeros_like(mix_r)
    wet_l[d_l:] = mix_r[:-d_l] * 0.16
    wet_r[d_r:] = mix_l[:-d_r] * 0.16
    out_l = mix_l + wet_l
    out_r = mix_r + wet_r

    peak = float(max(np.max(np.abs(out_l)), np.max(np.abs(out_r)), 1e-6))
    target_lin = 10.0 ** (-1.4 / 20.0)
    scale = target_lin / peak
    stereo = np.stack([out_l * scale, out_r * scale], axis=-1)
    pcm16 = np.clip(np.round(stereo * 32767.0), -32768, 32767).astype(np.int16)

    out_wav.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out_wav), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(pcm16.tobytes())

    return {
        "wav_path": str(out_wav),
        "duration_s": round(n_samp / SR, 3),
        "peak_dbfs": round(20.0 * math.log10(float(np.max(np.abs(stereo)))), 2),
    }


def export_pure_data_patch(out_pd: Path) -> Path:
    """Writes a self-contained Pure Data Vanilla patch running the 32-step Koopman/Bhairav Crab Canon."""
    score = build_canon_score()
    recta_floats = " ".join(f"{float(r['recta_ratio']):.6f}" for r in score)
    cancri_floats = " ".join(f"{float(r['cancri_ratio']):.6f}" for r in score)

    lines = [
        "#N canvas 80 60 880 620 10;",
        "#X text 28 20 CODEX SPECULORUM :: LIBER I — CANON CANCRIZANS KOOPMANIANUS (RAAG BHAIRAV JUST INTONATION);",
        "#X text 28 40 Exact Octave-Inversion Crab Canon: Vox_Recta[k] * Vox_Cancrizans[31 - k] = 2/1 across all 32 steps (Sa = 130.8128 Hz);",
        "#X obj 28 76 loadbang;",
        "#X msg 28 104 \\; pd dsp 1;",
        "#X obj 140 76 tgl 20 0 empty empty RUN_CANON 17 7 0 10 -262144 -1 -1 1 1;",
        "#X obj 140 106 metro 681.818;",
        "#X obj 140 136 f 0;",
        "#X obj 190 136 + 1;",
        "#X obj 235 136 mod 32;",
        "#X obj 28 176 table bhairav_recta 32;",
        "#X obj 230 176 table bhairav_cancri 32;",
        f"#X msg 28 208 \\; bhairav_recta 0 {recta_floats};",
        f"#X msg 28 248 \\; bhairav_cancri 0 {cancri_floats};",
        "#X obj 140 296 tabread bhairav_recta;",
        "#X obj 360 296 tabread bhairav_cancri;",
        "#X obj 140 326 * 130.8128;",
        "#X obj 360 326 * 130.8128;",
        "#X obj 140 356 pack f 45;",
        "#X obj 360 356 pack f 45;",
        "#X obj 140 386 line~;",
        "#X obj 360 386 line~;",
        "#X obj 140 416 phasor~;",
        "#X obj 360 416 osc~;",
        "#X obj 140 446 cos~;",
        "#X obj 140 476 *~ 0.22;",
        "#X obj 360 476 *~ 0.22;",
        "#X obj 560 386 osc~ 65.4064;",
        "#X obj 560 416 *~ 0.11;",
        "#X obj 240 536 dac~ 1 2;",
        "#X connect 2 0 3 0;",
        "#X connect 2 0 11 0;",
        "#X connect 2 0 12 0;",
        "#X connect 2 0 4 0;",
        "#X connect 4 0 5 0;",
        "#X connect 5 0 6 0;",
        "#X connect 6 0 7 0;",
        "#X connect 7 0 8 0;",
        "#X connect 8 0 6 1;",
        "#X connect 6 0 13 0;",
        "#X connect 6 0 14 0;",
        "#X connect 13 0 15 0;",
        "#X connect 14 0 16 0;",
        "#X connect 15 0 17 0;",
        "#X connect 16 0 18 0;",
        "#X connect 17 0 19 0;",
        "#X connect 18 0 20 0;",
        "#X connect 19 0 21 0;",
        "#X connect 20 0 22 0;",
        "#X connect 21 0 23 0;",
        "#X connect 23 0 24 0;",
        "#X connect 22 0 25 0;",
        "#X connect 26 0 27 0;",
        "#X connect 24 0 28 0;",
        "#X connect 25 0 28 1;",
        "#X connect 27 0 28 0;",
        "#X connect 27 0 28 1;",
    ]
    out_pd.parent.mkdir(parents=True, exist_ok=True)
    out_pd.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_pd


if __name__ == "__main__":
    here = Path(__file__).resolve().parent
    info = render_canon_wav(here / "out" / "canon_cancrizans_bhairav_koopman.wav")
    export_pure_data_patch(here / "out" / "koopman_raag_crab_canon.pd")
    print("[canon]", info)
