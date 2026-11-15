from typing import Iterable, Sequence, Tuple
from common.geometry.core import Point
from common.illum import furniture as fu


class Map:
    """Maps millimeter plate coordinates onto a centered 504x720 pt Codex leaf."""

    def __init__(self, width_mm: float = 170.0, height_mm: float = 220.0, pw: float = fu.PW, ph: float = fu.PH):
        self.width_mm = width_mm
        self.height_mm = height_mm
        self.pw = pw
        self.ph = ph
        self.x0 = (pw - width_mm * fu.MM) / 2.0
        self.y0 = (ph - height_mm * fu.MM) / 2.0

    def P(self, x_mm: float, y_mm: float) -> Point:
        return (self.x0 + x_mm * fu.MM, self.y0 + (self.height_mm - y_mm) * fu.MM)

    def mm(self, v_mm: float) -> float:
        return v_mm * fu.MM


def bbox_of(pts: Iterable[Point]) -> Tuple[float, float, float, float]:
    pts_list = list(pts)
    xs = [p[0] for p in pts_list]
    ys = [p[1] for p in pts_list]
    return (min(xs), min(ys), max(xs), max(ys))


def inside(p: Point, box: Tuple[float, float, float, float]) -> bool:
    return box[0] <= p[0] <= box[2] and box[1] <= p[1] <= box[3]
