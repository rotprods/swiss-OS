from __future__ import annotations

"""Compile a PCF-finalized HSLCA capture into canonical MEMBER-DIRECTORY-1.0.

The HSLCA/PCF stack historically emitted an intermediate compatibility manifest.
D2C/CMI consumes the stricter transfer-valid manifest implemented by
``swiss_os.member_directory``. This adapter closes that representation gap while
remaining strictly pre-authority: it never allocates H-IDs, mutates canonical
state, opens outbound, or infers source completeness beyond the finalized capture.
"""

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Mapping

from .member_directory import (
    DirectoryManifestConfig,
    DirectoryRecord,
    build_member_directory_manifest,
    validate_member_directory_manifest,
)


class HSLCA transfer_manifestError(ValueError):
    pass
