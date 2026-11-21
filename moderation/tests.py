from django.test import TestCase

from accounts.models import User


class ModeratorAccessTests(TestCase):
    def setUp(self):
        self.moderator = User.objects.create_user(
            email='moderator@example.com',
            password='Password123',
            is_active=True,
            role=User.Role.MODERATOR,
        )
        self.student = User.objects.create_user(
            email='student@example.com',
            password='Password123',
            is_active=True,
        )

    def test_moderator_can_open_moderation_queue(self):
        self.client.force_login(self.moderator)
        response = self.client.get('/moderation/')
        self.assertEqual(response.status_code, 200)

    def test_student_cannot_open_moderation_queue(self):
        self.client.force_login(self.student)
        response = self.client.get('/moderation/')
        self.assertEqual(response.status_code, 403)

    def test_moderator_cannot_open_secretary_sanctions(self):
        self.client.force_login(self.moderator)
        response = self.client.get('/moderation/sanctions/')
        self.assertEqual(response.status_code, 403)
