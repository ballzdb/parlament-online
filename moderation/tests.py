from django.test import TestCase

from accounts.models import User

from .models import ModerationEntry


class ModerationQueueAccessTests(TestCase):
    def test_queue_requires_login_and_secretary_role(self):
        response = self.client.get('/moderation/')
        self.assertRedirects(response, '/accounts/login/?next=/moderation/')

        student = User.objects.create_user(
            email='student@khul.ukr.education',
            password='Password123!',
            is_active=True,
        )
        self.client.force_login(student)
        self.assertEqual(self.client.get('/moderation/').status_code, 403)

        secretary = User.objects.create_user(
            email='secretary@khul.ukr.education',
            password='Password123!',
            role=User.Role.SECRETARY,
            is_active=True,
        )
        self.client.force_login(secretary)
        self.assertEqual(self.client.get('/moderation/').status_code, 200)

    def test_verdict_html_is_escaped(self):
        secretary = User.objects.create_user(
            email='secretary@khul.ukr.education',
            password='Password123!',
            role=User.Role.SECRETARY,
            is_active=True,
        )
        ModerationEntry.objects.create(
            target_type='idea',
            target_id=1,
            verdict={'message': '<script>alert(1)</script>'},
        )
        self.client.force_login(secretary)

        response = self.client.get('/moderation/')

        self.assertContains(response, '&lt;script&gt;alert(1)&lt;/script&gt;', html=False)
        self.assertNotContains(response, '<script>alert(1)</script>', html=False)
