import unittest

from engine.revise.decision import decide
from engine.revise.external import SourceVerifier, run_external_verifiers
from engine.revise.models import Decision, DimensionResult, EvaluationProfile, EvaluationResult, Evidence, Mode, TaskContract
from engine.revise.profile import build_profile


class FakeFetcher:
    def __init__(self, results):
        self.results = results
        self.calls = []

    def fetch(self, url, *, timeout, max_bytes):
        self.calls.append((url, timeout, max_bytes))
        result = self.results[url]
        if isinstance(result, Exception):
            raise result
        return result


class ExternalVerificationTests(unittest.TestCase):
    def contract(self, *, requirements=()):
        return TaskContract(
            goal="Research the topic and cite sources",
            requirements=requirements,
            mode=Mode.BASIC,
        )

    def test_research_profile_selects_external_source_verification(self):
        profile = build_profile(self.contract())
        self.assertIn("source_verification", profile.external_verification)
        self.assertNotIn("source_verification", profile.dimensions)
        self.assertIn("groundedness", profile.dimensions)
        self.assertIn("evidence_quality", profile.dimensions)

    def test_reachable_source_passes(self):
        fetcher = FakeFetcher({"https://example.com/source": (200, "https://example.com/source", "text/html; charset=utf-8")})
        verifier = SourceVerifier(fetcher=fetcher)
        result = verifier.verify(self.contract(), "Source: https://example.com/source", EvaluationProfile(dimensions=("correctness",)))
        self.assertEqual(result[0].result, "pass")
        self.assertIn("status:200", result[0].provenance)

    def test_unavailable_source_fails(self):
        fetcher = FakeFetcher({"https://example.com/missing": (404, "https://example.com/missing", "text/html")})
        verifier = SourceVerifier(fetcher=fetcher)
        result = verifier.verify(self.contract(), "Source: https://example.com/missing", EvaluationProfile(dimensions=("correctness",)))
        self.assertEqual(result[0].result, "fail")
        self.assertIn("status:404", result[0].provenance)

    def test_required_citations_fail_when_none_are_present(self):
        verifier = SourceVerifier(fetcher=FakeFetcher({}))
        result = verifier.verify(self.contract(), "Here is a research answer without links.", EvaluationProfile(dimensions=("correctness",)))
        self.assertEqual(result[0].result, "fail")
        self.assertIn("citation_required", result[0].provenance)

    def test_duplicate_urls_are_checked_once_and_source_limit_is_bounded(self):
        urls = [f"https://example.com/{index}" for index in range(6)]
        fetcher = FakeFetcher({url: (200, url, "text/html") for url in urls})
        verifier = SourceVerifier(fetcher=fetcher, max_sources=4)
        response = " ".join(urls[:2] + urls[:4])
        result = verifier.verify(self.contract(), response, EvaluationProfile(dimensions=("correctness",)))
        self.assertEqual(len(result), 4)
        self.assertEqual(len(fetcher.calls), 4)
        self.assertEqual(len({call[0] for call in fetcher.calls}), 4)

    def test_fetch_error_becomes_external_failure(self):
        fetcher = FakeFetcher({"https://example.com/down": RuntimeError("offline")})
        verifier = SourceVerifier(fetcher=fetcher)
        result = verifier.verify(self.contract(), "Source: https://example.com/down", EvaluationProfile(dimensions=("correctness",)))
        self.assertEqual(result[0].result, "fail")
        self.assertIn("fetch_error:RuntimeError", result[0].provenance)

    def test_registry_runs_external_verifier(self):
        contract = self.contract()
        profile = build_profile(contract)
        fetcher = FakeFetcher({"https://example.com/source": (200, "https://example.com/source", "text/html")})
        evidence = run_external_verifiers(
            contract,
            "https://example.com/source",
            profile,
            registry={"source_verification": SourceVerifier(fetcher=fetcher)},
        )
        self.assertTrue(any(item.method == "external" and item.result == "pass" for item in evidence))

    def test_missing_configured_external_verifier_fails_closed(self):
        contract = self.contract()
        profile = build_profile(contract)
        evidence = run_external_verifiers(contract, "https://example.com/source", profile, registry={})
        self.assertEqual(len(evidence), 1)
        self.assertEqual(evidence[0].result, "fail")
        self.assertIn("verifier_unavailable:source_verification", evidence[0].provenance)

    def test_external_failure_blocks_acceptance(self):
        profile = EvaluationProfile(
            dimensions=("goal_alignment",),
            minimum_scores={"goal_alignment": 0.70},
            required_dimensions=("goal_alignment",),
            minimum_confidence=0.60,
            minimum_overall_score=0.75,
            max_revisions=1,
        )
        result = EvaluationResult(
            Decision.ACCEPT,
            0.95,
            0.95,
            dimensions={"goal_alignment": DimensionResult(0.95, 0.95, "pass")},
            evidence=(Evidence("external.source_verification", "external", "fail", 1.0, ("status:404",)),),
        )
        decision = decide(self.contract(), profile, result, revisions_used=0)
        self.assertEqual(decision.decision, Decision.REVISE)


if __name__ == "__main__":
    unittest.main()
