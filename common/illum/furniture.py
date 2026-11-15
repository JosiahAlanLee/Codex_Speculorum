import os
import random
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from reportlab.lib.colors import Color
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas

from common.geometry.core import Point, Wobble, arc_pts

REPO = Path(__file__).resolve().parents[2]
FONTS = REPO / "common" / "fonts"

MM = 72.0 / 25.4
PW, PH = 504.0, 720.0  # 7 x 10 in canonical Codex trim

# Canonical Codex Series RGB Palette (extracted from Codex-Intervallorum)
PAPER = (237, 230, 212)      # #ede6d4
INK = (22, 25, 24)           # #161918
RED = (163, 43, 36)          # #a32b24
SEPIA = (90, 67, 49)
OCHRE = (184, 154, 106)
UMBER = (109, 95, 75)
SLATE = (74, 86, 92)
VERDIGRIS = (98, 122, 96)
DARK = (28, 24, 19)
LIGHT = (235, 225, 200)

HEX_PAPER = "#ede6d4"
HEX_INK = "#161918"
HEX_RED = "#a32b24"
HEX_MUTE = "#5a4331"

W = {
    "core": 0.9,
    "orn": 0.55,
    "hair": 0.3,
    "cip": 0.5,
    "heavy": 1.4,
}

_FONT_MAP: Optional[Dict[str, str]] = None

VOL1_FONT_FILES = {
    "Fell": "IMFeENrm28P.ttf",
    "FellIt": "IMFeENit28P.ttf",
    "FellSC": "IMFeENsc28P.ttf",
    "FellTitle": "IMFellEnglish-Regular.ttf",
    "Mono": "IBMPlexMono-Regular.ttf",
    "Math": "DejaVuSerif.ttf",
    "Hand": "SueEllenFrancisco-Regular.ttf",
    "Pica": "IMFePIrm28P.ttf",
    "PicaIt": "IMFePIit28P.ttf",
    "DMSerif": "DMSerifDisplay-Regular.ttf",
}

SYSTEM_TTF_CANDIDATES = {
    "serif": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
    ],
    "serif_it": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf",
    ],
    "serif_bold": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
    ],
    "mono": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
    ],
}


def rgb(c: Tuple[int, int, int], a: float = 1.0) -> Color:
    return Color(c[0] / 255.0, c[1] / 255.0, c[2] / 255.0, alpha=a)


def _register_ttf_if_exists(alias: str, path: Path) -> bool:
    if path.is_file():
        if alias not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(alias, str(path)))
        return True
    return False


def fonts() -> Dict[str, str]:
    """
    Registers Volume I press fonts from common/fonts/ when present, falling back
    gracefully to installed system TrueType serifs or standard PDF Type1 fonts.
    """
    global _FONT_MAP
    if _FONT_MAP is not None:
        return dict(_FONT_MAP)

    sys_resolved: Dict[str, str] = {
        "serif": "Times-Roman",
        "serif_it": "Times-Italic",
        "serif_bold": "Times-Bold",
        "mono": "Courier",
    }
    for role, paths in SYSTEM_TTF_CANDIDATES.items():
        for p in paths:
            alias = f"CodexSys_{role}"
            if _register_ttf_if_exists(alias, Path(p)):
                sys_resolved[role] = alias
                break

    role_defaults = {
        "Fell": sys_resolved["serif"],
        "FellIt": sys_resolved["serif_it"],
        "FellSC": sys_resolved["serif_bold"],
        "FellTitle": sys_resolved["serif_bold"],
        "Mono": sys_resolved["mono"],
        "Math": sys_resolved["serif"],
        "Hand": sys_resolved["serif_it"],
        "Pica": sys_resolved["serif"],
        "PicaIt": sys_resolved["serif_it"],
        "DMSerif": sys_resolved["serif_bold"],
    }

    resolved: Dict[str, str] = {}
    for logical, filename in VOL1_FONT_FILES.items():
        candidate = FONTS / filename
        if _register_ttf_if_exists(logical, candidate):
            resolved[logical] = logical
        else:
            resolved[logical] = role_defaults[logical]

    _FONT_MAP = resolved
    return dict(_FONT_MAP)


class Hand:
    """ReportLab stroke helper matching Codex-Intervallorum stroke weights and inks."""

    def __init__(self, c: Canvas, rng: Optional[random.Random] = None, amp: float = 0.0, colors: Optional[Dict[str, Tuple[int, int, int]]] = None):
        self.c = c
        self.rng = rng or random.Random(0)
        self.wobble = Wobble(self.rng, amp=amp)
        self.colors = {
            "ink": INK,
            "red": RED,
            "sepia": SEPIA,
            "ochre": OCHRE,
            "umber": UMBER,
            "slate": SLATE,
            "verdigris": VERDIGRIS,
        }
        if colors:
            self.colors.update(colors)

    def stroke(
        self,
        pts: Sequence[Point],
        weight: str = "orn",
        color: str = "ink",
        closed: bool = False,
        amp: Optional[float] = None,
        dash: Optional[Sequence[float]] = None,
    ) -> None:
        if len(pts) < 2:
            return
        w_pts = self.wobble.perturb(pts, amp=amp) if (amp or self.wobble.amp > 0) else list(pts)
        self.c.saveState()
        self.c.setStrokeColor(rgb(self.colors.get(color, INK)))
        self.c.setLineWidth(W.get(weight, float(weight) if isinstance(weight, (int, float)) else 0.55))
        self.c.setLineCap(1)
        self.c.setLineJoin(1)
        if dash:
            self.c.setDash(list(dash), 0)
        p = self.c.beginPath()
        p.moveTo(w_pts[0][0], w_pts[0][1])
        for x, y in w_pts[1:]:
            p.lineTo(x, y)
        if closed:
            p.close()
        self.c.drawPath(p, stroke=1, fill=0)
        self.c.restoreState()

    def dot(self, x: float, y: float, r: float = 0.9, color: str = "ink") -> None:
        self.c.saveState()
        self.c.setFillColor(rgb(self.colors.get(color, INK)))
        self.c.circle(x, y, r, stroke=0, fill=1)
        self.c.restoreState()

    def ring(self, x: float, y: float, r: float = 1.6, weight: str = "cip", color: str = "ink") -> None:
        pts = arc_pts(x, y, r, 0.0, 360.0, steps=28)
        self.stroke(pts, weight=weight, color=color, closed=True, amp=0.0)


class YDown:
    """Top-left origin adapter (in points or mm) onto a bottom-left ReportLab canvas."""

    def __init__(self, hand: Hand, page_height: float = PH, scale: float = 1.0):
        self.hand = hand
        self.ph = page_height
        self.scale = scale

    def P(self, x: float, y: float) -> Point:
        return (x * self.scale, self.ph - y * self.scale)

    def stroke(self, pts: Iterable[Point], **kwargs) -> None:
        mapped = [self.P(x, y) for x, y in pts]
        self.hand.stroke(mapped, **kwargs)

    def dot(self, x: float, y: float, r: float = 0.9, color: str = "ink") -> None:
        px, py = self.P(x, y)
        self.hand.dot(px, py, r=r * self.scale, color=color)

    def ring(self, x: float, y: float, r: float = 1.6, weight: str = "cip", color: str = "ink") -> None:
        px, py = self.P(x, y)
        self.hand.ring(px, py, r=r * self.scale, weight=weight, color=color)


def ground(c: Canvas, color: Tuple[int, int, int] = PAPER, pw: float = PW, ph: float = PH) -> None:
    c.saveState()
    c.setFillColor(rgb(color))
    c.rect(0, 0, pw, ph, stroke=0, fill=1)
    c.restoreState()


def ruled_frame(c: Canvas, x: float = 44.0, y: float = 52.0, w: float = PW - 88.0, h: float = PH - 104.0, double: bool = True) -> Tuple[float, float, float, float]:
    hnd = Hand(c, amp=0.0)
    pts = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
    hnd.stroke(pts, weight="orn", color="ink", closed=True)
    if double:
        inset = 3.0
        inner = [(x + inset, y + inset), (x + w - inset, y + inset), (x + w - inset, y + h - inset), (x + inset, y + h - inset)]
        hnd.stroke(inner, weight="hair", color="red", closed=True)
    return (x, y, w, h)


def running_head(c: Canvas, book_title: str, folio_label: str, page_no: int) -> None:
    fmap = fonts()
    c.saveState()
    c.setFillColor(rgb(SEPIA))
    c.setFont(fmap["FellSC"], 8.5)
    c.drawCentredString(PW / 2.0, PH - 36.0, book_title.upper())
    c.setFont(fmap["Mono"], 8.0)
    if page_no % 2 == 1:
        c.drawRightString(PW - 48.0, 32.0, f"{folio_label} · {page_no}")
    else:
        c.drawString(48.0, 32.0, f"{page_no} · {folio_label}")
    c.restoreState()


def wrap(text: str, font_name: str, font_size: float, max_width: float) -> List[str]:
    words = text.replace("`", "").split()
    if not words:
        return [""]
    lines: List[str] = []
    cur = ""
    for word in words:
        trial = f"{cur} {word}" if cur else word
        if pdfmetrics.stringWidth(trial, font_name, font_size) <= max_width:
            cur = trial
            continue
        if cur:
            lines.append(cur)
        if pdfmetrics.stringWidth(word, font_name, font_size) <= max_width:
            cur = word
            continue
        cur = ""
        for char in word:
            if cur and pdfmetrics.stringWidth(cur + char, font_name, font_size) > max_width:
                lines.append(cur)
                cur = ""
            cur += char
    lines.append(cur)
    return lines
