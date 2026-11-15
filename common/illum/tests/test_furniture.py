import io
import unittest
from reportlab.pdfgen import canvas
from common.illum import furniture as fu


class TestFurniture(unittest.TestCase):
    def test_canonical_dimensions_and_palette(self):
        self.assertEqual((fu.PW, fu.PH), (504.0, 720.0))
        self.assertEqual(fu.PAPER, (237, 230, 212))
        self.assertEqual(fu.INK, (22, 25, 24))
        self.assertEqual(fu.RED, (163, 43, 36))

    def test_fonts_and_ruled_frame_render(self):
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=(fu.PW, fu.PH))
        fmap = fu.fonts()
        self.assertIn("Fell", fmap)
        self.assertIn("Mono", fmap)
        fu.ground(c)
        box = fu.ruled_frame(c)
        self.assertEqual(len(box), 4)
        c.showPage()
        c.save()
        self.assertGreater(len(buf.getvalue()), 400)


if __name__ == "__main__":
    unittest.main()
