import math
from typing import List, Tuple

Point = Tuple[float, float]


def rosette(
    cx: float,
    cy: float,
    r_base: float,
    amp: float,
    lobes: int,
    passes: int = 7,
    phase_step_deg: float = 9.0,
    radial_step: float = 0.45,
    steps: int = 360,
) -> List[List[Point]]:
    """Generates multi-pass guilloche rosette polylines in plate millimeters."""
    curves: List[List[Point]] = []
    for p in range(passes):
        ph = math.radians(p * phase_step_deg)
        r0 = r_base - p * radial_step
        pts: List[Point] = []
        for i in range(steps + 1):
            th = math.tau * i / steps
            r = r0 + amp * math.cos(lobes * th + ph) + 0.35 * amp * math.sin((lobes * 2) * th - ph)
            pts.append((cx + r * math.cos(th), cy + r * math.sin(th)))
        curves.append(pts)
    return curves


def wave_ring(
    cx: float,
    cy: float,
    r_mid: float,
    amp: float,
    cycles: int,
    phase_deg: float = 0.0,
    steps: int = 320,
) -> List[Point]:
    ph = math.radians(phase_deg)
    pts: List[Point] = []
    for i in range(steps + 1):
        th = math.tau * i / steps
        r = r_mid + amp * math.sin(cycles * th + ph)
        pts.append((cx + r * math.cos(th), cy + r * math.sin(th)))
    return pts


def lissajous_nodal(
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    p_freq: int,
    q_freq: int,
    delta_deg: float = 90.0,
    steps: int = 480,
) -> List[Point]:
    delta = math.radians(delta_deg)
    return [
        (
            cx + rx * math.sin(p_freq * (math.tau * i / steps) + delta),
            cy + ry * math.sin(q_freq * (math.tau * i / steps)),
        )
        for i in range(steps + 1)
    ]
