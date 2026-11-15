import math
from typing import Dict, List, Optional, Sequence, Tuple
from xml.sax.saxutils import escape

Point = Tuple[float, float]


class Plate:
    """
    Native two-layer, two-ink procedural plate builder matching
    Codex-Intervallorum's 170 x 220 mm SVG / ReportLab plate specification.
    """

    def __init__(
        self,
        title: str,
        width: float = 170.0,
        height: float = 220.0,
        ink: str = "#161918",
        red: str = "#a32b24",
        paper: str = "#ede6d4",
    ):
        self.title = title
        self.width = width
        self.height = height
        self.ink = ink
        self.red = red
        self.paper = paper
        self.strokes: List[Dict] = []
        self.labels: List[Dict] = []
        self.extra_paths: List[str] = []

    def add(self, points: Sequence[Point], red: bool = False, width: float = 0.16, layer: str = "art") -> None:
        if len(points) >= 2:
            self.strokes.append({
                "points": list(points),
                "red": bool(red),
                "width": float(width),
                "layer": layer,
            })

    def ring(self, cx: float, cy: float, r: float, red: bool = False, width: float = 0.16, steps: int = 120) -> None:
        pts = [
            (cx + r * math.cos(math.tau * i / steps), cy + r * math.sin(math.tau * i / steps))
            for i in range(steps + 1)
        ]
        self.add(pts, red=red, width=width)

    def text(self, x: float, y: float, content: str, size_mm: float = 3.0, red: bool = False, anchor: str = "middle") -> None:
        self.labels.append({
            "x": x,
            "y": y,
            "text": content,
            "size": size_mm,
            "red": red,
            "anchor": anchor,
        })

    def add_raw_svg_path(self, svg_element: str) -> None:
        self.extra_paths.append(svg_element)

    def svg(self, opaque_ground: bool = True) -> str:
        lines = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}mm" height="{self.height}mm" viewBox="0 0 {self.width:.2f} {self.height:.2f}">',
        ]
        if opaque_ground:
            lines.append(f'  <rect x="0" y="0" width="{self.width:.2f}" height="{self.height:.2f}" fill="{self.paper}"/>')

        lines.append('  <g id="layer-art" fill="none" stroke-linecap="round" stroke-linejoin="round">')
        for st in self.strokes:
            if st["layer"] != "art":
                continue
            col = self.red if st["red"] else self.ink
            d = "M " + " L ".join(f"{x:.3f} {y:.3f}" for x, y in st["points"])
            lines.append(f'    <path d="{d}" stroke="{col}" stroke-width="{st["width"]:.3f}"/>')
        for raw in self.extra_paths:
            lines.append(f"    {raw}")
        lines.append("  </g>")

        lines.append('  <g id="layer-text" fill="none" stroke-linecap="round" stroke-linejoin="round">')
        for st in self.strokes:
            if st["layer"] != "text":
                continue
            col = self.red if st["red"] else self.ink
            d = "M " + " L ".join(f"{x:.3f} {y:.3f}" for x, y in st["points"])
            lines.append(f'    <path d="{d}" stroke="{col}" stroke-width="{st["width"]:.3f}"/>')
        for lb in self.labels:
            col = self.red if lb["red"] else self.ink
            lines.append(
                f'    <text x="{lb["x"]:.3f}" y="{lb["y"]:.3f}" fill="{col}" stroke="none" '
                f'font-family="serif" font-size="{lb["size"]:.2f}" text-anchor="{lb["anchor"]}">{escape(lb["text"])}</text>'
            )
        lines.append("  </g>")
        lines.append("</svg>")
        return "\n".join(lines) + "\n"
