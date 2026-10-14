import re
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class LocalizationQuality(unittest.TestCase):
    def test_latest_combined_languages_have_no_replacement_glyphs_or_java_identifier_fallbacks(self):
        candidates = list((ROOT / 'build').glob('combined_all_*_final_v*/RP/texts/pt_BR.lang'))
        self.assertTrue(candidates)
        candidates.sort(key=lambda path: int(re.search(r'_v(\d+)', path.parents[2].name).group(1)))
        text = candidates[-1].read_text(encoding='utf-8')
        self.assertNotIn('\ufffd', text)
        self.assertNotRegex(text, r'=.*Syringeitem')
        self.assertNotRegex(text, r'=.*[A-Za-z]+moduleitem')

    def test_repair_source_sanitizes_corrupt_upstream_titles(self):
        source = (ROOT / 'tools/repair_combined_pack.py').read_text(encoding='utf-8')
        self.assertIn("'\\ufffd' not in text", source)
        self.assertIn('portuguese_fallback', source)
        self.assertIn('humanized_name', source)


if __name__ == '__main__':
    unittest.main()
