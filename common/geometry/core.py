import math
import random
from typing import List, Sequence, Tuple

Point = Tuple[float, float]


class Wobble:
    """Deterministic hand-tremor perturbation for organic pen-plotter strokes."""

    def __init__(self, rng: random.Random, amp: float = 0.18, wl: Tuple[float, float] = (3.5, 9.5)):
        self.rng = rng
        self.amp = amp
        self.wl = wl

    def perturb(self, pts: Sequence[Point], amp: float = None) -> List[Point]:
        a = self.amp if amp is None else amp
        if a <= 0.0 or len(pts) < 2:
            return list(pts)
        phase = self.rng.uniform(0.0, math.tau)
        freq = math.tau / self.rng.uniform(self.wl[0], self.wl[1])
        out: List[Point] = []
        dist = 0.0
        for idx, (x, y) in enumerate(pts):
            if idx > 0:
                px, py = pts[idx - 1]
                dx, dy = x - px, y - py
                seg = math.hypot(dx, dy)
                dist += seg
                if seg > 1e-6:
                    nx, ny = -dy / seg, dx / seg
                    disp = a * math.sin(dist * freq + phase)
                    out.append((x + nx * disp, y + ny * disp))
                    continue
            out.append((x, y))
        return out


def arc_pts(cx: float, cy: float, r: float, a0_deg: float, a1_deg: float, steps: int = 48) -> List[Point]:
    a0 = math.radians(a0_deg)
    a1 = math.radians(a1_deg)
    return [
        (cx + r * math.cos(a0 + (a1 - a0) * i / max(1, steps)),
         cy + r * math.sin(a0 + (a1 - a0) * i / max(1, steps)))
        for i in range(steps + 1)
    ]


def bezier(p0: Point, p1: Point, p2: Point, p3: Point, steps: int = 32) -> List[Point]:
    pts: List[Point] = []
    for i in range(steps + 1):
        t = i / max(1, steps)
        u = 1.0 - t
        x = (u**3) * p0[0] + 3 * (u**2) * t * p1[0] + 3 * u * (t**2) * p2[0] + (t**3) * p3[0]
        y = (u**3) * p0[1] + 3 * (u**2) * t * p1[1] + 3 * u * (t**2) * p2[1] + (t**3) * p3[1]
        pts.append((x, y))
    return pts


def catmull(pts: Sequence[Point], samples_per_seg: int = 12) -> List[Point]:
    if len(pts) < 3:
        return list(pts)
    ext = [pts[0]] + list(pts) + [pts[-1]]
    out: List[Point] = []
    for i in range(1, len(ext) - 2):
        p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
        for j in range(samples_per_seg):
            t = j / samples_per_seg
            t2, t3 = t * t, t * t * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, y))
    out.append(pts[-1])
    return out


def curl_pts(x0: float, y0: float, r0: float, turns: float = 1.25, steps: int = 36) -> List[Point]:
    pts: List[Point] = []
    for i in range(steps + 1):
        u = i / max(1, steps)
        ang = u * turns * math.tau
        rad = r0 * (1.0 - 0.82 * u)
        pts.append((x0 + rad * math.cos(ang), y0 + rad * math.sin(ang)))
    return pts
