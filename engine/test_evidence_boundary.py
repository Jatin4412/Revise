from __future__ import annotations

import math
import unittest

from engine.revise.evidence import fuse_evidence, validate_evidence
from engine.revise.models import Evidence


class EvidenceBoundaryTests(unittest.TestCase):
    def test_invalid_result_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_evidence((Evidence("test", "llm", "passed", 1.0),))

    def test_non_finite_confidence_is_rejected(self):
        for confidence in (math.nan, math.inf, -math.inf):
            with self.subTest(confidence=confidence):
                with self.assertRaises(ValueError):
                    validate_evidence((Evidence("test", "llm", "pass", confidence),))

    def test_out_of_range_confidence_is_rejected(self):
        for confidence in (-0.01, 1.01):
            with self.subTest(confidence=confidence):
                with self.assertRaises(ValueError):
                    validate_evidence((Evidence("test", "llm", "pass", confidence),))

    def test_empty_metadata_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_evidence((Evidence("", "llm", "pass", 1.0),))
        with self.assertRaises(ValueError):
            validate_evidence((Evidence("test", "", "pass", 1.0),))

    def test_malformed_evidence_cannot_be_fused(self):
        with self.assertRaises(ValueError):
            fuse_evidence((Evidence("test", "llm", "pass", 2.0),))

    def test_custom_methods_remain_supported(self):
        evidence = Evidence("my.verifier", "custom", "pass", 0.8, ("checked",))
        fused = fuse_evidence((evidence,))
        self.assertEqual(fused.evidence, (evidence,))
        self.assertEqual(fused.confidence, 0.8)


if __name__ == "__main__":
    unittest.main()
