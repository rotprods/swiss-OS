from __future__ import annotations

import argparse
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
import time
from typing import Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


class ProviderIdentityEnrichmentError(ValueError):
    pass


PROVIDER_HOST = "hotelleriesuisse.ch"
MAX_RESPONSE_BYTES = 2_000_000
SOCIAL_OR_INFRA_HOSTS = frozenset({
    "facebook.com", "instagram.com", "linkedin.com", "youtube.com",
    "google.com", "maps.google.com", "googleapis.com", PROVIDER_HOST,
})


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_json(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _text(value: object) -> str:
    return str(value or "").strip()


def _host(value: str) -> str:
    host = (urlsplit(value).hostname or "").lower().rstrip(".")
    return host[4:] if host.startswith("www.") else host


def _provider_url(value: str) -> bool:
    parsed = urlsplit(value)
    return parsed.scheme.lower() == "https" and _host(value) == PROVIDER_HOST


def _normalize_url(value: str, base: str) -> str:
    raw = urljoin(base, value.strip())
    parsed = urlsplit(raw)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        return ""
    path = re.sub(r"/{2,}", "/", parsed.path or "/")
    return f"{parsed.scheme.lower()}://{parsed.netloc.lower()}{path}"


class _ProviderOnlyRedirectHandler(HTTPRedirectHandler):
    """Allow redirects only inside the pinned provider HTTPS origin."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        if not _provider_url(newurl):
            raise ProviderIdentityEnrichmentError(f"provider redirect escaped trust boundary: {newurl}")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class _IdentityParser(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.links: set[str] = set()
        self._in_jsonld = False
        self._jsonld_chunks: list[str] = []
        self.jsonld: list[object] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        pairs = {k.lower(): (v or "") for k, v in attrs}
        if tag.lower() == "a" and pairs.get("href"):
            normalized = _normalize_url(pairs["href"], self.base_url)
            if normalized:
                self.links.add(normalized)
        if tag.lower() == "script" and pairs.get("type", "").lower() == "application/ld+json":
            self._in_jsonld = True
            self._jsonld_chunks = []

    def handle_data(self, data: str) -> None:
        if self._in_jsonld:
            self._jsonld_chunks.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() != "script" or not self._in_jsonld:
            return
        self._in_jsonld = False
        raw = "".join(self._jsonld_chunks).strip()
        if raw:
            try:
                self.jsonld.append(json.loads(raw))
            except json.JSONDecodeError:
                pass
        self._jsonld_chunks = []


def _walk_jsonld(node: object):
    if isinstance(node, Mapping):
        yield node
        for value in node.values():
            yield from _walk_jsonld(value)
    elif isinstance(node, list):
        for value in node:
            yield from _walk_jsonld(value)


def extract_identity_candidates(html: bytes, page_url: str) -> dict[str, object]:
    parser = _IdentityParser(page_url)
    parser.feed(html.decode("utf-8", errors="replace"))
    provider_host = _host(page_url)
    links: list[dict[str, str]] = []
    for url in sorted(parser.links):
        host = _host(url)
        if not host or host == provider_host or host.endswith("." + provider_host):
            continue
        if host in SOCIAL_OR_INFRA_HOSTS:
            continue
        links.append({"url": url, "host": host, "evidence_role": "EXTERNAL_LINK_CANDIDATE_ONLY"})

    structured: list[dict[str, object]] = []
    allowed_types = {"hotel", "lodgingbusiness", "organization", "localbusiness"}
    for root in parser.jsonld:
        for node in _walk_jsonld(root):
            kind = _text(node.get("@type"))
            if kind.lower() not in allowed_types:
                continue
            address = node.get("address")
            if isinstance(address, Mapping):
                structured_address = {
                    key: _text(address.get(key))
                    for key in ("streetAddress", "postalCode", "addressLocality", "addressRegion", "addressCountry")
                    if _text(address.get(key))
                }
            else:
                structured_address = {"raw": _text(address)} if _text(address) else {}
            structured.append({
                "type": kind,
                "name": _text(node.get("name")),
                "url": _text(node.get("url")),
                "telephone": _text(node.get("telephone")),
                "address": structured_address,
                "evidence_role": "STRUCTURED_PROVIDER_CANDIDATE_ONLY",
            })
    return {"external_link_candidates": links, "structured_identity_candidates": structured}


def _read_limited(response) -> bytes:  # noqa: ANN001
    body = response.read(MAX_RESPONSE_BYTES + 1)
    if len(body) > MAX_RESPONSE_BYTES:
        raise ProviderIdentityEnrichmentError("provider response exceeds size limit")
    return body


def _fetch(url: str, *, timeout: float = 30.0) -> tuple[int, str, bytes]:
    if not _provider_url(url):
        raise ProviderIdentityEnrichmentError("provider detail URL must be HTTPS hotelleriesuisse.ch")
    request = Request(
        url,
        headers={"User-Agent": "SWITZERLAND_JOB_OS-ProviderIdentityEnrichment/1.1 (+review-only)"},
    )
    opener = build_opener(_ProviderOnlyRedirectHandler())
    try:
        with opener.open(request, timeout=timeout) as response:
            final_url = response.geturl()
            if not _provider_url(final_url):
                raise ProviderIdentityEnrichmentError("final provider URL escaped trust boundary")
            return int(getattr(response, "status", 200)), final_url, _read_limited(response)
    except HTTPError as exc:
        final_url = exc.geturl()
        if not _provider_url(final_url):
            raise ProviderIdentityEnrichmentError("HTTP error URL escaped trust boundary") from exc
        return int(exc.code), final_url, _read_limited(exc)
    except URLError as exc:
        raise ProviderIdentityEnrichmentError(f"fetch failed: {exc}") from exc


def enrich_batch(batch: Mapping[str, object], *, timeout: float = 30.0, delay: float = 0.25) -> dict[str, object]:
    items = batch.get("items")
    if not isinstance(items, list) or not items:
        raise ProviderIdentityEnrichmentError("items must be a non-empty array")
    if batch.get("authority_advanced") not in (None, False) or batch.get("h_id_allocations") not in (None, 0):
        raise ProviderIdentityEnrichmentError("input batch violates authority invariants")
    if batch.get("outbound") not in (None, "CLOSED") or batch.get("send_allowed") not in (None, 0):
        raise ProviderIdentityEnrichmentError("input batch violates outbound invariants")

    results: list[dict[str, object]] = []
    seen: set[str] = set()
    for index, item in enumerate(items):
        if not isinstance(item, Mapping):
            raise ProviderIdentityEnrichmentError("every item must be an object")
        key = _text(item.get("source_record_key"))
        if not key or key in seen:
            raise ProviderIdentityEnrichmentError("source_record_key must be unique and non-empty")
        seen.add(key)
        if any(_text(item.get(field)) for field in ("canonical_hotel_id", "matched_hotel_id", "allocated_hotel_id")):
            raise ProviderIdentityEnrichmentError(f"target H-ID materialization forbidden in enrichment staging: {key}")
        url = _text(item.get("detail_url"))
        if not _provider_url(url):
            raise ProviderIdentityEnrichmentError(f"unsupported provider detail URL for {key}")
        if index and delay:
            time.sleep(delay)
        status, final_url, body = _fetch(url, timeout=timeout)
        extracted = extract_identity_candidates(body, final_url)
        results.append({
            "source_record_key": key,
            "source_name": _text(item.get("name")),
            "source_city": _text(item.get("city")),
            "detail_url": url,
            "http_status": status,
            "final_url": final_url,
            "response_sha256": _sha256_bytes(body),
            **extracted,
            "identity_decision": "NONE_REVIEW_ONLY",
            "terminal_mapping_allowed": False,
            "canonical_id_reservation_allowed": False,
            "authority_action": "NONE",
        })

    packet: dict[str, object] = {
        "schema_version": "PROVIDER-IDENTITY-ENRICHMENT-1.1",
        "project": "SWITZERLAND_JOB_OS",
        "snapshot_id": batch.get("snapshot_id"),
        "batch_id": batch.get("batch_id"),
        "items_count": len(items),
        "results_count": len(results),
        "results": results,
        "results_sha256": _sha256_json(results),
        "review_only": True,
        "identity_decision_allowed": False,
        "terminal_mapping_allowed": False,
        "canonical_id_reservation_allowed": False,
        "authority_advanced": False,
        "h_id_allocations": 0,
        "crm_universe_complete": False,
        "outbound": "CLOSED",
        "send_allowed": 0,
        "packet_sha256": "",
    }
    packet["packet_sha256"] = _sha256_json({k: v for k, v in packet.items() if k != "packet_sha256"})
    return packet


def validate_packet(packet: Mapping[str, object]) -> tuple[str, ...]:
    violations: list[str] = []
    if packet.get("schema_version") != "PROVIDER-IDENTITY-ENRICHMENT-1.1":
        violations.append("INVALID_SCHEMA_VERSION")
    if packet.get("review_only") is not True or packet.get("identity_decision_allowed") is not False:
        violations.append("REVIEW_ONLY_REQUIRED")
    for key in ("terminal_mapping_allowed", "canonical_id_reservation_allowed", "authority_advanced", "crm_universe_complete"):
        if packet.get(key) is not False:
            violations.append(f"INVALID_{key.upper()}")
    if packet.get("h_id_allocations") != 0 or packet.get("send_allowed") != 0 or packet.get("outbound") != "CLOSED":
        violations.append("SAFETY_INVARIANT_VIOLATION")
    results = packet.get("results")
    if not isinstance(results, list) or not all(isinstance(x, Mapping) for x in results):
        violations.append("RESULTS_INVALID")
        results = []
    if packet.get("results_count") != len(results) or packet.get("items_count") != len(results):
        violations.append("RESULT_COUNT_MISMATCH")
    for result in results:
        if any(_text(result.get(field)) for field in ("canonical_hotel_id", "matched_hotel_id", "allocated_hotel_id")):
            violations.append("RESULT_TARGET_HID_FORBIDDEN")
        if result.get("identity_decision") != "NONE_REVIEW_ONLY" or result.get("authority_action") != "NONE":
            violations.append("RESULT_DECISION_FORBIDDEN")
        if result.get("terminal_mapping_allowed") is not False or result.get("canonical_id_reservation_allowed") is not False:
            violations.append("RESULT_TERMINAL_SEMANTICS_FORBIDDEN")
    if packet.get("results_sha256") != _sha256_json(results):
        violations.append("RESULTS_SHA_MISMATCH")
    if packet.get("packet_sha256") != _sha256_json({k: v for k, v in packet.items() if k != "packet_sha256"}):
        violations.append("PACKET_SHA_MISMATCH")
    return tuple(dict.fromkeys(violations))


def _read(path: str) -> object:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write(path: str, payload: object) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m swiss_os.provider_identity_enrichment")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("batch")
    run.add_argument("--out", required=True)
    run.add_argument("--timeout", type=float, default=30.0)
    run.add_argument("--delay", type=float, default=0.25)
    val = sub.add_parser("validate")
    val.add_argument("path")
    args = parser.parse_args(argv)
    try:
        if args.command == "run":
            batch = _read(args.batch)
            if not isinstance(batch, Mapping):
                raise ProviderIdentityEnrichmentError("batch must be an object")
            packet = enrich_batch(batch, timeout=args.timeout, delay=args.delay)
            violations = validate_packet(packet)
            if violations:
                raise ProviderIdentityEnrichmentError(",".join(violations))
            _write(args.out, packet)
            print(json.dumps({"valid": True, "results_count": packet["results_count"], "packet_sha256": packet["packet_sha256"], "out": args.out}, sort_keys=True))
            return 0
        packet = _read(args.path)
        if not isinstance(packet, Mapping):
            raise ProviderIdentityEnrichmentError("packet must be an object")
        violations = validate_packet(packet)
        print(json.dumps({"valid": not violations, "violations": list(violations)}, sort_keys=True))
        return 0 if not violations else 2
    except (ProviderIdentityEnrichmentError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"valid": False, "error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
