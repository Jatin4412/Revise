import unittest

from engine.revise.decision import decide
from engine.revise.external import SourceVerifier, run_external_verifiers
from engine.revise.models import Decision, DimensionResult, EvaluationProfile, EvaluationResult, Evidence, Mode, TaskContract
from engine.revise.profile import build_profile


class FakeFetcher:
    def __init__(self, results): self.results, self.calls = results, []
    def fetch(self, url, *, timeout, max_bytes):
        self.calls.append((url, timeout, max_bytes))
        result = self.results[url]
        if isinstance(result, Exception): raise result
        return result


class ExternalVerificationTests(unittest.TestCase):
    def contract(self, *, requirements=()):
        return TaskContract(goal="Research the topic and cite sources", requirements=requirements, mode=Mode.BASIC)

    def policy(self): return EvaluationProfile(dimensions=("correctness",))

    def test_research_profile_selects_external_source_verification(self):
        profile = build_profile(self.contract())
        self.assertIn("source_verification", profile.external_verification)
        self.assertNotIn("source_verification", profile.dimensions)
        self.assertIn("groundedness", profile.dimensions)
        self.assertIn("evidence_quality", profile.dimensions)

    def test_reachable_source_passes(self):
        fetcher = FakeFetcher({"https://example.com/source": (200, "https://example.com/source", "text/html; charset=utf-8")})
        result = SourceVerifier(fetcher=fetcher).verify(self.contract(), "Source: https://example.com/source", self.policy())
        self.assertEqual(result[0].result, "pass")
        self.assertIn("status:200", result[0].provenance)

    def test_unavailable_source_fails(self):
        fetcher = FakeFetcher({"https://example.com/missing": (404, "https://example.com/missing", "text/html")})
        result = SourceVerifier(fetcher=fetcher).verify(self.contract(), "Source: https://example.com/missing", self.policy())
        self.assertEqual(result[0].result, "fail")
        self.assertIn("status:404", result[0].provenance)

    def test_required_citations_fail_when_none_are_present(self):
        result = SourceVerifier(fetcher=FakeFetcher({})).verify(self.contract(), "Here is a research answer without links.", self.policy())
        self.assertEqual(result[0].result, "fail")
        self.assertIn("citation_required", result[0].provenance)

    def test_duplicate_urls_are_checked_once_and_source_limit_is_bounded(self):
        urls = [f"https://example.com/{index}" for index in range(6)]
        fetcher = FakeFetcher({url: (200, url, "text/html") for url in urls})
        response = " ".join(urls + [urls[0], urls[1]])
        result = SourceVerifier(fetcher=fetcher, max_sources=4).verify(self.contract(), response, self.policy())
        self.assertEqual(len(fetcher.calls), 4)
        self.assertEqual(len({call[0] for call in fetcher.calls}), 4)
        self.assertTrue(any(item.result == "fail" and "source_limit_exhausted" in item.provenance for item in result))

    def test_duplicate_urls_below_limit_remain_deduplicated(self):
        url = "https://example.com/source"
        fetcher = FakeFetcher({url: (200, url, "text/html")})
        result = SourceVerifier(fetcher=fetcher, max_sources=4).verify(self.contract(), f"{url} {url} {url}", self.policy())
        self.assertEqual(len(fetcher.calls), 1)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].result, "pass")

    def test_source_limit_is_applied_after_deduplication(self):
        urls = [f"https://example.com/{index}" for index in range(4)]
        fetcher = FakeFetcher({url: (200, url, "text/html") for url in urls})
        response = " ".join(urls + [urls[0], urls[1]])
        result = SourceVerifier(fetcher=fetcher, max_sources=4).verify(self.contract(), response, self.policy())
        self.assertEqual(len(fetcher.calls), 4)
        self.assertFalse(any("source_limit_exhausted" in item.provenance for item in result))

    def test_source_limit_counts_unique_sources_not_duplicate_citations(self):
        urls = [f"https://example.com/{index}" for index in range(6)]
        fetcher = FakeFetcher({url: (200, url, "text/html") for url in urls})
        response = " ".join((urls[0], urls[0], urls[1], urls[1], urls[2], urls[2], urls[3], urls[3], urls[4]))
        result = SourceVerifier(fetcher=fetcher, max_sources=4).verify(self.contract(), response, self.policy())
        self.assertEqual(len(fetcher.calls), 4)
        self.assertEqual({call[0] for call in fetcher.calls}, set(urls[:4]))
        limit_events = [item for item in result if "source_limit_exhausted" in item.provenance]
        self.assertEqual(len(limit_events), 1)
        self.assertIn("sources_available:5", limit_events[0].provenance)
        self.assertIn("sources_checked:4", limit_events[0].provenance)

    def test_source_limit_zero_checks_nothing_and_fails_closed(self):
        url = "https://example.com/source"
        fetcher = FakeFetcher({url: (200, url, "text/html")})
        result = SourceVerifier(fetcher=fetcher, max_sources=0).verify(self.contract(), url, self.policy())
        self.assertEqual(fetcher.calls, [])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].result, "fail")
        self.assertIn("source_limit_exhausted", result[0].provenance)

    def test_fetch_error_becomes_external_failure(self):
        result = SourceVerifier(fetcher=FakeFetcher({"https://example.com/down": RuntimeError("offline")})).verify(self.contract(), "Source: https://example.com/down", self.policy())
        self.assertEqual(result[0].result, "fail")
        self.assertIn("fetch_error:RuntimeError", result[0].provenance)

    def test_registry_runs_external_verifier(self):
        contract = self.contract()
        profile = build_profile(contract)
        fetcher = FakeFetcher({"https://example.com/source": (200, "https://example.com/source", "text/html")})
        evidence = run_external_verifiers(contract, "https://example.com/source", profile, registry={"source_verification": SourceVerifier(fetcher=fetcher)})
        self.assertTrue(any(item.method == "external" and item.result == "pass" for item in evidence))

    def test_missing_configured_external_verifier_fails_closed(self):
        contract = self.contract()
        profile = build_profile(contract)
        evidence = run_external_verifiers(contract, "https://example.com/source", profile, registry={})
        self.assertEqual(len(evidence), 1)
        self.assertEqual(evidence[0].result, "fail")
        self.assertIn("verifier_missing", evidence[0].provenance)

    def test_external_failure_blocks_acceptance(self):
        profile = EvaluationProfile(dimensions=("goal_alignment",), minimum_scores={"goal_alignment": 0.70}, required_dimensions=("goal_alignment",), minimum_confidence=0.60, minimum_overall_score=0.75, max_revisions=1)
        result = EvaluationResult(Decision.ACCEPT, 0.95, 0.95, dimensions={"goal_alignment": DimensionResult(0.95, 0.95, "pass")}, evidence=(Evidence("external.source_verification", "external", "fail", 1.0, ("status:404",)),))
        self.assertEqual(decide(self.contract(), profile, result, revisions_used=0).decision, Decision.REVISE)

    def test_external_verifier_step_budget_fails_closed(self):
        contract = self.contract()
        profile = EvaluationProfile(dimensions=("correctness",), external_verification=("source_verification", "missing_external"), max_verification_steps=1)
        fetcher = FakeFetcher({"https://example.com/source": (200, "https://example.com/source", "text/html")})
        evidence = run_external_verifiers(contract, "https://example.com/source", profile, registry={"source_verification": SourceVerifier(fetcher=fetcher)})
        self.assertTrue(any(item.result == "fail" and "verification_budget_exhausted" in item.provenance for item in evidence))


if __name__ == "__main__": unittest.main()
