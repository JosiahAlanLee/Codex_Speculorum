"""
common/illustrations/shader_plates.py
=====================================
Clean-room vector & 96-dpi vellum ports of Argon's mathematical demo-video
shader cores upgraded with formal invariants from `openai/math`:

1. 4D Hopf Fibration (`S^3 -> R^3` stereographic projection, 42 chiral 3T
   fibers + rubricated Villarceau link pair with Gauss linking number |Lk| = 1),
   ported from `solver_4d_floquet_hydrapy.py`.
2. Conformal Möbius Chamber & 4D Hyper-Vault (exact isothermal Apollonian
   coaxial circles + orthogonal hyperbolic flux arcs + two-generator loxodromic
   limit orbits + 16-vertex, 32-edge 7/16 octatonic 4D stereographic vault),
   ported from `build_classic_electro_10min_hydrapy.py` (`o2` + `verts_4d`).
3. Strict Hot-Spots Neumann Eigenmode & Koopman-Chladni Medallions (exact
   isotropic finite-volume Neumann Laplacian solver on a smooth bounded simply
   connected planar vault verifying `openai/math` Family 369: nonvanishing
   interior gradient |grad u_1| > 0 and boundary-only extrema, paired with
   Argon's Chladni standing-wave medallions from `nrro_cleanroom_av_engine.py`).
"""

import math
from typing import Dict, List, Sequence, Tuple

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import eigsh

Point = Tuple[float, float]


# ---------------------------------------------------------------------------
# Shared Plotter Geometry Helpers (Clipping, Marching-Squares & Stitching)
# ---------------------------------------------------------------------------

def _clip_polyline_circle(pts: Sequence[Point], cx: float, cy: float, r_max: float) -> List[List[Point]]:
    """Clips a polyline cleanly against a circle of radius `r_max` centered at `(cx, cy)`."""
    r2 = r_max * r_max
    chains: List[List[Point]] = []
    cur: List[Point] = []

    def inside(p: Point) -> bool:
        return (p[0] - cx) ** 2 + (p[1] - cy) ** 2 <= r2 + 1e-9

    def intersect(p0: Point, p1: Point) -> Point:
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        fx, fy = p0[0] - cx, p0[1] - cy
        a = dx * dx + dy * dy
        b = 2.0 * (fx * dx + fy * dy)
        c = fx * fx + fy * fy - r2
        disc = max(0.0, b * b - 4.0 * a * c)
        sq = math.sqrt(disc)
        for sign in (-1.0, 1.0):
            t = (-b + sign * sq) / (2.0 * a + 1e-15)
            if -1e-6 <= t <= 1.0 + 1e-6:
                tc = min(1.0, max(0.0, t))
                return (p0[0] + tc * dx, p0[1] + tc * dy)
        return p0

    for i, p in enumerate(pts):
        ins = inside(p)
        if i == 0:
            if ins:
                cur.append(p)
            continue
        prev = pts[i - 1]
        prev_ins = inside(prev)
        if prev_ins and ins:
            cur.append(p)
        elif prev_ins and not ins:
            cur.append(intersect(prev, p))
            if len(cur) >= 2:
                chains.append(cur)
            cur = []
        elif not prev_ins and ins:
            cur = [intersect(prev, p), p]
    if len(cur) >= 2:
        chains.append(cur)
    return chains


def _smooth_open_or_closed(chain: List[Point], passes: int = 1) -> List[Point]:
    if len(chain) < 4 or passes <= 0:
        return chain
    closed = math.hypot(chain[0][0] - chain[-1][0], chain[0][1] - chain[-1][1]) < 1e-2
    pts = list(chain[:-1]) if closed else list(chain)
    for _ in range(passes):
        if closed:
            n = len(pts)
            pts = [
                (
                    0.25 * pts[(i - 1) % n][0] + 0.50 * pts[i][0] + 0.25 * pts[(i + 1) % n][0],
                    0.25 * pts[(i - 1) % n][1] + 0.50 * pts[i][1] + 0.25 * pts[(i + 1) % n][1],
                )
                for i in range(n)
            ]
        else:
            nxt = [pts[0]]
            for i in range(1, len(pts) - 1):
                nxt.append((
                    0.25 * pts[i - 1][0] + 0.50 * pts[i][0] + 0.25 * pts[i + 1][0],
                    0.25 * pts[i - 1][1] + 0.50 * pts[i][1] + 0.25 * pts[i + 1][1],
                ))
            nxt.append(pts[-1])
            pts = nxt
    if closed:
        pts.append(pts[0])
    return pts


def _marching_squares_stitched(
    field: np.ndarray,
    xs: np.ndarray,
    ys: np.ndarray,
    valid_cell_mask: np.ndarray,
    level: float,
    tol: float = 1e-3,
    smooth_passes: int = 1,
) -> List[List[Point]]:
    """
    Extracts iso-contour segments at `field == level` over `valid_cell_mask`
    (shape `(ny-1, nx-1)`) and stitches them into continuous pen-plotter chains.
    """
    ny, nx = field.shape
    segs: List[Tuple[Point, Point]] = []

    def interp(v0: float, v1: float, p0: Point, p1: Point) -> Point:
        dv = v1 - v0
        t = 0.5 if abs(dv) < 1e-12 else min(1.0, max(0.0, (level - v0) / dv))
        return (p0[0] + t * (p1[0] - p0[0]), p0[1] + t * (p1[1] - p0[1]))

    for j in range(ny - 1):
        y0, y1 = float(ys[j]), float(ys[j + 1])
        for i in range(nx - 1):
            if not valid_cell_mask[j, i]:
                continue
            x0, x1 = float(xs[i]), float(xs[i + 1])
            v00 = float(field[j, i])
            v10 = float(field[j, i + 1])
            v11 = float(field[j + 1, i + 1])
            v01 = float(field[j + 1, i])

            code = (
                (1 if v00 >= level else 0)
                | (2 if v10 >= level else 0)
                | (4 if v11 >= level else 0)
                | (8 if v01 >= level else 0)
            )
            if code in (0, 15):
                continue

            e_top = interp(v00, v10, (x0, y0), (x1, y0))
            e_right = interp(v10, v11, (x1, y0), (x1, y1))
            e_bot = interp(v01, v11, (x0, y1), (x1, y1))
            e_left = interp(v00, v01, (x0, y0), (x0, y1))

            if code in (1, 14):
                segs.append((e_left, e_top))
            elif code in (2, 13):
                segs.append((e_top, e_right))
            elif code in (3, 12):
                segs.append((e_left, e_right))
            elif code in (4, 11):
                segs.append((e_right, e_bot))
            elif code == 5:
                vc = 0.25 * (v00 + v10 + v11 + v01)
                if vc >= level:
                    segs.append((e_left, e_bot))
                    segs.append((e_top, e_right))
                else:
                    segs.append((e_left, e_top))
                    segs.append((e_bot, e_right))
            elif code in (6, 9):
                segs.append((e_top, e_bot))
            elif code in (7, 8):
                segs.append((e_left, e_bot))
            elif code == 10:
                vc = 0.25 * (v00 + v10 + v11 + v01)
                if vc >= level:
                    segs.append((e_left, e_top))
                    segs.append((e_bot, e_right))
                else:
                    segs.append((e_left, e_bot))
                    segs.append((e_top, e_right))

    if not segs:
        return []

    def qkey(p: Point) -> Tuple[int, int]:
        return (int(round(p[0] / tol)), int(round(p[1] / tol)))

    adj: Dict[Tuple[int, int], List[int]] = {}
    pts_by_seg: List[Tuple[Point, Point]] = []
    for a, b in segs:
        if math.hypot(b[0] - a[0], b[1] - a[1]) < 1e-6:
            continue
        sid = len(pts_by_seg)
        pts_by_seg.append((a, b))
        ka, kb = qkey(a), qkey(b)
        adj.setdefault(ka, []).append(sid)
        adj.setdefault(kb, []).append(sid)

    used = [False] * len(pts_by_seg)
    chains: List[List[Point]] = []
    for start_id in range(len(pts_by_seg)):
        if used[start_id]:
            continue
        used[start_id] = True
        a, b = pts_by_seg[start_id]
        chain = [a, b]

        while True:
            kb = qkey(chain[-1])
            nxt_id = next((cand for cand in adj.get(kb, ()) if not used[cand]), None)
            if nxt_id is None:
                break
            used[nxt_id] = True
            p0, p1 = pts_by_seg[nxt_id]
            chain.append(p1 if qkey(p0) == kb else p0)

        while True:
            ka = qkey(chain[0])
            prv_id = next((cand for cand in adj.get(ka, ()) if not used[cand]), None)
            if prv_id is None:
                break
            used[prv_id] = True
            p0, p1 = pts_by_seg[prv_id]
            chain.insert(0, p0 if qkey(p1) == ka else p1)

        if len(chain) >= 3:
            chains.append(_smooth_open_or_closed(chain, passes=smooth_passes))
        elif len(chain) == 2 and math.hypot(chain[1][0] - chain[0][0], chain[1][1] - chain[0][1]) >= 0.4:
            chains.append(chain)

    return chains


# ---------------------------------------------------------------------------
# 1. 4D Hopf Fibration (`S^3 -> R^3` Stereographic Inversion & Villarceau Link)
# ---------------------------------------------------------------------------

def hopf_fiber_s3(theta: float, phi: float, steps: int = 180) -> np.ndarray:
    """Returns `(steps+1, 4)` unit vectors on S^3 for base point `(theta, phi) in S^2`."""
    xi = np.linspace(0.0, 2.0 * math.pi, steps + 1, dtype=np.float64)
    ct, st = math.cos(0.5 * theta), math.sin(0.5 * theta)
    q0 = ct * np.cos(xi + 0.5 * phi)
    q1 = ct * np.sin(xi + 0.5 * phi)
    q2 = st * np.cos(xi - 0.5 * phi)
    q3 = st * np.sin(xi - 0.5 * phi)
    return np.stack([q0, q1, q2, q3], axis=-1)


def hopf_project_r3(q4: np.ndarray, alpha_4d: float = 0.62, pole_pull: float = 0.68) -> np.ndarray:
    """
    Applies Argon's 4D `(q2, q3)` phase rotation and stereographic projection
    from `solver_4d_floquet_hydrapy.py` (`pole_pull` controls outer stereographic sweep).
    """
    cw, sw = math.cos(alpha_4d), math.sin(alpha_4d)
    z4 = q4[:, 2] * cw - q4[:, 3] * sw
    w4 = q4[:, 2] * sw + q4[:, 3] * cw
    sc = 0.94 / (1.42 - pole_pull * w4)
    return np.stack([q4[:, 0] * sc, q4[:, 1] * sc * 0.88, z4 * sc], axis=-1)


def gauss_linking_number(curve_a: np.ndarray, curve_b: np.ndarray) -> float:
    """
    Computes the discrete Gauss linking integral Lk(A, B) for two closed R^3 curves.
    """
    ra = 0.5 * (curve_a[:-1] + curve_a[1:])
    da = curve_a[1:] - curve_a[:-1]
    rb = 0.5 * (curve_b[:-1] + curve_b[1:])
    db = curve_b[1:] - curve_b[:-1]

    diff = ra[:, None, :] - rb[None, :, :]
    dist3 = (np.linalg.norm(diff, axis=-1) ** 3) + 1e-12
    cross = np.cross(da[:, None, :], db[None, :, :])
    num = np.sum(cross * diff, axis=-1)
    return float(np.sum(num / dist3) / (4.0 * math.pi))


def _project_r3_to_plate(pts3: np.ndarray, cx: float = 85.0, cy: float = 101.0, scale_mm: float = 52.0) -> List[Point]:
    yaw, pitch = 0.52, 0.54
    cyaw, syaw = math.cos(yaw), math.sin(yaw)
    cpit, spit = math.cos(pitch), math.sin(pitch)

    x1 = pts3[:, 0] * cyaw - pts3[:, 1] * syaw
    y1 = pts3[:, 0] * syaw + pts3[:, 1] * cyaw
    z1 = pts3[:, 2]

    y2 = y1 * cpit - z1 * spit
    z2 = y1 * spit + z1 * cpit

    persp = 3.1 / (3.1 - 0.38 * z2)
    px = cx + x1 * persp * scale_mm
    py = cy - y2 * persp * scale_mm
    return list(zip(px.tolist(), py.tolist()))


def hopf_fibration_geometry(cx: float = 85.0, cy: float = 101.0, r_horizon: float = 56.5) -> Dict:
    """
    Builds Tabula II's 42 ink Hopf fibers across 3 nested S^2 latitude shells
    (filling the armillary stereographic compass cleanly), 2 rubricated antipodal
    Villarceau linked circles, and a 3T stereographic horizon ring.
    """
    ink_strokes: List[Tuple[List[Point], float]] = []
    red_strokes: List[Tuple[List[Point], float]] = []

    shells = [
        (0.32 * math.pi, 10, 0.11, 0.13),   # Inner core torus (10 fibers)
        (0.52 * math.pi, 16, 0.00, 0.16),   # Clifford Villarceau torus (16 fibers)
        (0.76 * math.pi, 16, 0.19, 0.12),   # Grand stereographic outer lobes (16 fibers -> 42 total)
    ]
    for theta, count, phi0, w_mm in shells:
        for k in range(count):
            phi = phi0 + (2.0 * math.pi * k) / count
            r3 = hopf_project_r3(hopf_fiber_s3(theta, phi, steps=180), alpha_4d=0.62)
            pts2 = _project_r3_to_plate(r3, cx=cx, cy=cy, scale_mm=51.5)
            for ch in _clip_polyline_circle(pts2, cx, cy, r_horizon - 2.6):
                ink_strokes.append((ch, w_mm))

    # Distinguished rubricated Villarceau link pair (antipodal on Clifford equator)
    link_a_r3 = hopf_project_r3(hopf_fiber_s3(0.50 * math.pi, 0.28 * math.pi, steps=200), alpha_4d=0.62)
    link_b_r3 = hopf_project_r3(hopf_fiber_s3(0.50 * math.pi, 1.28 * math.pi, steps=200), alpha_4d=0.62)
    for r3 in (link_a_r3, link_b_r3):
        pts2 = _project_r3_to_plate(r3, cx=cx, cy=cy, scale_mm=51.5)
        for ch in _clip_polyline_circle(pts2, cx, cy, r_horizon - 2.4):
            red_strokes.append((ch, 0.34))

    # Outer & inner stereographic horizon compass rings + 24 rational degree ticks + 3T Ektaal seals
    for r_ring, w_mm in ((r_horizon, 0.22), (r_horizon - 2.2, 0.13)):
        ring_pts = [
            (cx + r_ring * math.cos(math.tau * i / 180), cy + r_ring * math.sin(math.tau * i / 180))
            for i in range(181)
        ]
        ink_strokes.append((ring_pts, w_mm))

    triad_seals: List[Point] = []
    for k in range(24):
        ang = math.tau * k / 24.0 - 0.5 * math.pi
        is_triad = (k % 8 == 0)
        r0 = r_horizon - (3.4 if is_triad else 2.2)
        r1 = r_horizon
        seg = [(cx + r0 * math.cos(ang), cy + r0 * math.sin(ang)), (cx + r1 * math.cos(ang), cy + r1 * math.sin(ang))]
        if is_triad:
            red_strokes.append((seg, 0.28))
            triad_seals.append((cx + (r_horizon - 1.1) * math.cos(ang), cy + (r_horizon - 1.1) * math.sin(ang)))
        else:
            ink_strokes.append((seg, 0.13))

    return {
        "ink_strokes": ink_strokes,
        "red_strokes": red_strokes,
        "triad_seals": triad_seals,
        "link_r3": (link_a_r3, link_b_r3),
    }


def hopf_vellum_field(nx: np.ndarray, ny: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Returns `(warm_field, cool_field)` in `[0, 1]` over normalized page coordinates
    `nx, ny in [0, 1]` representing stereographic Clifford torus action rings.
    """
    dx = (nx - 0.50) * (504.0 / 240.0)
    dy = (ny - 0.465) * (720.0 / 240.0)
    rr = np.hypot(dx, dy)
    ang = np.arctan2(dy, dx)

    conf = 1.0 / (1.0 + 0.85 * rr * rr) ** 1.5
    villarceau = 0.5 + 0.5 * np.cos(10.0 * rr - 3.0 * ang) * np.exp(-0.55 * (rr - 0.62) ** 2)
    spindle = 0.5 + 0.5 * np.cos(6.0 * (dx * 0.86 + dy * 0.50) + 2.0 * ang)
    envelope = np.exp(-0.75 * rr * rr)

    warm = np.clip(envelope * (0.58 * villarceau + 0.42 * conf), 0.0, 1.0).astype(np.float32)
    cool = np.clip(envelope * (1.0 - villarceau) * spindle, 0.0, 1.0).astype(np.float32)
    return warm, cool


# ---------------------------------------------------------------------------
# 2. Conformal Möbius Chamber & 4D Hyper-Vault (`o2` + `verts_4d` + `6689696`)
# ---------------------------------------------------------------------------

def mobius_bipolar_point(u: float, v: float, c_mm: float = 26.0, rot_rad: float = math.pi / 12.0) -> Point:
    """
    Exact isothermal conformal map `z(w) = c * (1 + w) / (1 - w)` for `w = exp(u + i v)`.
    Constant-`u` and constant-`v` curves intersect analytically at 90 degrees everywhere.
    """
    eu = math.exp(u)
    wr, wi = eu * math.cos(v), eu * math.sin(v)
    denom = (1.0 - wr) ** 2 + wi * wi + 1e-12
    zr = (1.0 - (wr * wr + wi * wi)) / denom
    zi = (2.0 * wi) / denom

    cr, sr = math.cos(rot_rad), math.sin(rot_rad)
    xr = c_mm * (zr * cr - zi * sr)
    yr = c_mm * (zr * sr + zi * cr)
    return (xr, yr)


def hypercube_4d_vault(
    cx: float = 85.0,
    cy: float = 101.0,
    scale_mm: float = 27.5,
    a_xw: float = math.tau * (7.0 / 16.0),
    a_yz: float = 0.44,
    a_zw: float = 0.31,
) -> Dict:
    """
    Ports Argon's 16-vertex, 32-edge 4D Hypercube / Calabi-Yau stereographic vault
    projection on the 7/16 octatonic axis from `build_classic_electro_10min_hydrapy.py`.
    """
    verts_orig = np.array(
        [[x, y, z, w] for x in (-1.0, 1.0) for y in (-1.0, 1.0) for z in (-1.0, 1.0) for w in (-1.0, 1.0)],
        dtype=np.float64,
    )
    edges = [
        (i, j)
        for i in range(16)
        for j in range(i + 1, 16)
        if abs(float(np.sum(np.abs(verts_orig[i] - verts_orig[j]))) - 2.0) < 1e-6
    ]

    v = verts_orig.copy()
    c1, s1 = math.cos(a_xw), math.sin(a_xw)
    c2, s2 = math.cos(a_yz), math.sin(a_yz)
    c3, s3 = math.cos(a_zw), math.sin(a_zw)

    v[:, 0], v[:, 3] = v[:, 0] * c1 - v[:, 3] * s1, v[:, 0] * s1 + v[:, 3] * c1
    v[:, 1], v[:, 2] = v[:, 1] * c2 - v[:, 2] * s2, v[:, 1] * s2 + v[:, 2] * c2
    v[:, 2], v[:, 3] = v[:, 2] * c3 - v[:, 3] * s3, v[:, 2] * s3 + v[:, 3] * c3

    persp4 = 1.0 / (2.55 - 0.65 * v[:, 3])
    persp3 = 1.0 / (2.75 - 0.75 * v[:, 2] * persp4)
    px = cx + v[:, 0] * persp4 * persp3 * (scale_mm * 5.2)
    py = cy - v[:, 1] * persp4 * persp3 * (scale_mm * 5.2)
    pts2 = list(zip(px.tolist(), py.tolist()))

    inner_edges = [(i, j) for (i, j) in edges if verts_orig[i, 3] > 0 and verts_orig[j, 3] > 0]
    outer_and_strut_edges = [(i, j) for (i, j) in edges if not (verts_orig[i, 3] > 0 and verts_orig[j, 3] > 0)]
    return {
        "verts_orig": verts_orig,
        "verts_2d": pts2,
        "edges": edges,
        "inner_edges": inner_edges,
        "outer_edges": outer_and_strut_edges,
    }


def mobius_conformal_geometry(cx: float = 85.0, cy: float = 101.0, r_ap: float = 55.5) -> Dict:
    """
    Constructs Tabula III: isothermal Apollonian circles + orthogonal hyperbolic arcs,
    two-generator Möbius orbit circles, and Argon's central 7/16 4D Hyper-Vault.
    """
    ink_strokes: List[Tuple[List[Point], float]] = []
    red_strokes: List[Tuple[List[Point], float]] = []

    u_levels = (-2.05, -1.50, -1.08, -0.76, -0.50, -0.28, 0.28, 0.50, 0.76, 1.08, 1.50, 2.05)
    v_samples = np.linspace(0.0, math.tau, 200)
    for u in u_levels:
        raw = [(cx + p[0], cy - p[1]) for p in (mobius_bipolar_point(u, float(vv)) for vv in v_samples)]
        for ch in _clip_polyline_circle(raw, cx, cy, r_ap - 1.8):
            ink_strokes.append((ch, 0.14))

    u_samples = np.linspace(-3.4, 3.4, 180)
    for k in range(1, 24):
        if k == 12:
            continue
        v = math.tau * k / 24.0
        if abs(math.sin(v)) < 0.14:
            continue
        raw = [(cx + p[0], cy - p[1]) for p in (mobius_bipolar_point(float(uu), v) for uu in u_samples)]
        for ch in _clip_polyline_circle(raw, cx, cy, r_ap - 1.8):
            ink_strokes.append((ch, 0.12))

    def mob_gen1(z: complex) -> complex:
        return (1.22 * z + 0.46) / (0.46 * z + 1.22)

    def mob_gen2(z: complex) -> complex:
        phase = complex(math.cos(math.pi * 7.0 / 8.0), math.sin(math.pi * 7.0 / 8.0))
        return phase * mob_gen1(z / phase)

    ang_t = np.linspace(0.0, math.tau, 96)
    seed_circle = [0.22j + 0.11 * complex(math.cos(t), math.sin(t)) for t in ang_t]
    seed_conj = [-0.22j + 0.11 * complex(math.cos(t), math.sin(t)) for t in ang_t]
    rot_c = complex(math.cos(math.pi / 12.0), math.sin(math.pi / 12.0))

    frontier = [seed_circle, seed_conj]
    for depth in range(1, 4):
        nxt_frontier = []
        for loop_z in frontier:
            for gen_fn in (mob_gen1, mob_gen2):
                mapped = [gen_fn(z) for z in loop_z]
                nxt_frontier.append(mapped)
                pts = [(cx + 42.0 * (z * rot_c).real, cy - 42.0 * (z * rot_c).imag) for z in mapped]
                for ch in _clip_polyline_circle(pts, cx, cy, r_ap - 2.0):
                    red_strokes.append((ch, 0.18 if depth < 3 else 0.14))
        frontier = nxt_frontier[:6]

    rot_rad = math.pi / 12.0
    foci = [
        (cx + 26.0 * math.cos(rot_rad), cy - 26.0 * math.sin(rot_rad)),
        (cx - 26.0 * math.cos(rot_rad), cy + 26.0 * math.sin(rot_rad)),
    ]

    vault = hypercube_4d_vault(cx=cx, cy=cy, scale_mm=27.5)
    for i, j in vault["outer_edges"]:
        ink_strokes.append(([vault["verts_2d"][i], vault["verts_2d"][j]], 0.21))
    for i, j in vault["inner_edges"]:
        red_strokes.append(([vault["verts_2d"][i], vault["verts_2d"][j]], 0.26))

    for r_ring, w_mm, is_red in ((r_ap, 0.24, False), (r_ap - 1.8, 0.14, True)):
        pts = [
            (cx + r_ring * math.cos(math.tau * i / 180), cy + r_ring * math.sin(math.tau * i / 180))
            for i in range(181)
        ]
        (red_strokes if is_red else ink_strokes).append((pts, w_mm))

    bx0, by0, bx1, by1 = cx - 61.0, cy - 63.0, cx + 61.0, cy + 63.0
    ink_strokes.append(([(bx0, by0), (bx1, by0), (bx1, by1), (bx0, by1), (bx0, by0)], 0.18))
    for corner_x, corner_y, a0, a1 in (
        (bx0, by0, 0.0, 0.5 * math.pi),
        (bx1, by0, 0.5 * math.pi, math.pi),
        (bx1, by1, math.pi, 1.5 * math.pi),
        (bx0, by1, 1.5 * math.pi, math.tau),
    ):
        arc = [
            (corner_x + 12.0 * math.cos(a0 + (a1 - a0) * k / 24), corner_y + 12.0 * math.sin(a0 + (a1 - a0) * k / 24))
            for k in range(25)
        ]
        red_strokes.append((arc, 0.16))

    return {
        "ink_strokes": ink_strokes,
        "red_strokes": red_strokes,
        "foci": foci,
        "vault": vault,
    }


def mobius_vellum_field(nx: np.ndarray, ny: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Evaluates Argon's `o2` conformal Möbius lattice wash + Apollonian dipole gradient.
    """
    xx = (nx - 0.50) * 2.1
    yy = (ny - 0.465) * 2.8
    denom = (xx - 0.34) ** 2 + (yy + 0.12) ** 2 + 0.22
    mob_u = (xx * xx + yy * yy - 0.28) / denom
    mob_v = (0.72 * yy) / denom

    ribs_u = np.exp(-6.5 * np.abs(np.sin(2.4 * mob_u)))
    ribs_v = np.exp(-6.5 * np.abs(np.sin(2.4 * mob_v)))
    env = np.exp(-0.62 * (xx * xx + 0.75 * yy * yy))

    warm = np.clip(env * (0.62 * ribs_u + 0.38 * (0.5 + 0.5 * np.tanh(mob_u))), 0.0, 1.0).astype(np.float32)
    cool = np.clip(env * (0.65 * ribs_v + 0.35 * (0.5 - 0.5 * np.tanh(mob_v))), 0.0, 1.0).astype(np.float32)
    return warm, cool


# ---------------------------------------------------------------------------
# 3. Strict Hot-Spots Neumann Eigenmode (`openai/math` Family 369) & Chladni
# ---------------------------------------------------------------------------

def _vault_phi(x_mm: np.ndarray, y_mm: np.ndarray, cx: float = 85.0, cy: float = 101.0) -> np.ndarray:
    """
    Smooth, bounded, simply connected upward-crowned apsidal vault domain `Phi(x, y) <= 1`:
    narrower crown at top (`Y < 0`, `y < cy`), broader base below (`Y > 0`, `y > cy`).
    """
    X = (x_mm - cx) / 38.0
    Y = (y_mm - cy) / 53.0
    taper = 1.0 + 0.22 * Y
    return (X / taper) ** 2 + Y ** 2


def solve_strict_hotspots_neumann(cx: float = 85.0, cy: float = 101.0, h_mm: float = 1.0) -> Dict:
    """
    Solves the isotropic 5-point finite-volume Neumann Laplacian `-Delta u = lambda_1 u`
    on the smooth simply connected vault domain `Phi(x, y) <= 1` and verifies
    `openai/math` Family 369 (`StrictHotSpots.lean`).
    """
    xs = np.arange(cx - 46.0, cx + 46.0 + 0.5 * h_mm, h_mm, dtype=np.float64)
    ys = np.arange(cy - 56.0, cy + 56.0 + 0.5 * h_mm, h_mm, dtype=np.float64)
    XX, YY = np.meshgrid(xs, ys, indexing="xy")
    phi = _vault_phi(XX, YY, cx=cx, cy=cy)
    inside = phi <= 1.0

    ny, nx = inside.shape
    node_id = np.full((ny, nx), -1, dtype=np.int32)
    pts_ij = np.argwhere(inside)
    n_nodes = len(pts_ij)
    for k, (j, i) in enumerate(pts_ij):
        node_id[j, i] = k

    rows: List[int] = []
    cols: List[int] = []
    vals: List[float] = []
    diag = np.zeros(n_nodes, dtype=np.float64)
    is_boundary = np.zeros(n_nodes, dtype=bool)

    for k, (j, i) in enumerate(pts_ij):
        deg = 0
        for dj, di in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nj, ni = j + dj, i + di
            if 0 <= nj < ny and 0 <= ni < nx and node_id[nj, ni] >= 0:
                nk = int(node_id[nj, ni])
                rows.append(k)
                cols.append(nk)
                vals.append(-1.0)
                deg += 1
        diag[k] = float(deg)
        if deg < 4:
            is_boundary[k] = True

    rows.extend(range(n_nodes))
    cols.extend(range(n_nodes))
    vals.extend(diag.tolist())
    L = sparse.csr_matrix((vals, (rows, cols)), shape=(n_nodes, n_nodes))

    v0 = np.array([cy - ys[j] for (j, _) in pts_ij], dtype=np.float64)
    evals, evecs = eigsh(L, k=3, sigma=-1e-5, which="LM", v0=v0)
    order = np.argsort(evals)
    evals = evals[order]
    evecs = evecs[:, order]

    u1_vec = evecs[:, 1].copy()
    top_k = int(np.argmin([ys[j] for (j, _) in pts_ij]))
    if u1_vec[top_k] < 0:
        u1_vec = -u1_vec
    u1_vec /= float(np.max(np.abs(u1_vec)))

    max_k = int(np.argmax(u1_vec))
    min_k = int(np.argmin(u1_vec))

    field = np.full((ny, nx), np.nan, dtype=np.float64)
    for k, (j, i) in enumerate(pts_ij):
        field[j, i] = u1_vec[k]

    grad_mag_interior: List[float] = []
    gx_grid = np.zeros((ny, nx), dtype=np.float64)
    gy_grid = np.zeros((ny, nx), dtype=np.float64)
    for k, (j, i) in enumerate(pts_ij):
        im = i - 1 if (i > 0 and inside[j, i - 1]) else i
        ip = i + 1 if (i + 1 < nx and inside[j, i + 1]) else i
        jm = j - 1 if (j > 0 and inside[j - 1, i]) else j
        jp = j + 1 if (j + 1 < ny and inside[j + 1, i]) else j
        gx = (field[j, ip] - field[j, im]) / max(h_mm, (ip - im) * h_mm)
        gy = (field[jp, i] - field[jm, i]) / max(h_mm, (jp - jm) * h_mm)
        gx_grid[j, i] = gx
        gy_grid[j, i] = gy
        if not is_boundary[k]:
            grad_mag_interior.append(math.hypot(gx, gy))

    j_max, i_max = pts_ij[max_k]
    j_min, i_min = pts_ij[min_k]

    return {
        "xs": xs,
        "ys": ys,
        "phi": phi,
        "inside": inside,
        "field": field,
        "gx": gx_grid,
        "gy": gy_grid,
        "lambda_1": float(evals[1]) / (h_mm * h_mm),
        "mean_u1": float(np.mean(u1_vec)),
        "max_on_boundary": bool(is_boundary[max_k]),
        "min_on_boundary": bool(is_boundary[min_k]),
        "min_interior_grad": float(min(grad_mag_interior)),
        "hot_pole": (float(xs[i_max]), float(ys[j_max])),
        "cold_pole": (float(xs[i_min]), float(ys[j_min])),
    }


def _trace_streamline(
    seed: Point,
    sign: float,
    xs: np.ndarray,
    ys: np.ndarray,
    gx: np.ndarray,
    gy: np.ndarray,
    cx: float,
    cy: float,
    step_mm: float = 0.65,
    max_steps: int = 160,
) -> List[Point]:
    x0, y0 = float(xs[0]), float(ys[0])
    hx = float(xs[1] - xs[0])
    hy = float(ys[1] - ys[0])
    ny, nx = gx.shape

    def sample_dir(px: float, py: float) -> Tuple[float, float]:
        fi = (px - x0) / hx
        fj = (py - y0) / hy
        i0 = int(math.floor(fi))
        j0 = int(math.floor(fj))
        if i0 < 0 or i0 + 1 >= nx or j0 < 0 or j0 + 1 >= ny:
            return (0.0, 0.0)
        tx, ty = fi - i0, fj - j0
        vx = (
            (1 - tx) * (1 - ty) * gx[j0, i0]
            + tx * (1 - ty) * gx[j0, i0 + 1]
            + (1 - tx) * ty * gx[j0 + 1, i0]
            + tx * ty * gx[j0 + 1, i0 + 1]
        )
        vy = (
            (1 - tx) * (1 - ty) * gy[j0, i0]
            + tx * (1 - ty) * gy[j0, i0 + 1]
            + (1 - tx) * ty * gy[j0 + 1, i0]
            + tx * ty * gy[j0 + 1, i0 + 1]
        )
        nrm = math.hypot(vx, vy)
        if nrm < 1e-8:
            return (0.0, 0.0)
        return (sign * vx / nrm, sign * vy / nrm)

    pts = [seed]
    px, py = seed
    for _ in range(max_steps):
        d1x, d1y = sample_dir(px, py)
        if d1x == 0.0 and d1y == 0.0:
            break
        mx, my = px + 0.5 * step_mm * d1x, py + 0.5 * step_mm * d1y
        d2x, d2y = sample_dir(mx, my)
        if d2x == 0.0 and d2y == 0.0:
            break
        nx_p, ny_p = px + step_mm * d2x, py + step_mm * d2y
        if float(_vault_phi(np.array(nx_p), np.array(ny_p), cx=cx, cy=cy)) > 0.985:
            pts.append((nx_p, ny_p))
            break
        pts.append((nx_p, ny_p))
        px, py = nx_p, ny_p
    return pts


def chladni_medallion_strokes(cx: float, cy: float, r_mm: float, n_m: int, m_m: int) -> Tuple[List[List[Point]], List[List[Point]], List[Point]]:
    """
    Computes exact stitched nodal curves of Argon's Chladni basis inside a circular
    medallion, separating central core nodal axes (`red_nodals`) from outer rings.
    """
    g = 56
    us = np.linspace(-1.0, 1.0, g)
    vs = np.linspace(-1.0, 1.0, g)
    UU, VV = np.meshgrid(us, vs, indexing="xy")
    field = np.cos(n_m * math.pi * UU) * np.cos(m_m * math.pi * VV) - np.cos(m_m * math.pi * UU) * np.cos(n_m * math.pi * VV)
    xs = cx + us * r_mm
    ys = cy + vs * r_mm
    valid = np.ones((g - 1, g - 1), dtype=bool)
    raw_chains = _marching_squares_stitched(field, xs, ys, valid, level=0.0, tol=1e-3, smooth_passes=1)

    red_nodals: List[List[Point]] = []
    ink_nodals: List[List[Point]] = []
    for ch in raw_chains:
        for cl in _clip_polyline_circle(ch, cx, cy, r_mm - 0.8):
            min_d = min(math.hypot(p[0] - cx, p[1] - cy) for p in cl)
            if min_d < 1.5:
                red_nodals.append(cl)
            else:
                ink_nodals.append(cl)

    ring = [(cx + r_mm * math.cos(math.tau * i / 96), cy + r_mm * math.sin(math.tau * i / 96)) for i in range(97)]
    return ink_nodals, red_nodals, ring


def hotspots_neumann_geometry(cx: float = 85.0, cy: float = 101.0) -> Dict:
    """
    Constructs Tabula IV: Strict Hot-Spots Neumann eigenfunction iso-contours,
    rubricated nodal zero-curve, non-singular interior gradient streamlines,
    rubricated boundary extrema seals, and 4 Koopman-Chladni spandrel medallions.
    """
    sol = solve_strict_hotspots_neumann(cx=cx, cy=cy, h_mm=1.0)
    xs, ys, inside, field = sol["xs"], sol["ys"], sol["inside"], sol["field"]
    valid_cells = inside[:-1, :-1] & inside[:-1, 1:] & inside[1:, 1:] & inside[1:, :-1]
    safe_field = np.where(inside, field, 0.0)

    ink_strokes: List[Tuple[List[Point], float]] = []
    red_strokes: List[Tuple[List[Point], float]] = []

    all_cells = np.ones((len(ys) - 1, len(xs) - 1), dtype=bool)
    for b_ch in _marching_squares_stitched(sol["phi"], xs, ys, all_cells, level=1.0, tol=1e-3, smooth_passes=2):
        ink_strokes.append((b_ch, 0.25))
    for b_in in _marching_squares_stitched(sol["phi"], xs, ys, all_cells, level=1.055, tol=1e-3, smooth_passes=2):
        ink_strokes.append((b_in, 0.12))

    levels = (-0.88, -0.74, -0.60, -0.46, -0.32, -0.18, -0.08, 0.08, 0.18, 0.32, 0.46, 0.60, 0.74, 0.88)
    for lv in levels:
        for ch in _marching_squares_stitched(safe_field, xs, ys, valid_cells, level=lv, tol=1e-3, smooth_passes=1):
            ink_strokes.append((ch, 0.14))

    nodal_chains = _marching_squares_stitched(safe_field, xs, ys, valid_cells, level=0.0, tol=1e-3, smooth_passes=1)
    for n_ch in nodal_chains:
        red_strokes.append((n_ch, 0.32))

    if nodal_chains:
        main_nodal = max(nodal_chains, key=len)
        idxs = np.linspace(2, len(main_nodal) - 3, 13, dtype=int)
        for idx in idxs:
            seed = main_nodal[int(idx)]
            up_pts = _trace_streamline(seed, +1.0, xs, ys, sol["gx"], sol["gy"], cx=cx, cy=cy)
            dn_pts = _trace_streamline(seed, -1.0, xs, ys, sol["gx"], sol["gy"], cx=cx, cy=cy)
            full_line = list(reversed(dn_pts[1:])) + up_pts
            if len(full_line) >= 4:
                ink_strokes.append((_smooth_open_or_closed(full_line, passes=1), 0.12))

    medallions = [
        (34.0, 48.0, 2, 3, "16:15"),
        (136.0, 48.0, 3, 4, "5:4"),
        (34.0, 154.0, 3, 5, "3:2"),
        (136.0, 154.0, 4, 5, "15:8"),
    ]
    medallion_labels: List[Tuple[float, float, str]] = []
    for mx, my, nm, mm_mode, ratio_lbl in medallions:
        ink_nods, red_nods, ring = chladni_medallion_strokes(mx, my, r_mm=12.5, n_m=nm, m_m=mm_mode)
        ink_strokes.append((ring, 0.18))
        for ch in ink_nods:
            ink_strokes.append((ch, 0.13))
        for ch in red_nods:
            red_strokes.append((ch, 0.19))
        medallion_labels.append((mx, my + 16.0, ratio_lbl))

    return {
        "solver": sol,
        "ink_strokes": ink_strokes,
        "red_strokes": red_strokes,
        "hot_pole": sol["hot_pole"],
        "cold_pole": sol["cold_pole"],
        "medallion_labels": medallion_labels,
    }


def hotspots_vellum_field(nx: np.ndarray, ny: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Evaluates the smooth Neumann thermal dipole wash (`warm` toward the upper apse
    crown hot-spot, `cool` toward the lower base cold-spot) + Chladni nodal watermark.
    """
    xx = (nx - 0.50) * 2.0
    yy = (ny - 0.465) * 2.4
    taper = np.clip(1.0 + 0.22 * yy, 0.55, 1.45)
    phi_approx = (xx / (0.62 * taper)) ** 2 + (yy / 0.86) ** 2
    env = np.exp(-0.78 * phi_approx)

    chladni = np.cos(3.0 * math.pi * xx) * np.cos(4.0 * math.pi * yy) - np.cos(4.0 * math.pi * xx) * np.cos(3.0 * math.pi * yy)
    nodal_ribs = np.exp(-4.2 * np.abs(chladni))
    vault_rim = np.exp(-12.0 * np.abs(phi_approx - 0.92))
    dipole = -np.tanh(1.75 * yy)

    warm = np.clip(env * (0.52 * np.maximum(0.0, dipole) + 0.34 * nodal_ribs + 0.28 * vault_rim), 0.0, 1.0).astype(np.float32)
    cool = np.clip(env * (0.56 * np.maximum(0.0, -dipole) + 0.30 * (1.0 - nodal_ribs) + 0.20 * vault_rim), 0.0, 1.0).astype(np.float32)
    return warm, cool


# ---------------------------------------------------------------------------
# 4. Koopman / Raag Bhairav Crab Canon (`Tabula V · Canon Cancrizans`)
# ---------------------------------------------------------------------------

def canon_koopman_geometry(score_rows: Sequence[Dict], cx: float = 85.0) -> Dict:
    """
    Constructs Tabula V (`Canon Cancrizans Koopmanianus`):
      - Upper & lower 8-line Just Intonation ratio staves (`32` steps across `8` bars)
        plotting `Vox Recta` (ink) and `Vox Cancrizans` (rubricated diamonds)
        crossing symmetrically around the central `t = 15.5` mirror axis.
      - Lower octagonal Koopman-Bhairav Mirror Wheel (`r · r' = 2:1` involution chords
        + 8 miniature Chladni/Koopman nodal medallions).
    """
    ink_strokes: List[Tuple[List[Point], float]] = []
    red_strokes: List[Tuple[List[Point], float]] = []
    recta_notes: List[Point] = []
    cancri_diamonds: List[List[Point]] = []
    labels: List[Tuple[float, float, str, bool, float]] = []

    # 1. 8-Swara Ratio Stave (`x in [24, 149]`, `y in [40, 82]`, top = S', bottom = Sa)
    sx0, sx1 = 26.0, 148.0
    sy_top, sy_bot = 40.0, 82.0
    swara_names = ["Sa", "r", "G", "m", "P", "d", "N", "S'"]
    for deg in range(8):
        ly = sy_bot - deg * ((sy_bot - sy_top) / 7.0)
        is_axis = deg in (0, 7)
        ink_strokes.append(([(sx0, ly), (sx1, ly)], 0.18 if is_axis else 0.10))
        labels.append((21.2, ly + 0.8, swara_names[deg], deg in (1, 5), 2.0))

    # Barlines (8 bars = 9 barlines) + rubricated central mirror fold axis at Bar 4|5
    for b in range(9):
        bx = sx0 + b * ((sx1 - sx0) / 8.0)
        if b == 4:
            red_strokes.append(([(bx, sy_top - 3.5), (bx, sy_bot + 3.5)], 0.30))
            labels.append((bx, sy_top - 5.0, "AXIS 2:1", True, 2.0))
        else:
            ink_strokes.append(([(bx, sy_top), (bx, sy_bot)], 0.14 if b in (0, 8) else 0.10))

    # Plot 32-step melodic contours & mensural noteheads
    n_steps = len(score_rows)
    step_dx = (sx1 - sx0) / float(n_steps)
    recta_poly: List[Point] = []
    cancri_poly: List[Point] = []
    for row in score_rows:
        k = int(row["step"])
        nx_p = sx0 + (k + 0.5) * step_dx
        ry = sy_bot - int(row["recta_deg"]) * ((sy_bot - sy_top) / 7.0)
        cy_n = sy_bot - int(row["cancri_deg"]) * ((sy_bot - sy_top) / 7.0)
        recta_poly.append((nx_p, ry))
        cancri_poly.append((nx_p, cy_n))
        recta_notes.append((nx_p, ry))
        d = 1.05
        cancri_diamonds.append([(nx_p, cy_n - d), (nx_p + d, cy_n), (nx_p, cy_n + d), (nx_p - d, cy_n), (nx_p, cy_n - d)])

    ink_strokes.append((recta_poly, 0.20))
    red_strokes.append((cancri_poly, 0.18))
    for dm in cancri_diamonds:
        red_strokes.append((dm, 0.20))

    # 2. Lower Octagonal Koopman-Bhairav Involution Wheel (`(85, 127)`, `R = 28.0 mm`)
    wcx, wcy, wr = cx, 127.0, 28.0
    r_lbl_in, r_lbl_out = wr - 10.5, wr - 3.2
    ink_strokes.append(([(wcx + wr * math.cos(math.tau * i / 144), wcy + wr * math.sin(math.tau * i / 144)) for i in range(145)], 0.20))
    ink_strokes.append(([(wcx + r_lbl_in * math.cos(math.tau * i / 144), wcy + r_lbl_in * math.sin(math.tau * i / 144)) for i in range(145)], 0.10))

    base_angles = [-0.82 * math.pi, -0.58 * math.pi, -0.34 * math.pi, -0.10 * math.pi]
    deg_angles = {
        0: base_angles[0], 7: base_angles[0] + math.pi,
        1: base_angles[1], 6: base_angles[1] + math.pi,
        2: base_angles[2], 5: base_angles[2] + math.pi,
        3: base_angles[3], 4: base_angles[3] + math.pi,
    }
    ratio_strs = ["1:1", "16:15", "5:4", "4:3", "3:2", "8:5", "15:8", "2:1"]
    koopman_modes = [(1, 2), (1, 3), (2, 3), (3, 4), (3, 5), (4, 5), (2, 5), (2, 3)]

    wheel_nodes: Dict[int, Point] = {}
    for d in range(8):
        ang = deg_angles[d]
        px = wcx + wr * math.cos(ang)
        py = wcy + wr * math.sin(ang)
        wheel_nodes[d] = (px, py)

        mx = wcx + (wr + 8.6) * math.cos(ang)
        my = wcy + (wr + 8.6) * math.sin(ang)
        nm, mm_m = koopman_modes[d]
        in_c, rd_c, m_ring = chladni_medallion_strokes(mx, my, r_mm=5.0, n_m=nm, m_m=mm_m)
        ink_strokes.append((m_ring, 0.14))
        for ch in in_c:
            ink_strokes.append((ch, 0.10))
        for ch in rd_c:
            red_strokes.append((ch, 0.13))

        # Place ratio label cleanly inside the open label annulus `[r_lbl_in .. r_lbl_out]`
        r_mid_lbl = 0.5 * (r_lbl_in + r_lbl_out)
        lx = wcx + r_mid_lbl * math.cos(ang)
        ly = wcy + r_mid_lbl * math.sin(ang) + 0.75
        labels.append((lx, ly, ratio_strs[d], d in (1, 5), 1.85))
        # Short outer index tick from `r_lbl_out` to `wr`
        red_strokes.append(([(wcx + r_lbl_out * math.cos(ang), wcy + r_lbl_out * math.sin(ang)), (px, py)], 0.22))

    # Draw the 4 rubricated octave-inversion diameters inside `r_lbl_in` so labels stay 100% unobstructed!
    for d in range(4):
        a0, a1 = deg_angles[d], deg_angles[7 - d]
        p_in0 = (wcx + (r_lbl_in - 0.6) * math.cos(a0), wcy + (r_lbl_in - 0.6) * math.sin(a0))
        p_in1 = (wcx + (r_lbl_in - 0.6) * math.cos(a1), wcy + (r_lbl_in - 0.6) * math.sin(a1))
        red_strokes.append(([p_in0, p_in1], 0.22))
    # Connect sequential scale polygon in ink
    poly_order = [0, 1, 2, 3, 7, 6, 5, 4, 0]
    ink_strokes.append(([wheel_nodes[idx] for idx in poly_order], 0.13))

    return {
        "ink_strokes": ink_strokes,
        "red_strokes": red_strokes,
        "recta_notes": recta_notes,
        "wheel_center": (wcx, wcy),
        "labels": labels,
    }


def canon_vellum_field(nx: np.ndarray, ny: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    96-dpi standing-wave vellum wash for Tabula V: palindromic horizontal wave
    interference above + 8-spoke Koopman harmonic rosette below.
    """
    xx = (nx - 0.50) * 2.1
    yy = (ny - 0.58) * 2.4
    rr = np.hypot(xx, yy)
    ang = np.arctan2(yy, xx)

    stave_band = np.exp(-((ny - 0.28) / 0.11) ** 2) * (0.5 + 0.5 * np.cos(16.0 * math.pi * nx))
    wheel_band = np.exp(-0.95 * rr * rr) * (0.5 + 0.5 * np.cos(8.0 * ang) * np.cos(7.0 * rr))

    warm = np.clip(0.55 * stave_band + 0.65 * wheel_band, 0.0, 1.0).astype(np.float32)
    cool = np.clip(0.45 * np.exp(-0.85 * rr * rr) * (1.0 - 0.5 * np.cos(4.0 * ang)), 0.0, 1.0).astype(np.float32)
    return warm, cool


# ---------------------------------------------------------------------------
# 5. Hidden-Line-Eliminated 3D Aperiodic Cutaway Vault (`Tabula VI`)
#    (`openai/math` Family 155: `PeriodicTilingThree.lean`, `d = 3` minimal)
# ---------------------------------------------------------------------------

def _thue_morse(n: int) -> int:
    return bin(abs(int(n))).count("1") & 1


def _sturmian_golden(n: int) -> int:
    phi = (1.0 + math.sqrt(5.0)) * 0.5
    return int(math.floor((n + 2) / phi) - math.floor((n + 1) / phi))


def build_3d_skew_vault_voxels(nx: int = 8, ny: int = 8, nz: int = 6) -> Dict:
    """
    Constructs an exact, zero-overlap translational 3D tiling of stepped 4-cube
    Z-voussoir monotiles `T_Z = {(0,0,0), (1,0,0), (1,0,1), (2,0,1)}` sheared across
    `y`-galleries by `(Thue-Morse(y), Sturmian(y))`, then carves an Escherian
    stepped courtyard cutaway into the front-top octant so interior courses show.
    """
    t_offsets = [(0, 0, 0), (1, 0, 0), (1, 0, 1), (2, 0, 1)]
    voxel_owner: Dict[Tuple[int, int, int], int] = {}
    stone_voxels: Dict[int, List[Tuple[int, int, int]]] = {}
    rubric_stones: set = set()

    sid = 0
    for y in range(ny):
        sx = _thue_morse(y)
        sz = _sturmian_golden(y)
        for k in range(-2, nz // 2 + 3):
            for m in range(-3, nx // 2 + 4):
                ax = 2 * m + k + sx
                ay = y
                az = 2 * k + sz
                cells = [(ax + dx, ay + dy, az + dz) for (dx, dy, dz) in t_offsets]

                # Keep only whole 4-voxel monotiles inside the cutaway architectural volume
                valid = True
                for cx_v, cy_v, cz_v in cells:
                    if not (0 <= cx_v < nx and 0 <= cy_v < ny and 0 <= cz_v < nz):
                        valid = False
                        break
                    # Carve stepped Escherian amphitheater cutaway in front-upper corner `(cx >= 4, cy >= 4, cz >= 2)`
                    if cx_v >= 4 and cy_v >= 4 and cz_v >= 2:
                        valid = False
                        break
                    if cx_v >= 6 and cy_v >= 2 and cz_v >= 4:
                        valid = False
                        break
                    if cy_v >= 6 and cx_v >= 2 and cz_v >= 4:
                        valid = False
                        break
                if not valid:
                    continue

                sid += 1
                stone_voxels[sid] = cells
                for cell in cells:
                    if cell in voxel_owner:
                        raise AssertionError(f"Translational overlap at voxel {cell}!")
                    voxel_owner[cell] = sid

                # Highlight the stepped skew-shear witness courses in rubric red (#a32b24)
                if (cz_v_min := min(c[2] for c in cells)) in (2, 3) and (ay in (1, 3, 5)) and (2 <= min(c[0] for c in cells) <= 5):
                    rubric_stones.add(sid)

    return {
        "voxel_owner": voxel_owner,
        "stone_voxels": stone_voxels,
        "rubric_stones": rubric_stones,
        "y_shears": [(_thue_morse(y), _sturmian_golden(y)) for y in range(ny)],
    }


def aperiodic_vault_geometry(cx: float = 85.0, cy: float = 109.0, unit_mm: float = 5.4) -> Dict:
    """
    Renders `Tabula VI` (`Fornix Sine Periodo`):
      - Exact isometric triangle-lattice Z-buffer hidden-line elimination, fusing
        coplanar voxel faces of each 4-cube Z-stone into solid carved masonry blocks.
      - Fine Escher woodcut hatching on `+Y` shadow faces.
      - Upper spandrel medallions contrasting `d = 2` periodic lattice lock vs.
        `d = 3` non-periodic skew-shear strata (`openai/math` Family 155).
    """
    vault = build_3d_skew_vault_voxels(nx=8, ny=8, nz=6)
    voxel_owner = vault["voxel_owner"]
    rubric_stones = vault["rubric_stones"]

    # Exact integer isometric lattice:
    # A vertex `(vx, vy, vz)` maps to integer lattice coords `U = vx - vy`, `V = vx + vy - 2*vz`
    # Physical plate mm: `X_mm = cx + U * (sqrt(3)/2 * unit_mm)`, `Y_mm = cy + V * (0.5 * unit_mm)`
    sx_u = (math.sqrt(3.0) * 0.5) * unit_mm
    sy_v = 0.5 * unit_mm

    def lat_to_mm(u_i: int, v_i: int) -> Point:
        return (cx + u_i * sx_u, cy + v_i * sy_v)

    # Z-buffer over elementary isometric screen triangles keyed by `(u1+u2+u3, v1+v2+v3)`
    # Value: `(depth, stone_id, face_id, tri_verts_lat)` where `face_id`: 0 = +Z (top), 1 = +X (right), 2 = +Y (left-shadow)
    tri_buf: Dict[Tuple[int, int], Tuple[int, int, int, Tuple[Tuple[int, int], Tuple[int, int], Tuple[int, int]]]] = {}

    for (vx, vy, vz), sid in voxel_owner.items():
        depth = vx + vy + vz
        u0 = (vx + 1) - (vy + 1)
        v0 = (vx + 1) + (vy + 1) - 2 * (vz + 1)

        p_c = (u0, v0)
        p_top = (u0, v0 - 2)
        p_ur = (u0 + 1, v0 - 1)
        p_lr = (u0 + 1, v0 + 1)
        p_bot = (u0, v0 + 2)
        p_ll = (u0 - 1, v0 + 1)
        p_ul = (u0 - 1, v0 - 1)

        six_tris = [
            (0, (p_c, p_ul, p_top)),
            (0, (p_c, p_top, p_ur)),
            (1, (p_c, p_ur, p_lr)),
            (1, (p_c, p_lr, p_bot)),
            (2, (p_c, p_bot, p_ll)),
            (2, (p_c, p_ll, p_ul)),
        ]
        for face_id, tv in six_tris:
            tkey = (tv[0][0] + tv[1][0] + tv[2][0], tv[0][1] + tv[1][1] + tv[2][1])
            prev = tri_buf.get(tkey)
            if prev is None or depth > prev[0]:
                tri_buf[tkey] = (depth, sid, face_id, tv)

    # Collect undirected lattice edges -> adjacent visible triangle states
    edge_adj: Dict[Tuple[Tuple[int, int], Tuple[int, int]], List[Tuple[int, int]]] = {}
    shadow_quads_mm: List[List[Point]] = []

    for _, sid, face_id, (a, b, c_v) in tri_buf.values():
        for p1, p2 in ((a, b), (b, c_v), (c_v, a)):
            ek = (p1, p2) if p1 <= p2 else (p2, p1)
            edge_adj.setdefault(ek, []).append((sid, face_id))

    mortar_segs_ink: List[Tuple[Point, Point]] = []
    mortar_segs_red: List[Tuple[Point, Point]] = []
    crease_segs_ink: List[Tuple[Point, Point]] = []
    crease_segs_red: List[Tuple[Point, Point]] = []

    for (p1, p2), states in edge_adj.items():
        m1, m2 = lat_to_mm(*p1), lat_to_mm(*p2)
        if len(states) == 1:
            # Silhouette boundary against background or courtyard cutaway
            sid0, _ = states[0]
            (mortar_segs_red if sid0 in rubric_stones else mortar_segs_ink).append((m1, m2))
        elif len(states) == 2:
            (s1, f1), (s2, f2) = states
            if s1 != s2:
                # True mortar joint between two distinct translated monotiles!
                is_red = (s1 in rubric_stones) or (s2 in rubric_stones)
                (mortar_segs_red if is_red else mortar_segs_ink).append((m1, m2))
            elif f1 != f2:
                # Internal 90-degree crease within the same 4-cube Z-stone
                is_red = s1 in rubric_stones
                (crease_segs_red if is_red else crease_segs_ink).append((m1, m2))

    # Add crisp Escher woodcut parallel shading strokes inside visible `+Y` (left-facing) triangles
    hatch_strokes: List[List[Point]] = []
    for _, sid, face_id, (a, b, c_v) in tri_buf.values():
        if face_id != 2:
            continue
        pa, pb, pc = lat_to_mm(*a), lat_to_mm(*b), lat_to_mm(*c_v)
        for t_frac in (0.28, 0.54, 0.78):
            # Interpolate parallel to edge `(b -> c_v)` toward vertex `a`
            q1 = (pa[0] + t_frac * (pb[0] - pa[0]), pa[1] + t_frac * (pb[1] - pa[1]))
            q2 = (pa[0] + t_frac * (pc[0] - pa[0]), pa[1] + t_frac * (pc[1] - pa[1]))
            if math.hypot(q2[0] - q1[0], q2[1] - q1[1]) > 0.6:
                hatch_strokes.append([q1, q2])

    def stitch_raw_segs(segs: Sequence[Tuple[Point, Point]]) -> List[List[Point]]:
        if not segs:
            return []
        tol = 1e-3
        def qk(p: Point) -> Tuple[int, int]:
            return (int(round(p[0] / tol)), int(round(p[1] / tol)))
        adj: Dict[Tuple[int, int], List[int]] = {}
        clean = list(segs)
        for i, (u_p, v_p) in enumerate(clean):
            adj.setdefault(qk(u_p), []).append(i)
            adj.setdefault(qk(v_p), []).append(i)
        used = [False] * len(clean)
        out: List[List[Point]] = []
        for i in range(len(clean)):
            if used[i]:
                continue
            used[i] = True
            ch = [clean[i][0], clean[i][1]]
            while True:
                k_end = qk(ch[-1])
                nxt = next((j for j in adj.get(k_end, ()) if not used[j]), None)
                if nxt is None:
                    break
                used[nxt] = True
                a_p, b_p = clean[nxt]
                ch.append(b_p if qk(a_p) == k_end else a_p)
            while True:
                k_beg = qk(ch[0])
                prv = next((j for j in adj.get(k_beg, ()) if not used[j]), None)
                if prv is None:
                    break
                used[prv] = True
                a_p, b_p = clean[prv]
                ch.insert(0, a_p if qk(b_p) == k_beg else b_p)
            out.append(ch)
        return out

    ink_strokes: List[Tuple[List[Point], float]] = []
    red_strokes: List[Tuple[List[Point], float]] = []

    for ch in hatch_strokes:
        ink_strokes.append((ch, 0.08))
    for ch in stitch_raw_segs(crease_segs_ink):
        ink_strokes.append((ch, 0.13))
    for ch in stitch_raw_segs(mortar_segs_ink):
        ink_strokes.append((ch, 0.22))
    for ch in stitch_raw_segs(crease_segs_red):
        red_strokes.append((ch, 0.16))
    for ch in stitch_raw_segs(mortar_segs_red):
        red_strokes.append((ch, 0.30))

    # Upper Spandrel Medallions contrasting d=2 Bhattacharya Lattice vs d=3 Family 155 Non-Periodicity
    # Left Medallion `(36, 48, r=12.5)`: Periodic Z^2 lattice grid with closed fundamental torus vectors
    lcx, lcy, mr = 35.0, 48.0, 12.0
    ink_strokes.append(([(lcx + mr * math.cos(math.tau * i / 96), lcy + mr * math.sin(math.tau * i / 96)) for i in range(97)], 0.18))
    for g_off in (-7.5, -2.5, 2.5, 7.5):
        span = math.sqrt(max(0.0, (mr - 1.2) ** 2 - g_off * g_off))
        ink_strokes.append(([(lcx - span, lcy + g_off), (lcx + span, lcy + g_off)], 0.11))
        ink_strokes.append(([(lcx + g_off, lcy - span), (lcx + g_off, lcy + span)], 0.11))
    red_strokes.append(([(lcx - 2.5, lcy - 2.5), (lcx + 2.5, lcy - 2.5), (lcx + 2.5, lcy + 2.5), (lcx - 2.5, lcy + 2.5), (lcx - 2.5, lcy - 2.5)], 0.24))

    # Right Medallion `(135, 48, r=12.0)`: Sheared non-periodic d=3 coset strata (Thue-Morse + Sturmian offsets)
    rcx, rcy = 135.0, 48.0
    ink_strokes.append(([(rcx + mr * math.cos(math.tau * i / 96), rcy + mr * math.sin(math.tau * i / 96)) for i in range(97)], 0.18))
    for idx_r, y_off in enumerate((-8.0, -4.8, -1.6, 1.6, 4.8, 8.0)):
        span = math.sqrt(max(0.0, (mr - 1.2) ** 2 - y_off * y_off))
        ink_strokes.append(([(rcx - span, rcy + y_off), (rcx + span, rcy + y_off)], 0.11))
        sh = 1.9 * _thue_morse(idx_r) + 1.3 * _sturmian_golden(idx_r)
        for bx in np.arange(-10.0 + sh, 10.5, 4.4):
            if bx * bx + (y_off + 1.6) ** 2 < (mr - 1.4) ** 2 and y_off < 7.5:
                seg = [(rcx + bx, rcy + y_off), (rcx + bx, rcy + min(8.0, y_off + 3.2))]
                (red_strokes if idx_r in (2, 4) else ink_strokes).append((seg, 0.16 if idx_r in (2, 4) else 0.11))

    # Isolated specimen diagram of the single unrotated 4-cube Z-stone at bottom-right `(136, 154)`
    scx, scy, su = 134.0, 153.0, 3.4
    spec_tris: Dict[Tuple[int, int], Tuple[int, int, Tuple]] = {}
    for (vx, vy, vz) in [(0, 0, 0), (1, 0, 0), (1, 0, 1), (2, 0, 1)]:
        d_s = vx + vy + vz
        u0, v0 = (vx + 1) - (vy + 1), (vx + 1) + (vy + 1) - 2 * (vz + 1)
        pc, pt, pur, plr, pb_v, pll, pul = (u0, v0), (u0, v0 - 2), (u0 + 1, v0 - 1), (u0 + 1, v0 + 1), (u0, v0 + 2), (u0 - 1, v0 + 1), (u0 - 1, v0 - 1)
        for fid, tv in ((0, (pc, pul, pt)), (0, (pc, pt, pur)), (1, (pc, pur, plr)), (1, (pc, plr, pb_v)), (2, (pc, pb_v, pll)), (2, (pc, pll, pul))):
            tk = (tv[0][0] + tv[1][0] + tv[2][0], tv[0][1] + tv[1][1] + tv[2][1])
            if tk not in spec_tris or d_s > spec_tris[tk][0]:
                spec_tris[tk] = (d_s, fid, tv)
    spec_edges: Dict[Tuple, List[int]] = {}
    for _, fid, (a, b, c_v) in spec_tris.values():
        for p1, p2 in ((a, b), (b, c_v), (c_v, a)):
            ek = (p1, p2) if p1 <= p2 else (p2, p1)
            spec_edges.setdefault(ek, []).append(fid)
    for (p1, p2), fids in spec_edges.items():
        if len(fids) == 1 or fids[0] != fids[1]:
            m1 = (scx + (p1[0] - 1.0) * sx_u * (su / unit_mm), scy + p1[1] * sy_v * (su / unit_mm))
            m2 = (scx + (p2[0] - 1.0) * sx_u * (su / unit_mm), scy + p2[1] * sy_v * (su / unit_mm))
            red_strokes.append(([m1, m2], 0.24 if len(fids) == 1 else 0.15))

    labels = [
        (lcx, lcy + 15.8, "D=2 PERIODIC", False, 1.95),
        (rcx, rcy + 15.8, "D=3 APERIODIC", True, 1.95),
        (scx + 1.0, scy + 11.5, "LAPIS UNICUS T", True, 1.95),
    ]

    return {
        "vault": vault,
        "ink_strokes": ink_strokes,
        "red_strokes": red_strokes,
        "labels": labels,
        "visible_triangles": len(tri_buf),
    }


def aperiodic_vellum_field(nx: np.ndarray, ny: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    96-dpi vellum wash for Tabula VI: 3-axis isometric quasi-periodic interference
    sheared by golden-ratio phase so background grain never locks to a 2D period.
    """
    phi = (1.0 + math.sqrt(5.0)) * 0.5
    xx = (nx - 0.50) * 2.2
    yy = (ny - 0.48) * 2.6
    env = np.exp(-0.68 * (xx * xx + 0.80 * yy * yy))

    u1 = xx * 0.866 + yy * 0.5
    u2 = -xx * 0.866 + yy * 0.5
    shear = np.cos(5.0 * math.pi * u1 + 1.4 * np.sin(3.0 * math.pi * phi * yy))
    cross = np.cos(5.0 * math.pi * phi * u2 - 1.2 * np.cos(4.0 * math.pi * xx))

    warm = np.clip(env * (0.5 + 0.5 * shear * cross), 0.0, 1.0).astype(np.float32)
    cool = np.clip(env * (0.5 - 0.5 * shear) * (0.5 + 0.5 * np.cos(6.0 * yy)), 0.0, 1.0).astype(np.float32)
    return warm, cool


# ---------------------------------------------------------------------------
# 6. Book III Acoustic Resonator (`Tabula VII · Cista Resonantiae Chladniana`)
# ---------------------------------------------------------------------------

def viol_resonator_phi(x_mm: np.ndarray, y_mm: np.ndarray, cx: float = 85.0, cy: float = 98.5) -> np.ndarray:
    """
    Smooth (`C^infty`), bounded, simply connected, **non-convex** waisted luthiery
    viol soundboard `Phi_viol(x, y) <= 1`:
      - Pinched inward at the C-bout waist near `Y = -0.06`
      - Broader lower bout (`Y > 0`) than upper bout (`Y < 0`).
    Tests `openai/math` Family 369 (`HotSpots.lean`) beyond convex domains!
    """
    Y = (y_mm - cy) / 43.5
    w = 25.5 * (1.0 + 0.14 * Y - 0.30 * np.exp(-((Y + 0.06) / 0.34) ** 2) + 0.12 * (Y ** 2))
    return ((x_mm - cx) / w) ** 2 + Y ** 2


def solve_viol_acoustic_resonator(cx: float = 85.0, cy: float = 98.5, h_mm: float = 0.90) -> Dict:
    """
    Solves the 5-point finite-volume Neumann Laplacian `-Delta u = mu_k u` (`d_nu u = 0`)
    for the first 6 eigenmodes (`mu_1 = 0 < mu_2 <= ... <= mu_6`) on the non-convex
    waisted viol soundboard `Phi_viol <= 1`, verifying:
      - Orthogonality `mean(u_2) == 0`
      - Nonvanishing interior gradient `min_{Omega^o} |grad u_2| > 0`
      - Boundary-only global extrema (`max` and `min` strictly on `dOmega`)
      - Acoustic overtone frequency ratios `sqrt(mu_k / mu_2)` (`k = 2..7`).
    """
    xs = np.arange(cx - 35.0, cx + 35.5, h_mm, dtype=np.float64)
    ys = np.arange(cy - 46.5, cy + 46.5 + 0.5 * h_mm, h_mm, dtype=np.float64)
    XX, YY = np.meshgrid(xs, ys, indexing="xy")
    phi = viol_resonator_phi(XX, YY, cx=cx, cy=cy)
    inside = phi <= 1.0

    ny, nx = inside.shape
    node_id = np.full((ny, nx), -1, dtype=np.int32)
    pts_ij = np.argwhere(inside)
    n_nodes = len(pts_ij)
    for k, (j, i) in enumerate(pts_ij):
        node_id[j, i] = k

    rows: List[int] = []
    cols: List[int] = []
    vals: List[float] = []
    diag = np.zeros(n_nodes, dtype=np.float64)
    is_boundary = np.zeros(n_nodes, dtype=bool)

    for k, (j, i) in enumerate(pts_ij):
        deg = 0
        for dj, di in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nj, ni = j + dj, i + di
            if 0 <= nj < ny and 0 <= ni < nx and node_id[nj, ni] >= 0:
                rows.append(k)
                cols.append(int(node_id[nj, ni]))
                vals.append(-1.0)
                deg += 1
        diag[k] = float(deg)
        if deg < 4:
            is_boundary[k] = True

    rows.extend(range(n_nodes))
    cols.extend(range(n_nodes))
    vals.extend(diag.tolist())
    L = sparse.csr_matrix((vals, (rows, cols)), shape=(n_nodes, n_nodes))

    v0 = np.array([cy - ys[j] for (j, _) in pts_ij], dtype=np.float64)
    evals, evecs = eigsh(L, k=7, sigma=-1e-5, which="LM", v0=v0)
    order = np.argsort(evals)
    evals = evals[order]
    evecs = evecs[:, order]

    # Mode u_2 (first positive Neumann eigenfunction, index 1)
    u2 = evecs[:, 1].copy()
    top_k = int(np.argmin([ys[j] for (j, _) in pts_ij]))
    if u2[top_k] < 0:
        u2 = -u2
    u2 /= float(np.max(np.abs(u2)))

    max_k = int(np.argmax(u2))
    min_k = int(np.argmin(u2))

    def unpack_mode(col_idx: int) -> np.ndarray:
        vec = evecs[:, col_idx].copy()
        vec /= float(np.max(np.abs(vec)))
        arr = np.full((ny, nx), np.nan, dtype=np.float64)
        for k_i, (j_i, i_i) in enumerate(pts_ij):
            arr[j_i, i_i] = vec[k_i]
        return arr

    field_u2 = np.full((ny, nx), np.nan, dtype=np.float64)
    for k, (j, i) in enumerate(pts_ij):
        field_u2[j, i] = u2[k]

    grad_mag_interior: List[float] = []
    gx_grid = np.zeros((ny, nx), dtype=np.float64)
    gy_grid = np.zeros((ny, nx), dtype=np.float64)
    for k, (j, i) in enumerate(pts_ij):
        im = i - 1 if (i > 0 and inside[j, i - 1]) else i
        ip = i + 1 if (i + 1 < nx and inside[j, i + 1]) else i
        jm = j - 1 if (j > 0 and inside[j - 1, i]) else j
        jp = j + 1 if (j + 1 < ny and inside[j + 1, i]) else j
        gx = (field_u2[j, ip] - field_u2[j, im]) / max(h_mm, (ip - im) * h_mm)
        gy = (field_u2[jp, i] - field_u2[jm, i]) / max(h_mm, (jp - jm) * h_mm)
        gx_grid[j, i] = gx
        gy_grid[j, i] = gy
        if not is_boundary[k]:
            grad_mag_interior.append(math.hypot(gx, gy))

    freq_ratios = [float(math.sqrt(evals[m] / evals[1])) for m in range(1, 7)]
    j_max, i_max = pts_ij[max_k]
    j_min, i_min = pts_ij[min_k]

    return {
        "xs": xs,
        "ys": ys,
        "phi": phi,
        "inside": inside,
        "field_u2": field_u2,
        "field_u4": unpack_mode(3),
        "field_u5": unpack_mode(4),
        "gx": gx_grid,
        "gy": gy_grid,
        "mu_2": float(evals[1]) / (h_mm * h_mm),
        "freq_ratios": freq_ratios,
        "mean_u2": float(np.mean(u2)),
        "max_on_boundary": bool(is_boundary[max_k]),
        "min_on_boundary": bool(is_boundary[min_k]),
        "min_interior_grad": float(min(grad_mag_interior)),
        "hot_pole": (float(xs[i_max]), float(ys[j_max])),
        "cold_pole": (float(xs[i_min]), float(ys[j_min])),
    }


def _trace_viol_streamline(
    seed: Point,
    sign: float,
    xs: np.ndarray,
    ys: np.ndarray,
    gx: np.ndarray,
    gy: np.ndarray,
    cx: float,
    cy: float,
    step_mm: float = 0.60,
    max_steps: int = 165,
) -> List[Point]:
    x0, y0 = float(xs[0]), float(ys[0])
    hx = float(xs[1] - xs[0])
    hy = float(ys[1] - ys[0])
    ny, nx = gx.shape

    def sample_dir(px: float, py: float) -> Tuple[float, float]:
        fi = (px - x0) / hx
        fj = (py - y0) / hy
        i0 = int(math.floor(fi))
        j0 = int(math.floor(fj))
        if i0 < 0 or i0 + 1 >= nx or j0 < 0 or j0 + 1 >= ny:
            return (0.0, 0.0)
        tx, ty = fi - i0, fj - j0
        vx = (
            (1 - tx) * (1 - ty) * gx[j0, i0]
            + tx * (1 - ty) * gx[j0, i0 + 1]
            + (1 - tx) * ty * gx[j0 + 1, i0]
            + tx * ty * gx[j0 + 1, i0 + 1]
        )
        vy = (
            (1 - tx) * (1 - ty) * gy[j0, i0]
            + tx * (1 - ty) * gy[j0, i0 + 1]
            + (1 - tx) * ty * gy[j0 + 1, i0]
            + tx * ty * gy[j0 + 1, i0 + 1]
        )
        nrm = math.hypot(vx, vy)
        if nrm < 1e-8:
            return (0.0, 0.0)
        return (sign * vx / nrm, sign * vy / nrm)

    pts = [seed]
    px, py = seed
    for _ in range(max_steps):
        d1x, d1y = sample_dir(px, py)
        if d1x == 0.0 and d1y == 0.0:
            break
        mx, my = px + 0.5 * step_mm * d1x, py + 0.5 * step_mm * d1y
        d2x, d2y = sample_dir(mx, my)
        if d2x == 0.0 and d2y == 0.0:
            break
        nx_p, ny_p = px + step_mm * d2x, py + step_mm * d2y
        if float(viol_resonator_phi(np.array(nx_p), np.array(ny_p), cx=cx, cy=cy)) > 0.975:
            pts.append((nx_p, ny_p))
            break
        pts.append((nx_p, ny_p))
        px, py = nx_p, ny_p
    return pts


def acoustic_resonator_geometry(cx: float = 85.0, cy: float = 98.5) -> Dict:
    """
    Constructs `Tabula VII · Cista Resonantiae Chladniana`:
      1. Central double-purfled non-convex luthiery viol soundboard (`pi_1 = 0`, zero f-holes)
         engraving smooth pressure iso-bars `u_2 = c`, rubricated Chladni nodal waist curve
         `u_2 = 0` with quartz-sand stipple ticks, 11 non-singular interior gradient streamlines
         `grad u_2 != 0`, upper bowing hot-spot `P_+` + horsehair bow tangent, and cold pole `P_-`.
      2. Four corner spandrel medallions contrasting higher Chladni overtones (`u_4`, `u_5`)
         against the two sharp counterexample regimes: doubly-connected twin-hole plates
         (Burdzy-Werner 1999, `pi_1 != 0`) and 3D starlike chambers (Atar-Burdzy 2026, `r=0` max).
      3. Graduated Helmholtz monochord eigenfrequency ratio bar (`sqrt(mu_k / mu_2)`).
    """
    sol = solve_viol_acoustic_resonator(cx=cx, cy=cy, h_mm=0.90)
    xs, ys, inside, f_u2 = sol["xs"], sol["ys"], sol["inside"], sol["field_u2"]
    valid_cells = inside[:-1, :-1] & inside[:-1, 1:] & inside[1:, 1:] & inside[1:, :-1]
    safe_u2 = np.where(inside, f_u2, 0.0)

    ink_strokes: List[Tuple[List[Point], float]] = []
    red_strokes: List[Tuple[List[Point], float]] = []
    sand_dots: List[Point] = []

    # 1. Double-purfled luthiery viol soundboard rim (`Phi = 1.0` outer, `Phi = 0.925` purfling inlay)
    all_cells = np.ones((len(ys) - 1, len(xs) - 1), dtype=bool)
    for b_out in _marching_squares_stitched(sol["phi"], xs, ys, all_cells, level=1.0, tol=1e-3, smooth_passes=2):
        ink_strokes.append((b_out, 0.28))
    for b_purf in _marching_squares_stitched(sol["phi"], xs, ys, all_cells, level=0.925, tol=1e-3, smooth_passes=2):
        ink_strokes.append((b_purf, 0.12))

    # 2. Smooth non-crossing interior level curves `u_2 = c`
    for lv in (-0.86, -0.72, -0.58, -0.44, -0.30, -0.16, 0.16, 0.30, 0.44, 0.58, 0.72, 0.86):
        for ch in _marching_squares_stitched(safe_u2, xs, ys, valid_cells, level=lv, tol=1e-3, smooth_passes=1):
            ink_strokes.append((ch, 0.13))

    # 3. Rubricated Chladni Nodal Sand-Line `u_2(x, y) = 0` + quartz-sand grain ticks along nodal band
    nodal_chains = _marching_squares_stitched(safe_u2, xs, ys, valid_cells, level=0.0, tol=1e-3, smooth_passes=1)
    for n_ch in nodal_chains:
        red_strokes.append((n_ch, 0.34))
        # Deterministic quartz-sand stipple flecks resting beside the quiet nodal locus
        for idx_p, (px, py) in enumerate(n_ch[2:-2:2]):
            off_a = 1.15 * math.sin(idx_p * 2.39996)
            off_b = 1.65 * math.cos(idx_p * 1.61803)
            for dy_s in (off_a, -off_b):
                sx_g, sy_g = px + 0.45 * math.cos(idx_p), py + dy_s
                if float(viol_resonator_phi(np.array(sx_g), np.array(sy_g), cx=cx, cy=cy)) < 0.89:
                    sand_dots.append((sx_g, sy_g))
                    ink_strokes.append(([(sx_g - 0.22, sy_g), (sx_g + 0.22, sy_g)], 0.14))

    # 4. 11 Non-singular orthogonal acoustic velocity/gradient streamlines `grad u_2`
    if nodal_chains:
        main_nodal = max(nodal_chains, key=len)
        seed_idxs = np.linspace(3, max(4, len(main_nodal) - 4), 11, dtype=int)
        for idx in seed_idxs:
            seed = main_nodal[int(idx)]
            up_pts = _trace_viol_streamline(seed, +1.0, xs, ys, sol["gx"], sol["gy"], cx=cx, cy=cy)
            dn_pts = _trace_viol_streamline(seed, -1.0, xs, ys, sol["gx"], sol["gy"], cx=cx, cy=cy)
            full_line = list(reversed(dn_pts[1:])) + up_pts
            if len(full_line) >= 4:
                ink_strokes.append((_smooth_open_or_closed(full_line, passes=1), 0.11))

    # 5. Boundary Bowing Hot-Spot (`P_+` with Chladni horsehair bow tangent) & Cold Pole (`P_-`)
    hx, hy = sol["hot_pole"]
    lx_p, ly_p = sol["cold_pole"]
    for rr in (1.3, 2.5):
        red_strokes.append(([(hx + rr * math.cos(math.tau * i / 36), hy + rr * math.sin(math.tau * i / 36)) for i in range(37)], 0.22))
        ink_strokes.append(([(lx_p + rr * math.cos(math.tau * i / 36), ly_p + rr * math.sin(math.tau * i / 36)) for i in range(37)], 0.18))
    # Chladni horsehair bow drawn tangentially across the upper boundary antinode `P_+`
    red_strokes.append(([(hx - 14.0, hy - 3.6), (hx + 14.0, hy + 2.2)], 0.26))
    ink_strokes.append(([(hx - 13.6, hy - 4.7), (hx + 14.4, hy + 1.1)], 0.12))

    # Helper to draw a miniature scaled viol contour + nodal set inside a corner medallion
    def add_mini_viol_mode(mcx: float, mcy: float, mr: float, mode_grid: np.ndarray) -> None:
        ink_strokes.append(([(mcx + mr * math.cos(math.tau * i / 84), mcy + mr * math.sin(math.tau * i / 84)) for i in range(85)], 0.18))
        sc_m = 0.195
        for b_c in _marching_squares_stitched(sol["phi"], xs, ys, all_cells, level=1.0, tol=1e-3, smooth_passes=1):
            pts_m = [(mcx + (p[0] - cx) * sc_m, mcy + (p[1] - cy) * sc_m) for p in b_c]
            ink_strokes.append((pts_m, 0.16))
        safe_m = np.where(inside, mode_grid, 0.0)
        for n_c in _marching_squares_stitched(safe_m, xs, ys, valid_cells, level=0.0, tol=1e-3, smooth_passes=1):
            pts_m = [(mcx + (p[0] - cx) * sc_m, mcy + (p[1] - cy) * sc_m) for p in n_c]
            red_strokes.append((pts_m, 0.21))

    # 6. Four Corner Luthiery & Topological Foil Medallions (`r = 10.8 mm`)
    mr = 10.8
    # Upper-Left `(31, 46)`: Higher Viol Chladni Overtone `u_4` (4-quadrant saddle nodal cross)
    add_mini_viol_mode(31.0, 46.0, mr, sol["field_u4"])

    # Lower-Left `(31, 141)`: Higher Viol Chladni Overtone `u_5` (luthiery ring-and-bout mode)
    add_mini_viol_mode(31.0, 141.0, mr, sol["field_u5"])

    # Upper-Right `(139, 46)`: Doubly Connected Two-Hole Foil (Burdzy-Werner 1999, `pi_1 != 0`)
    rcx, rcy = 139.0, 46.0
    ink_strokes.append(([(rcx + mr * math.cos(math.tau * i / 84), rcy + mr * math.sin(math.tau * i / 84)) for i in range(85)], 0.18))
    sc_m = 0.195
    for b_c in _marching_squares_stitched(sol["phi"], xs, ys, all_cells, level=1.0, tol=1e-3, smooth_passes=1):
        ink_strokes.append(([(rcx + (p[0] - cx) * sc_m, rcy + (p[1] - cy) * sc_m) for p in b_c], 0.16))
    # Twin luthiery sound-holes (`pi_1 != 0` obstacles) + trapped interior hot-spot ring!
    for sgn in (-1.0, 1.0):
        hx_f = rcx + sgn * 2.8
        ink_strokes.append(([(hx_f + 1.0 * math.cos(math.tau * i / 32), rcy + 2.6 * math.sin(math.tau * i / 32)) for i in range(33)], 0.16))
    for rr_t, w_t in ((1.1, 0.24), (2.0, 0.14)):
        red_strokes.append(([(rcx + rr_t * math.cos(math.tau * i / 36), rcy + rr_t * math.sin(math.tau * i / 36)) for i in range(37)], w_t))

    # Lower-Right `(139, 141)`: 3D Starlike Spiked Chamber Foil (Atar-Burdzy Oct 2026, `r=0` interior max!)
    scx, scy = 139.0, 141.0
    ink_strokes.append(([(scx + mr * math.cos(math.tau * i / 84), scy + mr * math.sin(math.tau * i / 84)) for i in range(85)], 0.18))
    star_pts: List[Point] = []
    n_spikes = 12
    for i in range(n_spikes * 2 + 1):
        ang = math.tau * i / (n_spikes * 2)
        rad_s = 8.8 if (i % 2 == 0) else 4.3
        star_pts.append((scx + rad_s * math.cos(ang), scy + rad_s * math.sin(ang)))
    ink_strokes.append((star_pts, 0.15))
    for rr_s, is_r in ((1.2, True), (2.4, True), (3.6, False)):
        ring_s = [(scx + rr_s * math.cos(math.tau * i / 36), scy + rr_s * math.sin(math.tau * i / 36)) for i in range(37)]
        (red_strokes if is_r else ink_strokes).append((ring_s, 0.22 if rr_s < 1.5 else 0.13))

    # 7. Helmholtz Monochord Eigenfrequency Spectrum Rail (`y = 163.5 mm`, `x in [32, 138]`)
    bar_x0, bar_x1, bar_y = 32.0, 138.0, 163.5
    ink_strokes.append(([(bar_x0, bar_y), (bar_x1, bar_y)], 0.20))
    ink_strokes.append(([(bar_x0, bar_y - 1.3), (bar_x1, bar_y - 1.3)], 0.10))
    ratios = sol["freq_ratios"]  # [1.000, ~2.000, ~2.065, ~2.468, ~2.847, ~3.263]
    r_min, r_max = 1.0, max(3.4, ratios[-1] + 0.1)
    ratio_ticks: List[Tuple[float, float, str, bool]] = []
    for idx_r, r_val in enumerate(ratios):
        tx = bar_x0 + ((r_val - r_min) / (r_max - r_min)) * (bar_x1 - bar_x0)
        is_oct = idx_r in (0, 1)  # Highlight fundamental 1.00x and natural 2.00x octave lock!
        (red_strokes if is_oct else ink_strokes).append(([(tx, bar_y - 2.6), (tx, bar_y + 2.2)], 0.24 if is_oct else 0.15))
        # Offset closely spaced modes 2 & 3 (`2.00x` vs `2.07x`) slightly in label x/y so text never collides!
        lbl_x = tx - 3.2 if idx_r == 1 else (tx + 3.4 if idx_r == 2 else tx)
        ratio_ticks.append((lbl_x, bar_y + 5.2, f"{r_val:.2f}x", is_oct))

    labels = [
        (31.0, 60.2, "U4 OVER-NODE", False, 1.85),
        (139.0, 60.2, "2 HOLES: TRAP", True, 1.85),
        (31.0, 155.2, "U5 RING-MODE", False, 1.85),
        (139.0, 155.2, "D=3 STAR: R=0", True, 1.85),
        (cx, hy - 5.2, "BOW HOT-SPOT P+", True, 1.85),
        (cx, ly_p + 5.8, "RIM COLD-POLE P-", False, 1.85),
    ]
    for lx, ly, txt, is_r in ratio_ticks:
        labels.append((lx, ly, txt, is_r, 1.65))

    return {
        "solver": sol,
        "ink_strokes": ink_strokes,
        "red_strokes": red_strokes,
        "sand_dots": sand_dots,
        "labels": labels,
    }


def chladni_vellum_field(nx: np.ndarray, ny: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    96-dpi vellum wash for Tabula VII: luthiery spruce-grain Chladni standing-wave
    interference (`(2,3)` + `(3,5)` nodal superpositions) framed by the viol dipole.
    """
    xx = (nx - 0.50) * 2.1
    yy = (ny - 0.46) * 2.5
    env = np.exp(-0.72 * (xx * xx + 0.78 * yy * yy))

    chladni_23 = np.cos(2.0 * math.pi * xx) * np.cos(3.0 * math.pi * yy) - np.cos(3.0 * math.pi * xx) * np.cos(2.0 * math.pi * yy)
    chladni_14 = np.cos(1.0 * math.pi * xx) * np.cos(4.0 * math.pi * yy) + 0.5 * np.cos(3.0 * math.pi * yy)

    warm = np.clip(env * np.clip(-yy * 0.9 + 0.35, 0.0, 1.0) * (0.55 + 0.45 * np.abs(chladni_23)), 0.0, 1.0).astype(np.float32)
    cool = np.clip(env * np.clip(+yy * 0.9 + 0.35, 0.0, 1.0) * (0.50 + 0.50 * np.exp(-3.5 * (chladni_14 ** 2))), 0.0, 1.0).astype(np.float32)
    return warm, cool


# ---------------------------------------------------------------------------
# 7. Book IV Single-Fold Diophantine & Gödel Diagonal (`Tabula VIII`)
# ---------------------------------------------------------------------------

PRIMES_16: Tuple[int, ...] = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53)


def pell_matiyasevich_solutions(a: int, count: int = 7) -> List[Tuple[int, int]]:
    """
    Generates exact integer solutions `(x_n, y_n)` to Matiyasevich's Pell equation
    `x^2 - (a^2 - 1) * y^2 = 1` for `a >= 2` via the linear recurrence:
      x_0 = 1, y_0 = 0;  x_1 = a, y_1 = 1;  x_{n+1} = 2*a*x_n - x_{n-1}.
    Every solution provides exponential growth inside polynomial Diophantine equations.
    """
    if a < 2:
        raise ValueError("Pell parameter `a` must be >= 2.")
    sols: List[Tuple[int, int]] = [(1, 0)]
    if count == 1:
        return sols
    sols.append((a, 1))
    for _ in range(2, count):
        x_prev2, y_prev2 = sols[-2]
        x_prev1, y_prev1 = sols[-1]
        sols.append((2 * a * x_prev1 - x_prev2, 2 * a * y_prev1 - y_prev2))
    return sols


def verify_godel_singlefold_invariants() -> Dict:
    """
    Verifies the four exact mathematical invariants engraved on `Tabula VIII`:
      1. Exact Pell identity `x_n^2 - (a^2 - 1) y_n^2 == 1` across `a in 2..6, n in 0..6`.
      2. Single-fold integer polynomial witness uniqueness on Cantor's bijection
         `2*z = (x + y)*(x + y + 1) + 2*x` (`0..35` -> each `z` has *at most one* `(x, y)` in `N^2`).
      3. Cantor-Gödel 8x8 anti-diagonal construction `Delta_k = 1 - M[k, k]` escaping all 8 rows.
      4. Automorphism rigidity (`|Aut(P, <=)| == 1`) of the 7-element asymmetric poset gadget
         modeling `openai/math` Family 241 (`DegreeRigidity.lean`).
    """
    # 1. Pell identity
    for a in range(2, 7):
        d = a * a - 1
        for xn, yn in pell_matiyasevich_solutions(a, count=7):
            assert xn * xn - d * yn * yn == 1, f"Pell failure for a={a}: ({xn}, {yn})"

    # 2. Single-fold witness uniqueness on `P(z, x, y) = (x + y)*(x + y + 1) + 2*x - 2*z == 0`
    for z in range(36):
        witnesses = [
            (x, y)
            for x in range(10)
            for y in range(10)
            if (x + y) * (x + y + 1) + 2 * x - 2 * z == 0
        ]
        assert len(witnesses) == 1, f"Expected unique witness for z={z}, found {witnesses}"

    # 3. 8x8 Cantor-Gödel predicate matrix & anti-diagonal escape
    mat = np.zeros((8, 8), dtype=np.int32)
    for r in range(8):
        p = PRIMES_16[r]
        for c in range(8):
            mat[r, c] = ((p * (c + 3) + (r ^ c)) >> 1) & 1
    anti_diag = tuple(1 - int(mat[k, k]) for k in range(8))
    for r in range(8):
        row_t = tuple(int(mat[r, c]) for c in range(8))
        assert anti_diag[r] != row_t[r] and anti_diag != row_t

    # 4. Finite asymmetric poset rigidity (`|Aut(P, <=)| == 1`, zero non-identity automorphisms!)
    # 7-node Hasse covering edges: 0=bottom, 6=top, asymmetric chains of lengths 1, 2, 3 with cross-join:
    # 0 < 1 < 6 (len 2), 0 < 2 < 3 < 6 (len 3), 0 < 4 < 5 < 6 with 2 < 5 (breaks symmetry between chains!)
    import itertools
    n_pos = 7
    covers = {(0, 1), (1, 6), (0, 2), (2, 3), (3, 6), (0, 4), (4, 5), (5, 6), (2, 5)}
    # Transitive + reflexive closure
    le = {(i, i) for i in range(n_pos)} | covers
    changed = True
    while changed:
        changed = False
        for a_i in range(n_pos):
            for b_i in range(n_pos):
                if (a_i, b_i) in le:
                    for c_i in range(n_pos):
                        if (b_i, c_i) in le and (a_i, c_i) not in le:
                            le.add((a_i, c_i))
                            changed = True

    automorphisms = []
    for perm in itertools.permutations(range(n_pos)):
        ok = True
        for u_i in range(n_pos):
            for v_i in range(n_pos):
                if ((u_i, v_i) in le) != ((perm[u_i], perm[v_i]) in le):
                    ok = False
                    break
            if not ok:
                break
        if ok:
            automorphisms.append(perm)
    assert len(automorphisms) == 1 and automorphisms[0] == tuple(range(n_pos)), (
        f"Expected rigid poset Aut={{id}}, got {automorphisms}"
    )

    return {
        "matrix": mat,
        "anti_diagonal": anti_diag,
        "rigid_poset_covers": sorted(covers),
        "automorphism_count": len(automorphisms),
    }


def godel_diophantine_geometry(cx: float = 85.0, cy: float = 96.5) -> Dict:
    """
    Constructs `Tabula VIII · Speculum Diophantinum & Diagonalis Gödeliana`:
      1. Central Gödel Prime Astrolabe (`r_outer = 45.5 mm`, `r_inner = 41.5 mm`) marked with
         the first 16 primes `2, 3, ..., 53` and four sheaves of Pell-Matiyasevich hyperbolas
         `u^2 - d * v^2 = +-c` surrounding the central 8x8 Cantor-Gödel Diagonal Chamber.
      2. Central 8x8 Predicate Matrix (`40 x 40 mm`) with double-ring witness seals, quiet
         non-witness crosshairs, rubricated diagonal spine `(k, k)`, and the detached 8-cell
         Anti-Diagonal Witness Register `Delta_k = 1 - M[k, k]` suspended at `y = 148.5 mm`.
      3. Four Corner Logic & Computability Foil Medallions (`r = 10.8 mm`):
           - Upper-Left  (`MULTI-FOLD >=2`): Multiple witnesses on one vertical fiber (Babel redundancy)
           - Upper-Right (`SINGLE-FOLD <=1`): Family 242 unique witness fiber (`0` or `1` point per `x`)
           - Lower-Left  (`QUINE FIXED PT`): Diagonal self-substitution figure-eight meeting at `G`
           - Lower-Right (`AUT(D) = {ID}`): Family 241 rigid Turing-degree poset with zero symmetry.
    """
    inv = verify_godel_singlefold_invariants()
    mat = inv["matrix"]
    anti_diag = inv["anti_diagonal"]

    ink_strokes: List[Tuple[List[Point], float]] = []
    red_strokes: List[Tuple[List[Point], float]] = []

    r_out = 45.0
    r_in = 41.2
    for rr, w_mm in ((r_out, 0.24), (r_in, 0.14)):
        ink_strokes.append(([(cx + rr * math.cos(math.tau * i / 160), cy + rr * math.sin(math.tau * i / 160)) for i in range(161)], w_mm))

    # 16 Prime Gödel-Numbering radial divisions around the astrolabe annulus
    prime_labels: List[Tuple[float, float, str, bool, float]] = []
    for idx_p, p_val in enumerate(PRIMES_16):
        ang = -0.5 * math.pi + math.tau * idx_p / 16.0
        ca, sa = math.cos(ang), math.sin(ang)
        is_card = (idx_p % 4 == 0) or (p_val == 19)  # Highlight cardinal primes & shift prime 19!
        (red_strokes if p_val == 19 else ink_strokes).append((
            [(cx + r_in * ca, cy + r_in * sa), (cx + r_out * ca, cy + r_out * sa)],
            0.24 if is_card else 0.13,
        ))
        # Subtle sub-ticks inside the annulus encoding `p_val mod 6`
        for sub_i in range(1, 4):
            ang_s = ang + (math.tau / 64.0) * sub_i
            ink_strokes.append((
                [(cx + (r_out - 1.5) * math.cos(ang_s), cy + (r_out - 1.5) * math.sin(ang_s)),
                 (cx + r_out * math.cos(ang_s), cy + r_out * math.sin(ang_s))],
                0.09,
            ))
        if idx_p % 2 == 0 or p_val == 19:
            rl = r_out + 3.1
            prime_labels.append((cx + rl * ca, cy + rl * sa + 0.6, f"p={p_val}", p_val == 19, 1.50))

    # Central 8x8 Cantor-Gödel Matrix Chamber (`half = 19.2 mm` -> `38.4 x 38.4 mm`, fits inside `r_in = 41.2 mm` with Pell lunettes!)
    half_sq = 19.2
    x0_m, y0_m = cx - half_sq, cy - half_sq
    cell = (2.0 * half_sq) / 8.0  # 4.8 mm per cell

    # Pell-Matiyasevich hyperbola sheaves in the 4 circular lunettes between the 38.4mm square and r_in=41.2mm circle!
    ts = np.linspace(-1.35, 1.35, 90)
    for c_scale in (22.5, 26.0, 29.8, 33.8, 37.6):
        # 4 branches: top, bottom, left, right hyperbolas `u = +- c cosh(t), v = c sinh(t)`
        for orient in ("top", "bot", "left", "right"):
            pts_h: List[Point] = []
            for tv in ts:
                u_h = c_scale * math.cosh(tv)
                v_h = c_scale * 0.62 * math.sinh(tv)
                if orient == "top":
                    px, py = cx + v_h, cy - u_h
                elif orient == "bot":
                    px, py = cx + v_h, cy + u_h
                elif orient == "left":
                    px, py = cx - u_h, cy + v_h
                else:
                    px, py = cx + u_h, cy + v_h
                # Keep points strictly inside `r_in - 0.6` and outside the central 8x8 square!
                in_disk = math.hypot(px - cx, py - cy) <= (r_in - 0.7)
                out_box = (abs(px - cx) > half_sq + 0.6) or (abs(py - cy) > half_sq + 0.6)
                if in_disk and out_box:
                    pts_h.append((px, py))
                else:
                    if len(pts_h) >= 3:
                        ink_strokes.append((pts_h, 0.11))
                    pts_h = []
            if len(pts_h) >= 3:
                ink_strokes.append((pts_h, 0.11))

    # Outer & grid lines of the 8x8 Cantor-Gödel Matrix
    ink_strokes.append(([(x0_m, y0_m), (x0_m + 2 * half_sq, y0_m), (x0_m + 2 * half_sq, y0_m + 2 * half_sq), (x0_m, y0_m + 2 * half_sq), (x0_m, y0_m)], 0.24))
    for g_i in range(1, 8):
        gx_l = x0_m + g_i * cell
        gy_l = y0_m + g_i * cell
        ink_strokes.append(([(gx_l, y0_m), (gx_l, y0_m + 2 * half_sq)], 0.10))
        ink_strokes.append(([(x0_m, gy_l), (x0_m + 2 * half_sq, gy_l)], 0.10))

    # Rubricated Cantor Diagonal Spine `(k, k)`
    red_strokes.append(([(x0_m, y0_m), (x0_m + 2 * half_sq, y0_m + 2 * half_sq)], 0.28))

    for r_i in range(8):
        for c_i in range(8):
            ccx = x0_m + (c_i + 0.5) * cell
            ccy = y0_m + (r_i + 0.5) * cell
            on_diag = (r_i == c_i)
            val = int(mat[r_i, c_i])
            if val == 1:
                rr_c = 1.25 if on_diag else 1.05
                ring_c = [(ccx + rr_c * math.cos(math.tau * j / 28), ccy + rr_c * math.sin(math.tau * j / 28)) for j in range(29)]
                (red_strokes if on_diag else ink_strokes).append((ring_c, 0.22 if on_diag else 0.14))
                if on_diag:
                    red_strokes.append(([(ccx - 0.45, ccy), (ccx + 0.45, ccy)], 0.20))
            else:
                d_s = 0.72
                (red_strokes if on_diag else ink_strokes).append(([(ccx - d_s, ccy), (ccx + d_s, ccy)], 0.18 if on_diag else 0.10))
                (red_strokes if on_diag else ink_strokes).append(([(ccx, ccy - d_s), (ccx, ccy + d_s)], 0.18 if on_diag else 0.10))

    # Detached 8-Cell Inverted Anti-Diagonal Witness Row `Delta_k = 1 - M[k, k]` at `y = 152.0 mm`
    ry0 = 150.5
    ink_strokes.append(([(x0_m, ry0), (x0_m + 2 * half_sq, ry0), (x0_m + 2 * half_sq, ry0 + cell), (x0_m, ry0 + cell), (x0_m, ry0)], 0.20))
    for k_i in range(8):
        if k_i > 0:
            ink_strokes.append(([(x0_m + k_i * cell, ry0), (x0_m + k_i * cell, ry0 + cell)], 0.11))
        ccx = x0_m + (k_i + 0.5) * cell
        ccy = ry0 + 0.5 * cell
        # Dashed/faint projection tick above the register linking to column `k_i`
        red_strokes.append(([(ccx, ry0 - 2.2), (ccx, ry0 - 0.6)], 0.14))
        if anti_diag[k_i] == 1:
            ring_d = [(ccx + 1.25 * math.cos(math.tau * j / 28), ccy + 1.25 * math.sin(math.tau * j / 28)) for j in range(29)]
            red_strokes.append((ring_d, 0.24))
        else:
            red_strokes.append(([(ccx - 0.75, ccy - 0.75), (ccx + 0.75, ccy + 0.75)], 0.18))
            red_strokes.append(([(ccx - 0.75, ccy + 0.75), (ccx + 0.75, ccy - 0.75)], 0.18))

    # Four Corner Logic & Computability Foil Medallions (`r = 10.6 mm`)
    mr = 10.6
    # 1. Upper-Left `(30.5, 45.5)`: Multi-Fold MRDP Fiber (`>= 2` witnesses on single x-fiber)
    ulx, uly = 30.5, 45.5
    ink_strokes.append(([(ulx + mr * math.cos(math.tau * i / 84), uly + mr * math.sin(math.tau * i / 84)) for i in range(85)], 0.18))
    for fx_off in (-5.4, -1.8, 1.8, 5.4):
        ink_strokes.append(([(ulx + fx_off, uly - 7.4), (ulx + fx_off, uly + 7.4)], 0.10))
    # Smooth curve folding back across `fx_off = -1.8` and `1.8` to hit 3 witnesses on one vertical fiber!
    s_curve = [(ulx + 5.8 * math.sin(1.9 * s_t), uly + 6.8 * (s_t / 1.4)) for s_t in np.linspace(-1.4, 1.4, 60)]
    ink_strokes.append((s_curve, 0.15))
    for wy in (-4.8, 0.0, 4.8):
        red_strokes.append(([(ulx + 1.8 + 0.95 * math.cos(math.tau * j / 20), uly + wy + 0.95 * math.sin(math.tau * j / 20)) for j in range(21)], 0.22))

    # 2. Upper-Right `(139.5, 45.5)`: Single-Fold Family 242 Fiber (`<= 1` unique witness per `x`!)
    urx, ury = 139.5, 45.5
    ink_strokes.append(([(urx + mr * math.cos(math.tau * i / 84), ury + mr * math.sin(math.tau * i / 84)) for i in range(85)], 0.18))
    witness_heights = {0: -4.2, 2: 3.6, 3: -1.2, 5: 5.0}  # Fibers 1 and 4 are non-members (0 witnesses!)
    for idx_f, fx_off in enumerate((-6.0, -3.6, -1.2, 1.2, 3.6, 6.0)):
        ink_strokes.append(([(urx + fx_off, ury - 7.4), (urx + fx_off, ury + 7.4)], 0.10))
        if idx_f in witness_heights:
            wy = witness_heights[idx_f]
            red_strokes.append(([(urx + fx_off + 1.05 * math.cos(math.tau * j / 22), ury + wy + 1.05 * math.sin(math.tau * j / 22)) for j in range(23)], 0.24))

    # 3. Lower-Left `(30.5, 141.5)`: Quine-Gödel Self-Referential Fixed-Point Lemniscate `G <-> ~Prov(#G)`
    llx, lly = 30.5, 141.5
    ink_strokes.append(([(llx + mr * math.cos(math.tau * i / 84), lly + mr * math.sin(math.tau * i / 84)) for i in range(85)], 0.18))
    lem_a: List[Point] = []
    lem_b: List[Point] = []
    for ph in np.linspace(0.0, math.tau, 100):
        denom = 1.0 + math.sin(ph) ** 2
        lx_v = 7.8 * math.cos(ph) / denom
        ly_v = 7.8 * math.sin(ph) * math.cos(ph) / denom
        lem_a.append((llx + lx_v * 0.866 - ly_v * 0.5, lly + lx_v * 0.5 + ly_v * 0.866))
        lem_b.append((llx + lx_v * 0.866 + ly_v * 0.5, lly - lx_v * 0.5 + ly_v * 0.866))
    ink_strokes.append((lem_a, 0.15))
    ink_strokes.append((lem_b, 0.15))
    red_strokes.append(([(llx + 1.45 * math.cos(math.tau * j / 24), lly + 1.45 * math.sin(math.tau * j / 24)) for j in range(25)], 0.26))

    # 4. Lower-Right `(139.5, 141.5)`: Family 241 Rigid Poset of Turing Degrees (`Aut(D) = {id}`)
    lrx, lry = 139.5, 141.5
    ink_strokes.append(([(lrx + mr * math.cos(math.tau * i / 84), lry + mr * math.sin(math.tau * i / 84)) for i in range(85)], 0.18))
    poset_xy = {
        0: (lrx, lry + 7.2),          # 0 (computable base)
        1: (lrx - 5.8, lry + 0.5),    # 2-step left branch
        2: (lrx - 0.6, lry + 2.8),    # 3-step center-left lower
        3: (lrx - 1.2, lry - 2.6),    # 3-step center-left upper
        4: (lrx + 5.4, lry + 3.2),    # right lower
        5: (lrx + 5.2, lry - 2.4),    # right upper (receives asymmetric cross-edge 2->5!)
        6: (lrx, lry - 7.2),          # 0' / top join
    }
    for u_i, v_i in inv["rigid_poset_covers"]:
        is_asym = (u_i, v_i) == (2, 5)
        (red_strokes if is_asym else ink_strokes).append(([poset_xy[u_i], poset_xy[v_i]], 0.21 if is_asym else 0.13))
    for n_id, (px_n, py_n) in poset_xy.items():
        is_end = n_id in (0, 5, 6)
        ring_n = [(px_n + 0.85 * math.cos(math.tau * j / 20), py_n + 0.85 * math.sin(math.tau * j / 20)) for j in range(21)]
        (red_strokes if is_end else ink_strokes).append((ring_n, 0.20 if is_end else 0.14))

    labels = [
        (ulx, uly + 14.2, "MULTI-FOLD >=2", False, 1.80),
        (urx, ury + 14.2, "SINGLE-FOLD <=1", True, 1.80),
        (llx, lly + 14.2, "QUINE FIXED-PT", False, 1.80),
        (lrx, lry + 14.2, "AUT(D) = {ID}", True, 1.80),
        (cx, ry0 + cell + 4.2, "ANTI-DIAGONAL WITNESS DELTA = 1 - M[K,K]", True, 1.70),
    ]
    labels.extend(prime_labels)

    return {
        "invariants": inv,
        "ink_strokes": ink_strokes,
        "red_strokes": red_strokes,
        "labels": labels,
    }


def godel_vellum_field(nx: np.ndarray, ny: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    96-dpi vellum wash for Tabula VIII: Pell-hyperbola saddle harmonics (`x^2 - y^2`)
    crossed with a subtle Cantor-diagonal warm highlight band and prime radial rings.
    """
    xx = (nx - 0.50) * 2.2
    yy = (ny - 0.45) * 2.6
    env = np.exp(-0.68 * (xx * xx + 0.78 * yy * yy))

    pell_hyp = np.cos(4.5 * (xx * xx - yy * yy))
    diag_band = np.exp(-5.5 * ((xx - 0.78 * yy) ** 2))
    prime_rings = 0.5 + 0.5 * np.cos(11.0 * np.hypot(xx, yy))

    warm = np.clip(env * (0.55 * diag_band + 0.45 * (0.5 + 0.5 * pell_hyp)), 0.0, 1.0).astype(np.float32)
    cool = np.clip(env * (1.0 - 0.65 * diag_band) * prime_rings, 0.0, 1.0).astype(np.float32)
    return warm, cool
