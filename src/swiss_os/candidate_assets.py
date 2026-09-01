from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

ALLOWED_ASSET_TYPES = frozenset({"CV_MASTER", "CV_ENTRY", "CV_HYBRID", "CV_CREATIVE", "PORTFOLIO", "CASE_STUDY"})
ALLOWED_ASSET_STATES = frozenset({"DRAFT", "QA_PENDING", "APPROVED", "DEPRECATED"})


@dataclass(frozen=True)
class AssetManifest:
    asset_id: str
    asset_type: str
    version: str
    state: str
    private_storage_ref: str
    claim_ids: tuple[str, ...]
    content_sha256: str | None = None

    def validate(self) -> None:
        if self.asset_type not in ALLOWED_ASSET_TYPES:
            raise ValueError(f"invalid asset type: {self.asset_type}")
        if self.state not in ALLOWED_ASSET_STATES:
            raise ValueError(f"invalid asset state: {self.state}")
        if not self.asset_id.strip() or not self.version.strip():
            raise ValueError("asset_id and version are required")
        if not self.private_storage_ref.strip():
            raise ValueError("private storage reference required")
        if self.state == "APPROVED" and self.content_sha256 is None:
            raise ValueError("approved asset requires content_sha256")
        if self.content_sha256 is not None:
            if len(self.content_sha256) != 64 or any(c not in "0123456789abcdef" for c in self.content_sha256.lower()):
                raise ValueError("content_sha256 must be a hex SHA-256")

    @property
    def approved(self) -> bool:
        return self.state == "APPROVED"

    def public_safe_receipt(self) -> dict[str, object]:
        self.validate()
        # Never expose the private storage reference in a public receipt.
        return {
            "asset_id": self.asset_id,
            "asset_type": self.asset_type,
            "version": self.version,
            "state": self.state,
            "claim_count": len(self.claim_ids),
            "content_sha256": self.content_sha256,
            "private_storage_present": True,
        }


def sha256_text(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def canonical_manifest_hash(manifest: AssetManifest) -> str:
    receipt = manifest.public_safe_receipt()
    raw = json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()
