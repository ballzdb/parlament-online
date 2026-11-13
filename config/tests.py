from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from django.test import SimpleTestCase


class SettingsSecurityTests(SimpleTestCase):
    def run_settings_import(self, environment):
        project_root = Path(__file__).resolve().parent.parent
        code = (
            'import dotenv; '
            'dotenv.load_dotenv = lambda *args, **kwargs: None; '
            'import config.settings; '
            'print("DEBUG =", config.settings.DEBUG)'
        )
        return subprocess.run(
            [sys.executable, '-c', code],
            cwd=project_root,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_debug_defaults_to_false_and_missing_secret_key_is_fatal(self):
        environment = os.environ.copy()
        environment.pop('DEBUG', None)
        environment['SECRET_KEY'] = 'test-only-secret-key'
        debug_result = self.run_settings_import(environment)
        self.assertEqual(debug_result.returncode, 0, debug_result.stderr)
        self.assertIn('DEBUG = False', debug_result.stdout)

        environment['DEBUG'] = 'False'
        environment.pop('SECRET_KEY')
        missing_key_result = self.run_settings_import(environment)
        self.assertNotEqual(missing_key_result.returncode, 0)
        self.assertIn('SECRET_KEY', missing_key_result.stderr)
