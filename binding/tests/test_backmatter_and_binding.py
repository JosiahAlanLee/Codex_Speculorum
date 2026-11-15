import json
from pathlib import Path
import unittest

from binding import backmatter

REPO = Path(__file__).resolve().parents[2]


class TestDynamicBackmatter(unittest.TestCase):
    def test_dynamic_keys_match_bibliography_records_without_hardcoded_ranges(self):
        """
        Replaces Volume I's hardcoded `{f'V/S{i}' for i in range(1, 10)}` check
        with a dynamic schema & duplicate-key invariant driven by bibliography-records.json.
        """
        records = backmatter.load_records(REPO)
        self.assertGreaterEqual(len(records), 2)
        seen = set()
        for r in records:
            self.assertTrue(r.get("keys"), "Record must declare at least one citation key.")
            self.assertTrue(r.get("citation", "").strip(), "Citation string must be non-empty.")
            self.assertIn("inspection", r, "Record must explicitly state its inspection scope.")
            for k in r["keys"]:
                self.assertNotIn(k, seen, f"Duplicate bibliography key: {k}")
                seen.add(k)

    def test_backmatter_renders_on_recto(self):
        pdf_bytes, pages = backmatter.render_backmatter_pdf(REPO, start_page=11, paint_ground=True)
        self.assertGreater(len(pdf_bytes), 500)
        self.assertGreaterEqual(pages, 1)


if __name__ == "__main__":
    unittest.main()
