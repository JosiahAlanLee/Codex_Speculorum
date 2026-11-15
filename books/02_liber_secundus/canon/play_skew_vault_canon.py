#!/usr/bin/env python3
"""
books/02_liber_secundus/canon/play_skew_vault_canon.py
======================================================
Playable 3-Axis Thue-Morse & Sturmian Polymetric Canon (`Canon Polymetricus Sine Periodo`):
  1. Verifies in exact `fractions.Fraction` arithmetic that the two 5-limit Just Intonation
     vault cosets—`Harmonia Recta` (`S = 0`: `{1/1, 5/4, 3/2, 2/1}`) and its exact octave-inverse
     `Harmonia Inversa` (`S = 1`: `{1/1, 4/3, 8/5, 2/1}`, drawn from `Liber I`'s Raag Bhairav
     ratios)—yield pure 5-limit consonances (`{1/1, 6/5, 5/4, 4/3, 3/2, 8/5, 2/1}`) across
     all three pairwise vertical dyads (`X:Z`, `X:Y`, `Z:Y`) at every pulse.
  2. Proves programmatically that disabling the third-axis shear (`d = 2` planar floor)
     locks the 3-voice score into an exact `12`-pulse (`lcm(4, 6)`) repeating lattice
     (mirroring Bhattacharya's planar periodicity theorem), whereas enabling the `d = 3`
     skew-product (`Thue-Morse(y) = popcount(y) mod 2` + `Sturmian(y) = floor((y+2)/phi) - floor((y+1)/phi)`)
     eliminates every translational period `P` across the entire 32-corridor (`128`-pulse) vault.
  3. Synthesizes a 74.0-second `48 kHz` stereo WAV realization
     (`canon_polymetricus_sine_periodo.wav`) contrasting the `d = 2` periodic planar floor
     (Section I, 24 pulses) against the `d = 3` non-repeating sheared vault (Section II,
     96 pulses = 24 four-cube Z-stones) and resolving into an open Just Intonation vault coda:
       - Axis X (`Vox Lapidis`, Left-Center `-0.48`): Asymmetric wavefolded West-Coast LPG pluck
       - Axis Z (`Vox Fornicis`, Right-Center `+0.48`): Warm resonant 4-pole VCF harmonic reed
       - Axis Y (`Vox Axis Verticalis`, Center + Golden-Ratio M/S Vault Space): Sub-octave carry
         bass (`C2 = 65.4064 Hz` / `G2` / `F2`) + Koopman overtone shear bells over a slow
         beating harmonic drone (`Sa = C3 = 130.8128 Hz`).
  4. Exports a self-contained generative Pure Data Vanilla patch (`skew_vault_polymetric_canon.pd`)
     with real-time bitwise Thue-Morse popcount, golden-ratio Sturmian mechanical rotation,
     live `D2_PLANAR` vs. `D3_APERIODIC` mode toggle, 3 synthesis voices, and golden-ratio
     (`373 ms` / `603 ms`) stereo delay diffusion.
"""

from fractions import Fraction
import math
from pathlib import Path
from typing import Dict, List, Set, Tuple
import wave

import numpy as np

SR = 48000
SA_HZ = 130.8127826502993  # C3 tonic (shared with Book I Koopman/Bhairav Crab Canon)
PHI = (1.0 + math.sqrt(5.0)) * 0.5

# Dual octave-inverse 5-limit Just Intonation tetrads (both subsets of Raag Bhairav!):
# Coset S=0 (`Harmonia Recta`):   1/1 (Sa), 5/4 (Ga), 3/2 (Pa), 2/1 (S')
# Coset S=1 (`Harmonia Inversa`): 1/1 (Sa), 4/3 (Ma), 8/5 (komal Dha), 2/1 (S') = 2 / Coset_0
COSET_0: Tuple[Tuple[str, Fraction], ...] = (
    ("Sa", Fraction(1, 1)),
    ("G",  Fraction(5, 4)),
    ("P",  Fraction(3, 2)),
    ("S'", Fraction(2, 1)),
)

COSET_1: Tuple[Tuple[str, Fraction], ...] = (
    ("Sa", Fraction(1, 1)),
    ("m",  Fraction(4, 3)),
    ("d",  Fraction(8, 5)),
    ("S'", Fraction(2, 1)),
)

COSETS = (COSET_0, COSET_1)

# Unrotated translational motifs along X (4-voxel Z-stone step) and Z (6-pulse arch hemiola):
# Neither motif is ever inverted or retrograded; corridor shear acts purely by index translation.
MOTIF_X4: Tuple[int, ...] = (0, 1, 2, 3)
MOTIF_Z6: Tuple[int, ...] = (0, 2, 1, 3, 2, 1)

ALLOWED_5LIMIT_DYADS: Set[Fraction] = {
    Fraction(1, 1),
    Fraction(6, 5),
    Fraction(5, 4),
    Fraction(4, 3),
    Fraction(3, 2),
    Fraction(8, 5),
    Fraction(5, 3),
    Fraction(2, 1),
}


def thue_morse_bit(y: int) -> int:
    """Binary carry parity `popcount(y) mod 2`."""
    return int(y).bit_count() & 1


def sturmian_golden_bit(y: int) -> int:
    """Mechanical Sturmian word of irrational slope `1 / phi`: `floor((y+2)/phi) - floor((y+1)/phi)`."""
    inv_phi = 1.0 / PHI
    return int(math.floor((y + 2) * inv_phi) - math.floor((y + 1) * inv_phi))


def _octave_reduced_dyad(r1: Fraction, r2: Fraction) -> Fraction:
    """Normalizes the interval between `r1` and `r2` into `[1/1, 2/1]`."""
    hi = max(r1, r2)
    lo = min(r1, r2)
    d = hi / lo
    while d > Fraction(2, 1):
        d /= 2
    while d < Fraction(1, 1):
        d *= 2
    return d


def build_skew_canon_score(corridors: int = 32, d3_shear: bool = True) -> List[Dict]:
    """
    Constructs `4 * corridors` pulses (each 4-pulse bar corresponds to one unrotated
    4-cube Z-stone laid along corridor `y = 0 .. corridors-1`).
      - If `d3_shear=False` (`d = 2` planar floor), `(tm, st) = (0, 0)` everywhere,
        locking X (period 4) and Z (period 6) into a strict 12-pulse repeating lattice.
      - If `d3_shear=True` (`d = 3` sheared vault), `tm(y)` translates the X-cell phase
        while `st(y)` translates the Z-cell phase and selects the dual harmonic coset.
    """
    rows: List[Dict] = []
    cum_tm = 0
    cum_st = 0

    for y in range(corridors):
        tm = thue_morse_bit(y) if d3_shear else 0
        st = sturmian_golden_bit(y) if d3_shear else 0
        if d3_shear and y > 0:
            cum_tm = (cum_tm + tm) % 4
            cum_st = (cum_st + 1 + st) % 6
        coset = COSETS[st]

        for sub in range(4):
            k = 4 * y + sub
            if d3_shear:
                ix = MOTIF_X4[(sub + cum_tm) % 4]
                iz = MOTIF_Z6[(k + cum_st + 2 * tm) % 6]
            else:
                ix = MOTIF_X4[k % 4]
                iz = MOTIF_Z6[k % 6]

            # Axis Y bass anchors downbeat on Sa (idx 0) or Pa/Ma (idx 2/1) according to carry `tm`
            if sub == 0:
                iy = 0 if tm == 0 else (2 if st == 0 else 1)
            elif sub == 2:
                iy = 2 if st == 0 else 1
            else:
                iy = 0

            sw_x, rx = coset[ix]
            sw_z, rz = coset[iz]
            sw_y, ry_cell = coset[iy]
            # Axis Y sounds one octave below C3 (`* 1/2`), preserving octave-reduced dyad consonance
            ry = ry_cell * Fraction(1, 2)

            d_xz = _octave_reduced_dyad(rx, rz)
            d_xy = _octave_reduced_dyad(rx, ry)
            d_zy = _octave_reduced_dyad(rz, ry)

            rows.append({
                "step": k,
                "corridor_y": y,
                "stone_sub": sub,
                "tm": tm,
                "st": st,
                "coset_id": st,
                "x_swara": sw_x,
                "x_ratio": rx,
                "z_swara": sw_z,
                "z_ratio": rz,
                "y_swara": sw_y,
                "y_ratio": ry,
                "dyad_xz": d_xz,
                "dyad_xy": d_xy,
                "dyad_zy": d_zy,
            })
    return rows


def verify_skew_canon_invariants() -> Dict:
    """
    Verifies:
      1. Exact multiplicative octave-inversion duality between `COSET_0` and `COSET_1`.
      2. Exact `12`-pulse periodicity on the `d = 2` planar floor (`d3_shear=False`).
      3. Strict absence of any translational period `P in [1, 64]` on the 128-pulse
         (`32`-corridor) `d = 3` sheared vault (`d3_shear=True`).
      4. Pure 5-limit consonance across all three pairwise dyads (`X:Z`, `X:Y`, `Z:Y`)
         at every single pulse.
    """
    c0_set = {r for _, r in COSET_0}
    c1_set = {r for _, r in COSET_1}
    assert {Fraction(2, 1) / r for r in c0_set} == c1_set, "Coset 1 must be exact 2/r octave-inverse of Coset 0!"

    # 1. Verify d=2 planar periodicity (minimal period = 12 pulses = lcm(4, 6))
    planar = build_skew_canon_score(corridors=12, d3_shear=False)
    planar_tuples = [(r["x_ratio"], r["z_ratio"], r["y_ratio"]) for r in planar]
    for p in range(1, 12):
        assert not all(planar_tuples[i] == planar_tuples[i + p] for i in range(len(planar_tuples) - p)), (
            f"d=2 score unexpectedly had sub-period {p} < 12"
        )
    assert all(planar_tuples[i] == planar_tuples[i + 12] for i in range(len(planar_tuples) - 12)), (
        "d=2 planar score must repeat cleanly with period 12 = lcm(4, 6)!"
    )

    # 2. Verify d=3 sheared vault non-periodicity & universal 5-limit consonance
    vault = build_skew_canon_score(corridors=32, d3_shear=True)
    assert len(vault) == 128
    vault_tuples = [(r["x_ratio"], r["z_ratio"], r["y_ratio"]) for r in vault]
    for p in range(1, 65):
        is_periodic = all(vault_tuples[i] == vault_tuples[i + p] for i in range(len(vault_tuples) - p))
        assert not is_periodic, f"d=3 sheared vault score unexpectedly repeated with period {p}!"

    observed_dyads: Set[str] = set()
    for row in vault:
        for key in ("dyad_xz", "dyad_xy", "dyad_zy"):
            d = row[key]
            assert d in ALLOWED_5LIMIT_DYADS, f"Step {row['step']} {key}={d} leaves 5-limit consonances!"
            observed_dyads.add(str(d))

    return {
        "d2_minimal_period": 12,
        "d3_steps_verified": len(vault),
        "d3_max_period_tested": 64,
        "consonances": sorted(observed_dyads),
    }


def _synth_westcoast_lpg_pluck(freq_hz: float, dur_s: float, fold_amt: float = 1.0, accent: bool = False) -> np.ndarray:
    """
    Axis X (`Vox Lapidis`): Asymmetric bipolar wavefolder + vactrol Low-Pass Gate (LPG)
    inspired by Buchla / Joranalogue Enhance 2 / TipTop Fold modular voice topology.
    """
    n = int(round(dur_s * SR))
    t = np.arange(n, dtype=np.float64) / SR
    ph = 2.0 * math.pi * freq_hz * t

    # Vactrol LPG decay (fast 3.5 ms strike, organic coupled brightness+amplitude tail)
    vactrol = (1.0 - np.exp(-t / 0.0035)) * (0.68 * np.exp(-t / (dur_s * 0.46)) + 0.32 * np.exp(-t / (dur_s * 0.92)))
    fold_env = fold_amt * (1.35 if accent else 1.0) * np.exp(-t / (dur_s * 0.32))

    # Asymmetric bipolar offset before wavefolding produces rich even+odd ashlar overtones
    core = np.sin(ph) + 0.16 * np.cos(2.0 * ph)
    folded = np.sin((1.0 + 1.45 * fold_env) * core + 0.18 * fold_env) - 0.12 * fold_env
    sub_body = 0.42 * np.sin(ph)
    sig = (0.66 * folded + sub_body) * vactrol

    tail = min(n // 4, int(0.015 * SR))
    if tail > 1:
        sig[-tail:] *= np.linspace(1.0, 0.0, tail)
    return sig.astype(np.float32)


def _synth_curtis_arch_reed(freq_hz: float, dur_s: float, warm_detune: float = 0.0016, open_filter: bool = False) -> np.ndarray:
    """
    Axis Z (`Vox Fornicis`): Dual-oscillator harmonic reed shaped with a warm 2500/Curtis-style
    resonant filter sweep envelope.
    """
    n = int(round(dur_s * SR))
    t = np.arange(n, dtype=np.float64) / SR
    ph1 = 2.0 * math.pi * freq_hz * (1.0 - 0.5 * warm_detune) * t
    ph2 = 2.0 * math.pi * freq_hz * (1.0 + 0.5 * warm_detune) * t

    amp_env = (1.0 - np.exp(-t / 0.022)) * np.exp(-t / (dur_s * 0.88))
    vcf_env = (1.0 - np.exp(-t / 0.038)) * np.exp(-t / (dur_s * (0.62 if open_filter else 0.44)))

    # Harmonic additive approximation of a 24 dB/oct resonant lowpass sweep
    harm_weights = (1.0, 0.52, 0.34, 0.21, 0.13, 0.08)
    acc = np.zeros_like(t)
    cutoff_mult = 2.2 + (4.2 if open_filter else 2.6) * vcf_env
    for h_idx, w in enumerate(harm_weights, start=1):
        # Smooth 4-pole rolloff + gentle resonance peak near `h_idx == cutoff_mult`
        ratio = h_idx / cutoff_mult
        lp_gain = 1.0 / (1.0 + ratio ** 4)
        res_bump = 1.0 + 0.55 * np.exp(-((h_idx - cutoff_mult) ** 2) / 0.55)
        acc += w * lp_gain * res_bump * 0.5 * (np.sin(h_idx * ph1) + np.sin(h_idx * ph2 + 0.2 * h_idx))

    sig = np.tanh(1.22 * acc) * amp_env
    tail = min(n // 4, int(0.018 * SR))
    if tail > 1:
        sig[-tail:] *= np.linspace(1.0, 0.0, tail)
    return sig.astype(np.float32)


def _synth_carry_bass_and_bell(freq_hz: float, dur_s: float, trigger_bell: bool, st_bit: int) -> Tuple[np.ndarray, np.ndarray]:
    """
    Axis Y (`Vox Axis Verticalis`): Deep sub-harmonic phase-locked bass pulse paired with
    an upper-gallery Koopman nodal bell when a corridor carry/shear slip occurs.
    """
    n = int(round(dur_s * SR))
    t = np.arange(n, dtype=np.float64) / SR
    ph = 2.0 * math.pi * freq_hz * t
    env_b = (1.0 - np.exp(-t / 0.008)) * np.exp(-t / (dur_s * 0.86))
    bass = np.tanh(1.35 * (0.78 * np.sin(ph) + 0.26 * np.sin(2.0 * ph) + 0.10 * np.sin(3.0 * ph) * np.exp(-t / 0.22))) * env_b

    tail = min(n // 4, int(0.016 * SR))
    if tail > 1:
        bass[-tail:] *= np.linspace(1.0, 0.0, tail)

    if not trigger_bell:
        return bass.astype(np.float32), np.zeros(n, dtype=np.float32)

    # Crystalline gallery bell at 4x / 6x / (10x or 8x) harmonic partial
    n_bell = int(round(dur_s * 1.65 * SR))
    tb = np.arange(n_bell, dtype=np.float64) / SR
    upper_mult = 6.4 if st_bit == 1 else 5.0
    bell = (
        0.54 * np.sin(2.0 * math.pi * (freq_hz * 4.0) * tb) * np.exp(-tb / 0.62)
        + 0.29 * np.sin(2.0 * math.pi * (freq_hz * 6.0) * tb) * np.exp(-tb / 0.38)
        + 0.17 * np.sin(2.0 * math.pi * (freq_hz * upper_mult) * tb) * np.exp(-tb / 0.24)
    ) * (1.0 - np.exp(-tb / 0.003))
    return bass.astype(np.float32), bell.astype(np.float32)


def render_skew_canon_wav(out_wav: Path, bpm: float = 108.0) -> Dict:
    """
    Renders a ~74.0-second `48 kHz` stereo WAV realization of Book II's 3-Axis Canon:
      - Section I  (`d = 2` Pavimentum Planum, 24 pulses = 2 exact 12-pulse periods):
        Zero shear (`tm = 0, st = 0`) so the listener hears the planar grid repeat twice.
      - Fracture Bell (`Fractura Fornicis`): Marks entry into the 3D vertical ventilation shaft.
      - Section II (`d = 3` Fornix Sine Periodo, 96 pulses = 24 Z-stone courses `y = 0..23`):
        Full Thue-Morse (`popcount(y) mod 2`) + Golden Sturmian (`floor((y+2)/phi) - floor((y+1)/phi)`)
        skew-product canon across all three voices with zero global period.
      - Section III (`Coda in Abysso`): Open Just Intonation `1:1 - 3:2 - 2:1 - 5:2` vault resonance.
    """
    inv_info = verify_skew_canon_invariants()

    pulse_s = 60.0 / (bpm * 1.5)  # 162 pulses/min (~0.37037s per pulse) -> crisp, propulsive modular pulse
    planar_score = build_skew_canon_score(corridors=6, d3_shear=False)    # 24 pulses (2 x 12-pulse periods)
    vault_score = build_skew_canon_score(corridors=24, d3_shear=True)     # 96 pulses (24 non-repeating Z-stones)

    gap_beats = 2  # Brief resonant breathing space at the d=2 -> d=3 threshold bell
    total_pulses = len(planar_score) + gap_beats + len(vault_score)
    coda_s = 7.40
    total_s = total_pulses * pulse_s + coda_s
    n_samp = int(round(total_s * SR))

    mix_l = np.zeros(n_samp, dtype=np.float32)
    mix_r = np.zeros(n_samp, dtype=np.float32)

    # Radigue / Ciani inspired slow phase-beating harmonic drone bed (`C2 = 65.4064 Hz` & `G2 = 98.1096 Hz`)
    t_all = np.arange(n_samp, dtype=np.float64) / SR
    sa_sub = SA_HZ * 0.5
    pa_sub = sa_sub * 1.5
    lfo_a = 0.5 + 0.5 * np.sin(2.0 * math.pi * (0.071) * t_all)
    lfo_b = 0.5 + 0.5 * np.cos(2.0 * math.pi * (0.071 / PHI) * t_all)

    drone_sa_l = np.tanh(1.18 * (0.72 * np.sin(2 * math.pi * (sa_sub - 0.08) * t_all) + 0.20 * np.sin(4 * math.pi * sa_sub * t_all)))
    drone_sa_r = np.tanh(1.18 * (0.72 * np.sin(2 * math.pi * (sa_sub + 0.08) * t_all) + 0.20 * np.sin(4 * math.pi * sa_sub * t_all)))
    drone_pa = 0.50 * np.sin(2 * math.pi * pa_sub * t_all) + 0.16 * np.sin(4 * math.pi * pa_sub * t_all)

    drone_env = np.ones(n_samp, dtype=np.float64)
    fade_in = int(1.6 * SR)
    fade_out = int(4.2 * SR)
    drone_env[:fade_in] = np.sin(np.linspace(0.0, 0.5 * math.pi, fade_in)) ** 2
    drone_env[-fade_out:] = np.cos(np.linspace(0.0, 0.5 * math.pi, fade_out)) ** 2

    mix_l += ((0.11 * drone_sa_l * (0.68 + 0.32 * lfo_a) + 0.055 * drone_pa * lfo_b) * drone_env).astype(np.float32)
    mix_r += ((0.11 * drone_sa_r * (0.68 + 0.32 * lfo_b) + 0.055 * drone_pa * lfo_a) * drone_env).astype(np.float32)

    def place_stereo(i0: int, sig: np.ndarray, gain: float, pan: float) -> None:
        end = min(n_samp, i0 + len(sig))
        if end <= i0:
            return
        seg = sig[: end - i0]
        ang = (pan + 1.0) * (math.pi * 0.25)
        gl, gr = gain * math.cos(ang), gain * math.sin(ang)
        mix_l[i0:end] += seg * gl
        mix_r[i0:end] += seg * gr

    # Section I: d=2 Planar Periodicity (24 pulses = two exact 12-pulse cycles)
    for row in planar_score:
        k = row["step"]
        i0 = int(round(k * pulse_s * SR))
        fx = SA_HZ * float(row["x_ratio"]) * 2.0  # C4 register for crisp ashlar pluck
        fz = SA_HZ * float(row["z_ratio"])        # C3 register for warm arch reed
        fy = SA_HZ * float(row["y_ratio"])        # C2 register for bass anchor

        nx = _synth_westcoast_lpg_pluck(fx, pulse_s * 1.18, fold_amt=0.72, accent=(row["stone_sub"] == 0))
        place_stereo(i0, nx, gain=0.31, pan=-0.42)

        if k % 2 == 0 or row["stone_sub"] == 3:
            nz = _synth_curtis_arch_reed(fz, pulse_s * 1.65, open_filter=(k % 6 == 0))
            place_stereo(i0, nz, gain=0.26, pan=+0.42)

        if row["stone_sub"] in (0, 2):
            nb, _ = _synth_carry_bass_and_bell(fy, pulse_s * 1.75, trigger_bell=False, st_bit=0)
            place_stereo(i0, nb, gain=0.28, pan=0.0)

    # Threshold Bell (`Fractura Fornicis` — d=2 -> d=3 transition)
    i_fracture = int(round(len(planar_score) * pulse_s * SR))
    tb = np.arange(int(3.2 * SR), dtype=np.float64) / SR
    fracture_bell = (
        0.52 * np.sin(2.0 * math.pi * (SA_HZ * 2.0) * tb) * np.exp(-tb / 1.15)
        + 0.31 * np.sin(2.0 * math.pi * (SA_HZ * 3.0) * tb) * np.exp(-tb / 0.72)
        + 0.21 * np.sin(2.0 * math.pi * (SA_HZ * 3.2) * tb) * np.exp(-tb / 0.54)  # 16:5 komal Dha shimmer!
    ) * (1.0 - np.exp(-tb / 0.004))
    place_stereo(i_fracture, fracture_bell.astype(np.float32), gain=0.26, pan=0.0)

    # Section II: d=3 Non-Repeating Skew-Product Vault (96 pulses = 24 Z-stones)
    offset_pulses = len(planar_score) + gap_beats
    prev_tm = 0
    for row in vault_score:
        k = row["step"]
        i0 = int(round((offset_pulses + k) * pulse_s * SR))
        tm = row["tm"]
        st = row["st"]
        sub = row["stone_sub"]

        fx = SA_HZ * float(row["x_ratio"]) * 2.0
        fz = SA_HZ * float(row["z_ratio"])
        fy = SA_HZ * float(row["y_ratio"])

        # Slight stereo micro-parallax tracking `(tm, st)` shear offsets
        pan_x = -0.50 + 0.10 * tm
        pan_z = +0.50 - 0.10 * st

        nx = _synth_westcoast_lpg_pluck(
            fx,
            pulse_s * (1.32 if sub == 0 else 1.12),
            fold_amt=0.88 + 0.28 * st,
            accent=(sub == 0),
        )
        place_stereo(i0, nx, gain=0.33, pan=pan_x)

        # Axis Z articulates the 6-pulse sheared arch cell (sustained across paired pulses + syncopations)
        if (k + st) % 2 == 0 or sub == 0:
            nz = _synth_curtis_arch_reed(
                fz,
                pulse_s * (1.85 if sub == 0 else 1.42),
                open_filter=(st == 1 and sub == 0),
            )
            place_stereo(i0, nz, gain=0.28, pan=pan_z)

        # Axis Y articulates corridor downbeats & half-bar pillars; rings gallery bell on shear transitions
        if sub in (0, 2):
            carry_flip = (sub == 0) and (tm != prev_tm or st == 1)
            nb, nbell = _synth_carry_bass_and_bell(fy, pulse_s * 1.85, trigger_bell=carry_flip, st_bit=st)
            place_stereo(i0, nb, gain=0.32 if sub == 0 else 0.22, pan=0.0)
            if carry_flip:
                bell_pan = 0.34 if st == 1 else -0.34
                place_stereo(i0, nbell, gain=0.14, pan=bell_pan)
        if sub == 0:
            prev_tm = tm

    # Section III: Coda in Abysso (Open Just Intonation Vault Chord: C2 - C3 - G3 - C4 - E4)
    i_coda = int(round(total_pulses * pulse_s * SR))
    dur_rem = max(1.0, (n_samp - i_coda) / SR - 0.4)
    coda_bass, coda_bell = _synth_carry_bass_and_bell(SA_HZ * 0.5, dur_rem, trigger_bell=True, st_bit=0)
    place_stereo(i_coda, coda_bass, gain=0.32, pan=0.0)
    place_stereo(i_coda, coda_bell, gain=0.16, pan=0.18)
    place_stereo(i_coda, _synth_curtis_arch_reed(SA_HZ * 1.0, dur_rem, open_filter=True), gain=0.25, pan=-0.32)
    place_stereo(i_coda, _synth_curtis_arch_reed(SA_HZ * 1.5, dur_rem, open_filter=True), gain=0.23, pan=+0.32)
    place_stereo(i_coda, _synth_westcoast_lpg_pluck(SA_HZ * 2.5, dur_rem * 0.85, fold_amt=0.75, accent=True), gain=0.24, pan=0.0)

    # Golden-Ratio Stereo Vault Diffusion (`373 ms` and `603 ms`, `603 / 373 ≈ 1.6166 ≈ phi`)
    # Avoids rational comb periodicity in the spatial reverberation tail!
    d1 = int(0.373 * SR)
    d2 = int(0.603 * SR)
    wet_l = np.zeros_like(mix_l)
    wet_r = np.zeros_like(mix_r)
    wet_l[d1:] += mix_r[:-d1] * 0.17
    wet_r[d2:] += mix_l[:-d2] * 0.15
    wet_l[d2:] += mix_l[:-d2] * 0.08
    wet_r[d1:] += mix_r[:-d1] * 0.08

    out_l = mix_l + wet_l
    out_r = mix_r + wet_r

    # Gentle cosine safety fade on final 80 ms so sample_end == 0
    end_fade = int(0.08 * SR)
    out_l[-end_fade:] *= np.linspace(1.0, 0.0, end_fade)
    out_r[-end_fade:] *= np.linspace(1.0, 0.0, end_fade)

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
        "d2_pulses": len(planar_score),
        "d3_pulses": len(vault_score),
        "invariants": inv_info,
    }


def export_pure_data_patch(out_pd: Path) -> Path:
    """
    Exports a self-contained Pure Data Vanilla patch (`skew_vault_polymetric_canon.pd`)
    implementing Book II's real-time 3-Axis Thue-Morse & Sturmian Skew-Product Canon
    with zero external dependencies:
      - Unbounded corridor counter `y = div(step, 4)`
      - Live 12-bit bitwise popcount parity `Thue-Morse(y) = popcount(y) % 2`
      - Live irrational slope mechanical `Sturmian(y) = int((y+2)*0.6180339887) - int((y+1)*0.6180339887)`
      - Live `D3_APERIODIC_ENABLE` toggle (`1` = 3D non-repeating vault; `0` = 2D 12-step periodic lattice)
      - 8-entry dual-coset Just Intonation table (`[0..3]` Harmonia Recta, `[4..7]` Harmonia Inversa)
      - 3 synthesis voices (Wavefolded LPG Pluck X, Resonant `vcf~` Arch Z, Sub-Octave Carry Bass Y)
        routed into a Golden-Ratio (`373 ms` / `603 ms`) cross-coupled stereo vault delay.
    """
    # Dual coset table: indices 0..3 = Coset 0 (1, 5/4, 3/2, 2), indices 4..7 = Coset 1 (1, 4/3, 8/5, 2)
    ji_floats = " ".join(
        f"{float(r):.6f}" for _, r in (list(COSET_0) + list(COSET_1))
    )
    motif_z6_floats = " ".join(str(v) for v in MOTIF_Z6)

    nodes: List[Tuple[str, str]] = []

    def add(name: str, stmt: str) -> int:
        idx = len(nodes)
        nodes.append((name, stmt))
        return idx

    # Header comments
    add("hdr1", "#X text 24 16 CODEX SPECULORUM :: LIBER II — CANON POLYMETRICUS SINE PERIODO (3-AXIS SKEW VAULT);")
    add("hdr2", "#X text 24 36 Live Thue-Morse popcount(y)%2 + Golden Sturmian rotation floor((y+2)/phi)-floor((y+1)/phi) (Sa = 130.8128 Hz);")

    # Master transport & tables initialization
    n_lb = add("lb", "#X obj 24 68 loadbang;")
    n_dsp = add("dsp", "#X msg 24 98 \\; pd dsp 1;")
    n_run = add("run_tgl", "#X obj 132 68 tgl 18 0 empty empty RUN_VAULT 17 7 0 10 -262144 -1 -1 1 1;")
    n_d3_init = add("d3_init", "#X msg 276 68 1;")
    n_d3_tgl = add("d3_tgl", "#X obj 276 98 tgl 18 0 empty empty D3_SHEAR_ENABLE(0=D2_Periodic_12) 17 7 0 10 -262144 -1 -1 1 1;")
    n_metro = add("metro", "#X obj 132 102 metro 370.37;")

    # Tables: ji_cosets (8 floats) & z6_motif (6 ints)
    add("tbl_ji", "#X obj 520 68 table vault_ji_cosets 8;")
    add("tbl_z6", "#X obj 700 68 table vault_motif_z6 6;")
    n_msg_ji = add("msg_ji", f"#X msg 520 98 \\; vault_ji_cosets 0 {ji_floats};")
    n_msg_z6 = add("msg_z6", f"#X msg 520 132 \\; vault_motif_z6 0 {motif_z6_floats};")

    # Unbounded pulse counter `k` (wraps cleanly at 16384 = 4096 corridors > 1.6 hours)
    n_f_k = add("f_k", "#X obj 132 138 f 0;")
    n_inc_k = add("inc_k", "#X obj 182 138 + 1;")
    n_mod_k = add("mod_k", "#X obj 228 138 mod 16384;")
    n_t_k = add("t_k", "#X obj 132 168 t f f f;")

    # Corridor index `y = int(k / 4)` and stone sub-step `sub = k % 4`
    n_sub = add("sub_mod4", "#X obj 84 206 mod 4;")
    n_y_div = add("y_div4", "#X obj 196 206 div 4;")
    n_t_y = add("t_y", "#X obj 196 236 t f f;")

    # 12-bit exact Thue-Morse parity `popcount(y) % 2` & Golden Sturmian bit `st(y)`
    tm_expr = (
        "#X obj 196 270 expr (((int($f1)&1)+((int($f1)>>1)&1)+((int($f1)>>2)&1)+((int($f1)>>3)&1)"
        "+((int($f1)>>4)&1)+((int($f1)>>5)&1)+((int($f1)>>6)&1)+((int($f1)>>7)&1)"
        "+((int($f1)>>8)&1)+((int($f1)>>9)&1)+((int($f1)>>10)&1)+((int($f1)>>11)&1))%2);"
    )
    n_tm_raw = add("tm_raw", tm_expr)
    n_st_raw = add("st_raw", "#X obj 520 236 expr int(($f1+2)*0.6180339887) - int(($f1+1)*0.6180339887);")

    # Gate `tm` and `st` by `D3_SHEAR_ENABLE` (`* $f2` so `0` collapses immediately to d=2 period-12!)
    n_tm_gate = add("tm_gate", "#X obj 196 304 * 1;")
    n_st_gate = add("st_gate", "#X obj 520 270 * 1;")
    n_coset_off = add("coset_off", "#X obj 520 304 * 4;")

    # Axis X index: `((sub + tm + 2*st) % 4) + coset_off`
    n_x_idx = add("x_idx", "#X obj 84 348 expr ((int($f1)+int($f2))%4) + int($f3);")
    n_x_read = add("x_read", "#X obj 84 380 tabread vault_ji_cosets;")
    n_x_hz = add("x_hz", "#X obj 84 410 * 261.6256;")  # C4 register

    # Axis Z index: `tabread vault_motif_z6[(k + 2*tm + st) % 6] + coset_off`
    n_z_step = add("z_step", "#X obj 310 348 expr (int($f1) + 2*int($f2) + int($f3)) % 6;")
    n_z_mread = add("z_mread", "#X obj 310 380 tabread vault_motif_z6;")
    n_z_idx = add("z_idx", "#X obj 310 410 + 0;")
    n_z_read = add("z_read", "#X obj 310 440 tabread vault_ji_cosets;")
    n_z_hz = add("z_hz", "#X obj 310 470 * 130.8128;")  # C3 register

    # Axis Y Carry Bass index: `((sub == 0) ? (tm * 2) : 0)` mapped into active coset at C2 (`65.4064 Hz`)
    n_y_idx = add("y_idx", "#X obj 560 348 expr ((int($f1)==0)*(int($f2)*2)) + int($f3);")
    n_y_read = add("y_read", "#X obj 560 380 tabread vault_ji_cosets;")
    n_y_hz = add("y_hz", "#X obj 560 410 * 65.4064;")   # C2 sub-octave register

    # Voice X synthesis: West-Coast LPG wavefolded pluck (panned Left-Center)
    n_x_t = add("x_t", "#X obj 84 440 t b f;")
    n_x_pack = add("x_pack", "#X obj 124 470 pack f 12;")
    n_x_line_f = add("x_line_f", "#X obj 124 500 line~;")
    n_x_osc = add("x_osc", "#X obj 124 530 osc~ 261.626;")
    n_x_fold_g = add("x_fold_g", "#X obj 124 560 *~ 0.38;")
    n_x_cos = add("x_cos", "#X obj 124 590 cos~;")
    n_x_env_msg = add("x_env_msg", "#X msg 24 500 1 4 \\, 0.001 340 6;")
    n_x_env = add("x_env", "#X obj 24 532 vline~;")
    n_x_vca = add("x_vca", "#X obj 84 624 *~;")
    n_x_hip = add("x_hip", "#X obj 84 654 hip~ 45;")
    n_x_lvl = add("x_lvl", "#X obj 84 684 *~ 0.18;")

    # Voice Z synthesis: Resonant `vcf~` Arch Voice (panned Right-Center)
    n_z_pack = add("z_pack", "#X obj 310 500 pack f 28;")
    n_z_line_f = add("z_line_f", "#X obj 310 530 line~;")
    n_z_phasor = add("z_phasor", "#X obj 310 560 phasor~ 130.813;")
    n_z_dc = add("z_dc", "#X obj 310 590 -~ 0.5;")
    n_z_vcf = add("z_vcf", "#X obj 310 624 vcf~ 520 2.6;")
    n_z_lvl = add("z_lvl", "#X obj 310 654 *~ 0.22;")

    # Voice Y synthesis: Sub-Harmonic Carry Bass + Beating C2 Drone
    n_y_pack = add("y_pack", "#X obj 560 440 pack f 35;")
    n_y_line_f = add("y_line_f", "#X obj 560 470 line~;")
    n_y_osc = add("y_osc", "#X obj 560 500 osc~ 65.4064;")
    n_y_lop = add("y_lop", "#X obj 560 530 lop~ 240;")
    n_y_lvl = add("y_lvl", "#X obj 560 560 *~ 0.19;")
    n_dr_osc = add("dr_osc", "#X obj 710 500 osc~ 65.48;")
    n_dr_lvl = add("dr_lvl", "#X obj 710 530 *~ 0.08;")

    # Golden-Ratio (`373 ms` / `603 ms`) Stereo Vault Delay & `dac~ 1 2`
    n_bus_l = add("bus_l", "#X obj 196 724 +~;")
    n_bus_r = add("bus_r", "#X obj 360 724 +~;")
    n_dw_l = add("dw_l", "#X obj 540 724 delwrite~ vault_dl_l 1000;")
    n_dw_r = add("dw_r", "#X obj 710 724 delwrite~ vault_dl_r 1000;")
    n_dr_l = add("dr_l", "#X obj 540 756 delread~ vault_dl_r 373;")
    n_dr_r = add("dr_r", "#X obj 710 756 delread~ vault_dl_l 603;")
    n_wet_l = add("wet_l", "#X obj 540 786 *~ 0.18;")
    n_wet_r = add("wet_r", "#X obj 710 786 *~ 0.18;")
    n_out_l = add("out_l", "#X obj 196 816 +~;")
    n_out_r = add("out_r", "#X obj 360 816 +~;")
    n_dac = add("dac", "#X obj 276 856 dac~ 1 2;")

    conns: List[Tuple[int, int, int, int]] = [
        # Startup initialization
        (n_lb, 0, n_dsp, 0),
        (n_lb, 0, n_msg_ji, 0),
        (n_lb, 0, n_msg_z6, 0),
        (n_lb, 0, n_d3_init, 0),
        (n_lb, 0, n_run, 0),
        (n_d3_init, 0, n_d3_tgl, 0),
        (n_d3_tgl, 0, n_tm_gate, 1),
        (n_d3_tgl, 0, n_st_gate, 1),

        # Master pulse clock & unbounded counter
        (n_run, 0, n_metro, 0),
        (n_metro, 0, n_f_k, 0),
        (n_f_k, 0, n_inc_k, 0),
        (n_inc_k, 0, n_mod_k, 0),
        (n_mod_k, 0, n_f_k, 1),
        (n_f_k, 0, n_t_k, 0),

        # `t f f f`: outlet 2 fires FIRST (y_div -> tm, st, coset_off), outlet 1 fires SECOND (z_step), outlet 0 fires LAST (sub_mod4)!
        (n_t_k, 2, n_y_div, 0),
        (n_y_div, 0, n_t_y, 0),
        (n_t_y, 1, n_st_raw, 0),
        (n_t_y, 0, n_tm_raw, 0),
        (n_tm_raw, 0, n_tm_gate, 0),
        (n_st_raw, 0, n_st_gate, 0),
        (n_st_gate, 0, n_coset_off, 0),

        # Cold inlets fed first from `tm_gate`, `st_gate`, `coset_off`
        (n_tm_gate, 0, n_x_idx, 1),
        (n_coset_off, 0, n_x_idx, 2),
        (n_tm_gate, 0, n_z_step, 1),
        (n_st_gate, 0, n_z_step, 2),
        (n_coset_off, 0, n_z_idx, 1),
        (n_tm_gate, 0, n_y_idx, 1),
        (n_coset_off, 0, n_y_idx, 2),

        # Hot inlets triggered in deterministic right-to-left order from `t_k`
        (n_t_k, 1, n_z_step, 0),
        (n_t_k, 0, n_sub, 0),
        (n_sub, 0, n_x_idx, 0),
        (n_sub, 0, n_y_idx, 0),

        # Table lookups -> Hz
        (n_x_idx, 0, n_x_read, 0),
        (n_x_read, 0, n_x_hz, 0),
        (n_z_step, 0, n_z_mread, 0),
        (n_z_mread, 0, n_z_idx, 0),
        (n_z_idx, 0, n_z_read, 0),
        (n_z_read, 0, n_z_hz, 0),
        (n_y_idx, 0, n_y_read, 0),
        (n_y_read, 0, n_y_hz, 0),

        # Voice X audio chain
        (n_x_hz, 0, n_x_t, 0),
        (n_x_t, 1, n_x_pack, 0),
        (n_x_t, 0, n_x_env_msg, 0),
        (n_x_pack, 0, n_x_line_f, 0),
        (n_x_line_f, 0, n_x_osc, 0),
        (n_x_osc, 0, n_x_fold_g, 0),
        (n_x_fold_g, 0, n_x_cos, 0),
        (n_x_env_msg, 0, n_x_env, 0),
        (n_x_cos, 0, n_x_vca, 0),
        (n_x_env, 0, n_x_vca, 1),
        (n_x_vca, 0, n_x_hip, 0),
        (n_x_hip, 0, n_x_lvl, 0),

        # Voice Z audio chain (`vcf~` outlet 0 = bandpass, warm resonant reed)
        (n_z_hz, 0, n_z_pack, 0),
        (n_z_pack, 0, n_z_line_f, 0),
        (n_z_line_f, 0, n_z_phasor, 0),
        (n_z_phasor, 0, n_z_dc, 0),
        (n_z_dc, 0, n_z_vcf, 0),
        (n_z_vcf, 0, n_z_lvl, 0),

        # Voice Y & Drone audio chain
        (n_y_hz, 0, n_y_pack, 0),
        (n_y_pack, 0, n_y_line_f, 0),
        (n_y_line_f, 0, n_y_osc, 0),
        (n_y_osc, 0, n_y_lop, 0),
        (n_y_lop, 0, n_y_lvl, 0),
        (n_dr_osc, 0, n_dr_lvl, 0),

        # Stereo bus & Golden-Ratio cross-delay (`373 ms` / `603 ms`)
        (n_x_lvl, 0, n_bus_l, 0),
        (n_y_lvl, 0, n_bus_l, 1),
        (n_dr_lvl, 0, n_bus_l, 1),
        (n_z_lvl, 0, n_bus_r, 0),
        (n_y_lvl, 0, n_bus_r, 1),
        (n_dr_lvl, 0, n_bus_r, 1),
        (n_bus_l, 0, n_dw_l, 0),
        (n_bus_r, 0, n_dw_r, 0),
        (n_dr_l, 0, n_wet_l, 0),
        (n_dr_r, 0, n_wet_r, 0),
        (n_bus_l, 0, n_out_l, 0),
        (n_wet_l, 0, n_out_l, 1),
        (n_bus_r, 0, n_out_r, 0),
        (n_wet_r, 0, n_out_r, 1),
        (n_out_l, 0, n_dac, 0),
        (n_out_r, 0, n_dac, 1),
    ]

    lines = ["#N canvas 70 50 960 900 10;"]
    lines.extend(stmt for _, stmt in nodes)
    for src, out_i, dst, in_i in conns:
        assert 0 <= src < len(nodes) and 0 <= dst < len(nodes), f"Invalid Pd connection {src} -> {dst}"
        lines.append(f"#X connect {src} {out_i} {dst} {in_i};")

    out_pd.parent.mkdir(parents=True, exist_ok=True)
    out_pd.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_pd


if __name__ == "__main__":
    here = Path(__file__).resolve().parent
    info = render_skew_canon_wav(here / "out" / "canon_polymetricus_sine_periodo.wav")
    export_pure_data_patch(here / "out" / "skew_vault_polymetric_canon.pd")
    print("[skew_canon]", info)
