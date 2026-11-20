from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from ideas.models import Event, Idea


class IdeaModerationWorkflowTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            email='student@khul.ukr.education', password='Password123',
            display_name='Учень', is_active=True,
        )
        self.secretary = User.objects.create_user(
            email='secretary@khul.ukr.education', password='Password123',
            display_name='Секретар', role=User.Role.SECRETARY, is_active=True,
        )
        self.moderator = User.objects.create_user(
            email='moderator@khul.ukr.education', password='Password123',
            display_name='Модератор', role=User.Role.COMMISSION_HEAD, is_active=True,
        )

    def test_new_idea_waits_for_moderation_and_is_hidden_from_public(self):
        idea = Idea.objects.create(title='Нова ініціатива', body='Опис', author=self.student)
        self.assertEqual(idea.moderation_status, Idea.ModerationStatus.PENDING)
        self.assertNotContains(self.client.get('/ideas/'), 'Нова ініціатива')
        self.client.force_login(self.student)
        self.assertContains(self.client.get('/ideas/'), 'Нова ініціатива')

    def test_secretary_assigns_and_moderator_approves(self):
        idea = Idea.objects.create(title='Ініціатива', body='Опис', author=self.student)
        self.client.force_login(self.secretary)
        response = self.client.post(f'/moderation/idea/{idea.pk}/', {
            'action': 'assign', 'moderator': self.moderator.pk,
        })
        self.assertEqual(response.status_code, 302)
        idea.refresh_from_db()
        self.assertEqual(idea.assigned_moderator, self.moderator)

        self.client.force_login(self.moderator)
        response = self.client.post(f'/moderation/idea/{idea.pk}/', {'action': 'approve'})
        self.assertEqual(response.status_code, 302)
        idea.refresh_from_db()
        self.assertEqual(idea.moderation_status, Idea.ModerationStatus.APPROVED)
        self.assertEqual(idea.moderated_by, self.moderator)
        self.assertIsNotNone(idea.moderated_at)

    def test_unassigned_moderator_cannot_approve(self):
        idea = Idea.objects.create(title='Ініціатива', body='Опис', author=self.student)
        other = User.objects.create_user(
            email='other@khul.ukr.education', password='Password123',
            role=User.Role.COMMISSION_HEAD, is_active=True,
        )
        self.client.force_login(other)
        self.assertEqual(self.client.post(f'/moderation/idea/{idea.pk}/', {'action': 'approve'}).status_code, 403)

    def test_rejection_requires_reason(self):
        idea = Idea.objects.create(title='Ініціатива', body='Опис', author=self.student, assigned_moderator=self.moderator)
        self.client.force_login(self.moderator)
        self.client.post(f'/moderation/idea/{idea.pk}/', {'action': 'reject', 'reason': ''})
        idea.refresh_from_db()
        self.assertEqual(idea.moderation_status, Idea.ModerationStatus.PENDING)
        self.client.post(f'/moderation/idea/{idea.pk}/', {'action': 'reject', 'reason': 'Потрібно уточнити пропозицію'})
        idea.refresh_from_db()
        self.assertEqual(idea.moderation_status, Idea.ModerationStatus.REJECTED)
        self.assertEqual(idea.moderation_reason, 'Потрібно уточнити пропозицію')


class EventArchiveTests(TestCase):
    def setUp(self):
        self.member = User.objects.create_user(
            email='member@khul.ukr.education', password='Password123',
            role=User.Role.MEMBER, is_active=True,
        )
        self.event = Event.objects.create(
            title='Благодійний ярмарок',
            description='Шкільна благодійна подія',
            starts_at=timezone.now() - timedelta(days=1),
            organiser='Учнівський парламент',
            participating_classes='8-А, 9-Б',
            participant_count=42,
            outcome='Зібрані кошти передано на благодійність.',
            created_by=self.member,
        )

    def test_past_event_appears_in_archive_with_report(self):
        response = self.client.get('/ideas/events/')
        self.assertContains(response, 'Благодійний ярмарок')
        self.assertContains(response, 'Учнівський парламент')
        self.assertContains(response, '8-А, 9-Б')
        self.assertContains(response, '42')
        self.assertContains(response, 'Зібрані кошти')

    def test_event_detail_and_edit_permissions(self):
        response = self.client.get(f'/ideas/events/{self.event.pk}/')
        self.assertContains(response, 'Благодійний ярмарок')
        self.assertEqual(self.client.get(f'/ideas/events/{self.event.pk}/edit/').status_code, 302)
        self.client.force_login(self.member)
        self.assertEqual(self.client.get(f'/ideas/events/{self.event.pk}/edit/').status_code, 200)
