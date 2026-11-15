import unittest
from docs.objections.validate import append_only, parse_register, status


class TestObjectionsValidator(unittest.TestCase):
    SAMPLE = """# Register

## O-001 · 2026-11-14 · Claude Opus
- Location: `books/01_liber_primus`
- Raised by: in session
- Objection: Example objection text.
- 2026-11-14 · Author: deferred — until primary monochord check completes
"""

    def test_valid_parse_and_append(self):
        entries = parse_register(self.SAMPLE)
        self.assertEqual(len(entries), 1)
        self.assertEqual(status(entries[0]), "deferred")
        extended = self.SAMPLE + "- 2026-11-15 · Author: accepted — #12\n"
        entries2 = parse_register(extended)
        self.assertEqual(status(entries2[0]), "accepted")
        append_only(self.SAMPLE, extended)

    def test_overruled_requires_given(self):
        bad = self.SAMPLE + "- 2026-11-15 · Author: overruled — missing given clause\n"
        with self.assertRaises(ValueError):
            parse_register(bad)

    def test_append_only_catches_mutation(self):
        mutated = self.SAMPLE.replace("Example objection text.", "Edited text.")
        with self.assertRaises(ValueError):
            append_only(self.SAMPLE, mutated)


if __name__ == "__main__":
    unittest.main()
