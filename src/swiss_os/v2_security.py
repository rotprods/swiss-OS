from __future__ import annotations

from dataclasses import dataclass
import ipaddress
from pathlib import PurePosixPath
import re
from typing import Any, Mapping
from urllib.parse import urlsplit

from .v2_kernel import ContractError, redact_secrets


class SecurityBoundaryError(ContractError):
    """Raised when untrusted input crosses a forbidden V2 trust boundary."""


_ALLOWED_SCHEMES = frozenset({"https"})
_FORBIDDEN_HOSTS = frozenset({"localhost", "localhost.localdomain"})
_CREDENTIAL_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\b(?:sk|pk)-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
)
_PROMPT_INJECTION_PATTERNS = (
    re.compile(r"\bignore (?:all |any )?(?:previous|prior|system) instructions\b", re.I),
    re.compile(r"\breveal (?:the )?(?:system prompt|hidden instructions|credentials|secrets)\b", re.I),
    re.compile(r"\bact as (?:the )?(?:system|developer|administrator|root)\b", re.I),
    re.compile(r"\bexecute (?:this )?(?:shell|terminal|command)\b", re.I),
)


@dataclass(frozen=True)
class UntrustedTextAssessment:
    safe_as_data: bool
    instruction_like_markers: tuple[str, ...]
    credential_markers: tuple[str, ...]
    authority_granted: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "safe_as_data": self.safe_as_data,
            "instruction_like_markers": list(self.instruction_like_markers),
            "credential_markers": list(self.credential_markers),
            "authority_granted": self.authority_granted,
        }


def validate_public_https_url(value: object, *, allowed_hosts: tuple[str, ...] = ()) -> str:
    """Validate a provider URL without performing DNS or network access.

    The caller must still enforce response-size/content/time limits. DNS rebinding
    remains a transport-layer responsibility because this pure function does not
    resolve names.
    """

    if not isinstance(value, str) or not value.strip():
        raise SecurityBoundaryError("URL must be a non-empty string")
    if any(ch in value for ch in ("\x00", "\r", "\n", "\t")):
        raise SecurityBoundaryError("URL contains control characters")
    parsed = urlsplit(value.strip())
    if parsed.scheme.lower() not in _ALLOWED_SCHEMES:
        raise SecurityBoundaryError("only HTTPS provider URLs are allowed")
    if parsed.username is not None or parsed.password is not None:
        raise SecurityBoundaryError("credential-bearing URLs are forbidden")
    if not parsed.hostname:
        raise SecurityBoundaryError("URL hostname is required")
    host = parsed.hostname.rstrip(".").lower()
    if host in _FORBIDDEN_HOSTS or host.endswith(".localhost") or host.endswith(".local"):
        raise SecurityBoundaryError("local hostnames are forbidden")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address is not None and (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_multicast
        or address.is_reserved
        or address.is_unspecified
    ):
        raise SecurityBoundaryError("non-public IP address is forbidden")
    normalized_allowed = {item.rstrip(".").lower() for item in allowed_hosts}
    if normalized_allowed and host not in normalized_allowed:
        raise SecurityBoundaryError(f"host is not allow-listed: {host}")
    if parsed.fragment:
        raise SecurityBoundaryError("fragments are forbidden in provider fetch URLs")
    return parsed.geturl()


def validate_artifact_relative_path(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SecurityBoundaryError("artifact path must be a non-empty string")
    if len(value) > 240:
        raise SecurityBoundaryError("artifact path is too long")
    if "\x00" in value or "\\" in value:
        raise SecurityBoundaryError("artifact path contains forbidden characters")
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts:
        raise SecurityBoundaryError("artifact path must be relative")
    if any(part in {"", ".", ".."} for part in path.parts):
        raise SecurityBoundaryError("artifact path traversal is forbidden")
    if not re.fullmatch(r"[A-Za-z0-9._/-]+", value):
        raise SecurityBoundaryError("artifact path contains unsupported characters")
    return path.as_posix()


def assess_untrusted_text(value: object) -> UntrustedTextAssessment:
    if not isinstance(value, str):
        raise SecurityBoundaryError("untrusted text must be a string")
    injection = tuple(
        sorted({pattern.pattern for pattern in _PROMPT_INJECTION_PATTERNS if pattern.search(value)})
    )
    credentials = tuple(
        sorted({pattern.pattern for pattern in _CREDENTIAL_PATTERNS if pattern.search(value)})
    )
    return UntrustedTextAssessment(
        safe_as_data=not credentials,
        instruction_like_markers=injection,
        credential_markers=credentials,
        authority_granted=False,
    )


def sanitize_public_payload(value: Any) -> Any:
    """Redact credentials and preserve provider instructions strictly as data."""

    redacted = redact_secrets(value)

    def walk(item: Any) -> Any:
        if isinstance(item, Mapping):
            return {str(key): walk(child) for key, child in item.items()}
        if isinstance(item, list):
            return [walk(child) for child in item]
        if isinstance(item, tuple):
            return tuple(walk(child) for child in item)
        if isinstance(item, str):
            assessment = assess_untrusted_text(item)
            if assessment.credential_markers:
                return "[REDACTED]"
            return item
        if item is None or isinstance(item, (bool, int, float)):
            return item
        raise SecurityBoundaryError(f"unsupported public payload type: {type(item).__name__}")

    return walk(redacted)
