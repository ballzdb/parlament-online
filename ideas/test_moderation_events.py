from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from ideas.models import Event, Idea, IdeaVote
from moderation.models import ModerationEntry


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
        self.assertEqual(ModerationEntry.objects.filter(target_type='idea', target_id=idea.pk).count(), 2)
        self.client.force_login(self.student)
        detail = self.client.get(f'/ideas/{idea.pk}/')
        self.assertContains(detail, 'Історія модерації')
        self.assertContains(detail, 'Призначено модератора')
        self.assertContains(detail, 'Ідею допущено до публікації')

    def test_moderation_queue_renders_ideas_without_assigned_moderator(self):
        Idea.objects.create(title='Ідея без модератора', body='Опис', author=self.student)
        self.client.force_login(self.secretary)
        response = self.client.get('/moderation/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ідея без модератора')
        self.assertContains(response, 'Не призначено')

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


class TemporaryRestrictionTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            email='restricted@khul.ukr.education', password='Password123',
            display_name='Учень', is_active=True,
            restricted_until=timezone.now() + timedelta(days=2),
            restriction_reason='Повторний спам у пропозиціях.',
        )
        self.member = User.objects.create_user(
            email='member@khul.ukr.education', password='Password123',
            role=User.Role.MEMBER, is_active=True,
        )
        self.secretary = User.objects.create_user(
            email='sanctions-secretary@khul.ukr.education', password='Password123',
            role=User.Role.SECRETARY, is_active=True,
        )
        self.idea = Idea.objects.create(
            title='Опублікована ідея', body='Опис',
            author=self.member,
            moderation_status=Idea.ModerationStatus.APPROVED,
        )

    def test_restricted_student_cannot_submit_idea(self):
        self.client.force_login(self.student)
        response = self.client.post('/ideas/create/', {
            'title': 'Нова ідея',
            'body': 'Хочу запропонувати нову ініціативу.',
            'commission': '',
        })
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Idea.objects.filter(title='Нова ідея').exists())

    def test_restricted_student_cannot_vote(self):
        self.client.force_login(self.student)
        response = self.client.post(f'/ideas/{self.idea.pk}/', {'vote': '1'})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(IdeaVote.objects.filter(idea=self.idea, user=self.student).exists())

    def test_sanctions_page_renders_restriction_without_actor(self):
        self.client.force_login(self.secretary)
        response = self.client.get('/moderation/sanctions/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Не зазначено')

    def test_restriction_does_not_hide_public_ideas(self):
        self.client.force_login(self.student)
        self.assertContains(self.client.get('/ideas/'), 'Опублікована ідея')
