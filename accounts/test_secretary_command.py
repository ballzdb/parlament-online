from unittest.mock import patch

from django.core.management import call_command, CommandError
from django.test import TestCase

from .models import User


class CreateSecretaryCommandTests(TestCase):
    @patch('accounts.management.commands.create_secretary.getpass', return_value='StrongPass123!')
    def test_password_is_prompted_and_saved(self, prompt):
        call_command('create_secretary', email='secretary@example.com')

        user = User.objects.get(email='secretary@example.com')
        self.assertTrue(user.check_password('StrongPass123!'))
        prompt.assert_called_once()

    def test_password_shorter_than_ten_characters_is_rejected(self):
        with self.assertRaises(CommandError):
            call_command('create_secretary', email='secretary@example.com', password='short')

        self.assertFalse(User.objects.filter(email='secretary@example.com').exists())
