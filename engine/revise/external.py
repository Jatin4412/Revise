from __future__ import annotations

import ipaddress
import re
import socket
from dataclasses import dataclass
from typing import Protocol
from urllib import error, request
from urllib.parse import urljoin, urlparse

from .models import Evidence, EvaluationProfile, TaskContract

_URL_RE = re.compile(r"https?://[^\s<>()\[\]{}\"']+")


class SourceFetcher(Protocol):
    def fetch(self, url: str, *, timeout: float, max_bytes: int) -> tuple[int, str, str]: ...


class _SafeRedirectHandler(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        target = urljoin(req.full_url, newurl)
        _validate_public_url(target)
        return super().redirect_request(req, fp, code, msg, headers, target)


@dataclass(frozen=True)
class HttpSourceFetcher:
    user_agent: str = "ReviseEngine/0.1"

    def fetch(self, url: str, *, timeout: float, max_bytes: int) -> tuple[int, str, str]:
        parsed = _validate_public_url(url)
        req = request.Request(url, headers={"User-Agent": self.user_agent}, method="GET")
        opener = request.build_opener(_SafeRedirectHandler())
        try:
            with opener.open(req, timeout=timeout) as response:
                response.read(max_bytes)
                final_url = response.geturl()
                _validate_public_url(final_url)
                return int(response.status), final_url, response.headers.get("Content-Type", "")
        except error.HTTPError as exc:
            return int(exc.code), exc.geturl() or parsed.geturl(), exc.headers.get("Content-Type", "") if exc.headers else ""
        except error.URLError as exc:
            raise RuntimeError(str(exc.reason)) from exc


@dataclass(frozen=True)
class SourceVerifier:
    """Verify cited HTTP(S) source reachability; never judge claim truth."""
    name: str = "source_verification"
    fetcher: SourceFetcher = HttpSourceFetcher()
    timeout: float = 5.0
    max_bytes: int = 65536
    max_sources: int = 4

    def verify(self, contract: TaskContract, response: str, profile: EvaluationProfile, *, max_sources: int | None = None) -> tuple[Evidence, ...]:
        del profile
        urls = _extract_urls(response)
        if not urls:
            if _requires_citations(contract):
                return (Evidence("external.source_verification", "external", "fail", 1.0, ("citation_required", "no_http_sources_found")),)
            return ()
        limit = self.max_sources if max_sources is None else max(0, min(self.max_sources, max_sources))
        evidence: list[Evidence] = []
        for url in urls[:limit]:
            try:
                status, final_url, content_type = self.fetcher.fetch(url, timeout=self.timeout, max_bytes=self.max_bytes)
            except (RuntimeError, ValueError, OSError, socket.gaierror) as exc:
                evidence.append(Evidence("external.source_verification", "external", "fail", 1.0, (f"url:{url}", f"fetch_error:{type(exc).__name__}")))
                continue
            result = "pass" if 200 <= status < 400 else "fail"
            provenance = (f"url:{url}", f"status:{status}")
            if final_url != url: provenance += (f"final_url:{final_url}",)
            if content_type: provenance += (f"content_type:{content_type.split(';', 1)[0].strip().lower()}",)
            evidence.append(Evidence("external.source_verification", "external", result, 1.0, provenance))
        if len(urls) > limit:
            evidence.append(Evidence("external.source_verification", "external", "fail", 1.0, ("source_limit_exhausted", f"sources_available:{len(urls)}", f"sources_checked:{limit}")))
        return tuple(evidence)


def run_external_verifiers(contract: TaskContract, response: str, profile: EvaluationProfile, *, registry: dict[str, SourceVerifier] | None = None, max_steps: int | None = None) -> tuple[Evidence, ...]:
    selected = {"source_verification": SourceVerifier()} if registry is None else registry
    names = tuple(profile.external_verification)
    budget = profile.max_verification_steps if max_steps is None else max(0, max_steps)
    evidence: list[Evidence] = []
    for index, name in enumerate(names):
        if index >= budget:
            evidence.append(Evidence(f"external.{name}", "external", "fail", 1.0, ("verification_budget_exhausted",)))
            continue
        verifier = selected.get(name)
        if verifier is None:
            evidence.append(Evidence(f"external.{name}", "external", "fail", 1.0, ("verifier_missing",)))
            continue
        evidence.extend(verifier.verify(contract, response, profile))
    return tuple(evidence)


def _extract_urls(response: str) -> tuple[str, ...]:
    # Preserve first-seen URL order and deduplicate repeated citations.
    found: list[str] = []
    for raw in _URL_RE.findall(response):
        url = raw.rstrip(".,;:!?)]}")
        if url not in found: found.append(url)
    return tuple(found)


def _requires_citations(contract: TaskContract) -> bool:
    text = " ".join((contract.goal, *contract.requirements, *contract.verification_requirements)).lower()
    return any(term in text for term in ("citation", "cite sources", "sources", "source verification"))


def _validate_public_url(url: str):
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("only public HTTP(S) URLs without embedded credentials are supported")
    try:
        addresses = {item[4][0] for item in socket.getaddrinfo(parsed.hostname, None, type=socket.SOCK_STREAM)}
    except socket.gaierror as exc:
        raise ValueError("source hostname could not be resolved") from exc
    if not addresses: raise ValueError("source hostname has no resolved address")
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if any((ip.is_private, ip.is_loopback, ip.is_link_local, ip.is_reserved, ip.is_multicast, ip.is_unspecified)):
            raise ValueError("private or otherwise non-public source address is not allowed")
    return parsed
