import unittest

from scripts.platform_enforcement_guard import evaluate


BASE_CONTRACT = {
    'project_id': 'SWITZERLAND_JOB_OS',
    'status': 'REQUIRED_NOT_YET_PLATFORM_ENFORCED',
    'required_controls': {
        'pull_request_required': True,
        'required_status_checks': ['repo-guard'],
        'block_force_push': True,
        'block_deletion': True,
        'require_branch_up_to_date': True,
        'allow_bypass': False,
    },
}


class PlatformEnforcementGuardTests(unittest.TestCase):
    def test_unprotected_branch_is_explicit_blocker_not_false_failure(self):
        ok, receipt = evaluate(BASE_CONTRACT, {'protected': False}, None)
        self.assertTrue(ok)
        self.assertFalse(receipt['platform_enforced'])
        self.assertFalse(receipt['production_authority_allowed'])
        self.assertEqual(receipt['violations'], [])

    def test_false_enforced_claim_fails_closed(self):
        contract = {**BASE_CONTRACT, 'status': 'ENFORCED'}
        ok, receipt = evaluate(contract, {'protected': False}, None)
        self.assertFalse(ok)
        self.assertIn('FALSE_PLATFORM_ENFORCEMENT_CLAIM', receipt['violations'])

    def test_exact_protection_can_be_enforced(self):
        contract = {**BASE_CONTRACT, 'status': 'ENFORCED'}
        protection = {
            'required_pull_request_reviews': {},
            'required_status_checks': {'strict': True, 'contexts': ['repo-guard']},
            'allow_force_pushes': {'enabled': False},
            'allow_deletions': {'enabled': False},
        }
        ok, receipt = evaluate(contract, {'protected': True}, protection)
        self.assertTrue(ok)
        self.assertTrue(receipt['platform_enforced'])
        self.assertTrue(receipt['production_authority_allowed'])

    def test_protected_without_readback_is_not_enough(self):
        contract = {**BASE_CONTRACT, 'status': 'ENFORCED'}
        ok, receipt = evaluate(contract, {'protected': True}, None)
        self.assertFalse(ok)
        self.assertFalse(receipt['platform_enforced'])


if __name__ == '__main__':
    unittest.main()
