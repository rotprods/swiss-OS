from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet

LANES = frozenset({'ENTRY','HYBRID','CREATIVE','PORTAL','CROSS_LANE'})


@dataclass(frozen=True)
class NicheContract:
    niche_id: str
    slug: str
    adapter_version: str
    organization_types: FrozenSet[str]
    role_families: FrozenSet[str]
    source_scope_rules: FrozenSet[str]
    channel_types: FrozenSet[str]
    candidate_lanes: FrozenSet[str]

    def validate(self) -> None:
        if not self.niche_id.startswith('NICHE-') or len(self.niche_id) != 9:
            raise ValueError('niche_id must use NICHE-NNN')
        if not self.slug.strip() or not self.adapter_version.strip():
            raise ValueError('slug and adapter_version are required')
        if not self.organization_types:
            raise ValueError('at least one organization type is required')
        if not self.source_scope_rules:
            raise ValueError('source scope rules are required')
        unknown = set(self.candidate_lanes) - LANES
        if unknown:
            raise ValueError(f'unknown candidate lanes: {sorted(unknown)}')


HOTELS_V1 = NicheContract(
    niche_id='NICHE-001',
    slug='hotels',
    adapter_version='NICHE-CONTRACT-1.0',
    organization_types=frozenset({'HOTEL','HOSTEL','SERVICED_ACCOMMODATION','HOSPITALITY_GROUP'}),
    role_families=frozenset({'HOUSEKEEPING','KITCHEN_SUPPORT','SERVICE','PORTER_HOUSEMAN','FRONT_OFFICE','HOSPITALITY_OPERATIONS','CONTENT_DIGITAL'}),
    source_scope_rules=frozenset({'CURRENT_SNAPSHOT','HISTORICAL_INDEXED','RECONCILE_REQUIRED','UNKNOWN_SCOPE'}),
    channel_types=frozenset({'CAREERS_PORTAL','EMAIL','RECRUITER','JOB_BOARD','LINKEDIN','OTHER'}),
    candidate_lanes=frozenset({'ENTRY','HYBRID','CREATIVE','PORTAL'}),
)

HOTELS_V1.validate()
