from django.core.management import call_command
from django.test import Client, TestCase

from .models import User


class AccountFlowTests(TestCase):
    def test_registration_creates_inactive_user(self):
        response = self.client.post(
            '/accounts/register/',
            {
                'email': 'student@example.com',
                'display_name': 'Студент',
                'grade': 9,
                'class_letter': 'А',
                'password': 'Password123',
                'password_confirm': 'Password123',
            },
        )
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(email='student@example.com')
        self.assertFalse(user.is_active)

    def test_create_secretary_command(self):
        call_command('create_secretary', email='secretary@example.com', password='Secret123!')
        user = User.objects.get(email='secretary@example.com')
        self.assertTrue(user.is_active)
        self.assertEqual(user.role, User.Role.SECRETARY)
