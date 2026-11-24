from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from accounts.models import AuditLog, User
from ideas.models import Idea
from moderation.models import ModerationEntry


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

    def test_moderator_can_delete_pending_or_published_idea(self):
        self.client.force_login(self.moderator)
        for moderation_status in (
            Idea.ModerationStatus.PENDING,
            Idea.ModerationStatus.APPROVED,
        ):
            idea = Idea.objects.create(
                title=f'Ідея для видалення {moderation_status}',
                body='Тестовий опис',
                author=self.student,
                moderation_status=moderation_status,
            )
            response = self.client.post(f'/moderation/idea/{idea.pk}/delete/')
            self.assertEqual(response.status_code, 302)
            self.assertFalse(Idea.objects.filter(pk=idea.pk).exists())
            self.assertTrue(AuditLog.objects.filter(
                action='idea_deleted_by_moderator',
                details__contains=f'Idea #{idea.pk}',
            ).exists())
            self.assertTrue(ModerationEntry.objects.filter(
                target_type='idea',
                target_id=idea.pk,
                verdict__action='deleted',
            ).exists())

    def test_student_cannot_delete_idea(self):
        idea = Idea.objects.create(
            title='Чужа ідея',
            body='Опис',
            author=self.student,
            moderation_status=Idea.ModerationStatus.APPROVED,
        )
        self.client.force_login(self.student)
        response = self.client.post(f'/moderation/idea/{idea.pk}/delete/')
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Idea.objects.filter(pk=idea.pk).exists())

    def test_moderator_can_open_sanctions_and_temporarily_block_student(self):
        self.client.force_login(self.moderator)
        response = self.client.get('/moderation/sanctions/')
        self.assertEqual(response.status_code, 200)

        until = timezone.localtime(timezone.now() + timedelta(days=2))
        response = self.client.post('/moderation/sanctions/', {
            'user': self.student.pk,
            'restricted_until': until.strftime('%Y-%m-%dT%H:%M'),
            'reason': 'Повторне порушення правил платформи.',
        })
        self.assertEqual(response.status_code, 302)
        self.student.refresh_from_db()
        self.assertTrue(self.student.is_temporarily_restricted)
        self.assertEqual(self.student.restricted_by, self.moderator)
        self.assertTrue(AuditLog.objects.filter(
            action='student_temporarily_restricted',
            user=self.moderator,
        ).exists())

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

    def test_moderator_cannot_open_secretary_role_management(self):
        self.client.force_login(self.moderator)
        response = self.client.get('/accounts/roles/')
        self.assertEqual(response.status_code, 403)
