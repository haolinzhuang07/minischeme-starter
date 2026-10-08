"""Regression checks for symbol comparisons. Run: python -m unittest discover -s tests"""
from pathlib import Path
import subprocess
import sys
import unittest


ENTRY = Path(__file__).resolve().parents[1] / "src" / "main.py"


class SymbolComparisonTests(unittest.TestCase):
    def test_comparisons(self):
        cases = [
            ("(< 'a 'b)", "#t"),
            ("(> 'b 'a)", "#t"),
            ("(<= 'a 'a 'b)", "#t"),
            ("(>= 'b 'b 'a)", "#t"),
            ("(= 'a 'a)", "#t"),
            ("(= 'a 'b)", "#f"),
            ("(< 'a 'b 'a)", "#f"),
            ("(> 'a 'b)", "#f"),
            ("(<= 'b 'a)", "#f"),
            ("(>= 'a 'b)", "#f"),
            ("(< 'A 'a)", "#t"),
        ]
        for source, expected in cases:
            with self.subTest(source=source):
                result = subprocess.run(
                    [sys.executable, str(ENTRY)],
                    input=source, text=True, capture_output=True, timeout=5,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, expected + "\n")


if __name__ == "__main__":
    unittest.main()
