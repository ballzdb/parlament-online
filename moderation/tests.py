from django.test import TestCase

from accounts.models import User
from ideas.models import Idea


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

    def test_moderator_can_approve_unassigned_idea(self):
        idea = Idea.objects.create(
            title='Корисна ініціатива',
            body='Опис пропозиції',
            author=self.student,
        )
        self.client.force_login(self.moderator)
        response = self.client.post(f'/moderation/idea/{idea.pk}/', {'action': 'approve'})
        self.assertEqual(response.status_code, 302)
        idea.refresh_from_db()
        self.assertEqual(idea.moderation_status, Idea.ModerationStatus.APPROVED)

    def test_user_can_have_multiple_roles_at_once(self):
        user = User.objects.create_user(
            email='student-moderator@example.com',
            password='Password123',
            is_active=True,
            role=User.Role.STUDENT,
            additional_roles=[User.Role.MODERATOR, User.Role.MEMBER],
        )
        self.assertTrue(user.is_student)
        self.assertTrue(user.is_moderator)
        self.assertTrue(user.is_member)
        self.client.force_login(user)
        self.assertEqual(self.client.get('/moderation/').status_code, 200)

    def test_moderator_cannot_open_secretary_sanctions(self):
        self.client.force_login(self.moderator)
        response = self.client.get('/moderation/sanctions/')
        self.assertEqual(response.status_code, 403)
