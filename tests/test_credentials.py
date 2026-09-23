"""Offline checks for the visual Keychain configuration boundary."""
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'integrations' / 'jev_mac'))
import credentials


class CredentialTests(unittest.TestCase):
    def test_both_provider_keys_go_over_stdin_not_process_arguments(self):
        for provider, service in credentials.SERVICES.items():
            with self.subTest(provider=provider), patch.object(credentials.sys, 'platform', 'darwin'), \
                    patch('credentials.subprocess.run', return_value=Mock(returncode=0)) as run:
                credentials.save_key(provider, 'test-only-secret')
            args = run.call_args.args[0]
            self.assertEqual(args, [credentials.SECURITY, 'add-generic-password',
                                    '-a', 'default', '-s', service, '-U', '-w'])
            self.assertNotIn('test-only-secret', repr(args))
            self.assertEqual(run.call_args.kwargs['input'],
                             'test-only-secret\ntest-only-secret\n')
            self.assertTrue(run.call_args.kwargs['capture_output'])

    def test_invalid_provider_or_secret_never_reaches_keychain(self):
        with patch.object(credentials.sys, 'platform', 'darwin'), \
                patch('credentials.subprocess.run') as run:
            for provider, value in [('other', 'good'), ('deepseek', ''),
                                    ('jev', 'with space'), ('jev', 'line\nbreak'),
                                    ('deepseek', 'a' * 4097)]:
                with self.subTest(provider=provider, value_length=len(value)), self.assertRaises(ValueError):
                    credentials.save_key(provider, value)
            run.assert_not_called()

    def test_failure_message_does_not_echo_key_or_provider_output(self):
        with patch.object(credentials.sys, 'platform', 'darwin'), \
                patch('credentials.subprocess.run', return_value=Mock(
                    returncode=1, stderr='test-only-secret')):
            with self.assertRaises(ValueError) as result:
                credentials.save_key('deepseek', 'test-only-secret')
        self.assertNotIn('test-only-secret', str(result.exception))

    def test_delete_only_uses_project_service_and_absent_is_idempotent(self):
        with patch.object(credentials.sys, 'platform', 'darwin'), \
                patch('credentials.subprocess.run', return_value=Mock(returncode=44)) as run:
            credentials.delete_key('jev')
        self.assertEqual(run.call_args.args[0], [credentials.SECURITY, 'delete-generic-password',
                                                '-a', 'default', '-s', credentials.JEV_SERVICE])


if __name__ == '__main__':
    unittest.main()
