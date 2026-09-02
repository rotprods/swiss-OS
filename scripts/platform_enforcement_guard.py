#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

CONTRACT_PATH = Path('docs/state/platform/GRAPH_V2_PLATFORM_ENFORCEMENT_REQUIREMENT.json')
ALLOWED_PENDING = {'REQUIRED_NOT_YET_PLATFORM_ENFORCED', 'DEGRADED_EXTERNAL'}
ENFORCED = 'ENFORCED'


def _get_json(url: str, token: str | None = None) -> dict[str, Any]:
    headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'swiss-os-platform-guard'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
        headers['X-GitHub-Api-Version'] = '2022-11-28'
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as response:
        return json.load(response)


def evaluate(contract: dict[str, Any], branch: dict[str, Any], protection: dict[str, Any] | None) -> tuple[bool, dict[str, Any]]:
    required = contract.get('required_controls') or {}
    status = contract.get('status')
    protected = bool(branch.get('protected'))

    checks: dict[str, Any] = {
        'branch_protected': protected,
        'pull_request_required': False,
        'repo_guard_required': False,
        'branch_up_to_date_required': False,
        'force_push_blocked': False,
        'deletion_blocked': False,
        'bypass_absent': False,
    }

    if protection:
        pr = protection.get('required_pull_request_reviews')
        checks['pull_request_required'] = pr is not None
        status_checks = protection.get('required_status_checks') or {}
        contexts = set(status_checks.get('contexts') or [])
        for item in status_checks.get('checks') or []:
            if isinstance(item, dict) and item.get('context'):
                contexts.add(str(item['context']))
        checks['repo_guard_required'] = 'repo-guard' in contexts
        checks['branch_up_to_date_required'] = bool(status_checks.get('strict'))
        checks['force_push_blocked'] = not bool((protection.get('allow_force_pushes') or {}).get('enabled'))
        checks['deletion_blocked'] = not bool((protection.get('allow_deletions') or {}).get('enabled'))
        # Classic branch protection exposes bypass allowances in review restrictions inconsistently.
        # Treat absence of an explicit bypass allowance as the strongest verifiable signal here.
        checks['bypass_absent'] = not bool((protection.get('required_pull_request_reviews') or {}).get('bypass_pull_request_allowances'))

    exact = (
        protected
        and (not required.get('pull_request_required') or checks['pull_request_required'])
        and ('repo-guard' not in set(required.get('required_status_checks') or []) or checks['repo_guard_required'])
        and (not required.get('require_branch_up_to_date') or checks['branch_up_to_date_required'])
        and (not required.get('block_force_push') or checks['force_push_blocked'])
        and (not required.get('block_deletion') or checks['deletion_blocked'])
        and (required.get('allow_bypass') is not False or checks['bypass_absent'])
    )

    violations: list[str] = []
    if status == ENFORCED and not exact:
        violations.append('FALSE_PLATFORM_ENFORCEMENT_CLAIM')
    elif status not in ALLOWED_PENDING | {ENFORCED}:
        violations.append(f'UNKNOWN_PLATFORM_ENFORCEMENT_STATUS:{status}')

    receipt = {
        'schema_version': 'GRAPH-V2-PLATFORM-READBACK-1.0',
        'project_id': contract.get('project_id'),
        'contract_status': status,
        'platform_enforced': exact,
        'production_authority_allowed': exact,
        'checks': checks,
        'violations': violations,
    }
    return not violations, receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--contract', default=str(CONTRACT_PATH))
    parser.add_argument('--branch-json', help='Offline fixture/readback JSON for deterministic testing')
    parser.add_argument('--protection-json', help='Offline protection detail fixture JSON')
    parser.add_argument('--receipt', default=None)
    args = parser.parse_args()

    contract = json.loads(Path(args.contract).read_text())
    if args.branch_json:
        branch = json.loads(Path(args.branch_json).read_text())
        protection = json.loads(Path(args.protection_json).read_text()) if args.protection_json else None
    else:
        repo = os.environ.get('GITHUB_REPOSITORY', 'rotprods/swiss-OS')
        token = os.environ.get('GITHUB_TOKEN')
        branch = _get_json(f'https://api.github.com/repos/{repo}/branches/main', token)
        protection = None
        if branch.get('protected'):
            try:
                protection = _get_json(f'https://api.github.com/repos/{repo}/branches/main/protection', token)
            except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
                protection = None

    ok, receipt = evaluate(contract, branch, protection)
    text = json.dumps(receipt, sort_keys=True)
    print(text)
    if args.receipt:
        Path(args.receipt).parent.mkdir(parents=True, exist_ok=True)
        Path(args.receipt).write_text(text + '\n')
    if not receipt['platform_enforced']:
        print('PLATFORM_ENFORCEMENT_BLOCKED: production authority remains false', file=sys.stderr)
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
