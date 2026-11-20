from datetime import timedelta

from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from accounts.models import Commission, User
from ideas.models import Event, Idea, IdeaVote


class IdeaVoteTests(TestCase):
    def setUp(self):
        self.commission, _ = Commission.objects.get_or_create(slug='navchannia', defaults={'name': 'Навчання'})
        self.user = User.objects.create_user(email='user@example.com', password='Password123', display_name='Користувач', is_active=True)
        self.idea = Idea.objects.create(
            title='Відкрити асинхронний клуб',
            body='Мета — зібрати учнів...',
            author=self.user,
            commission=self.commission,
            moderation_status=Idea.ModerationStatus.APPROVED,
        )

    def test_vote_uniqueness(self):
        IdeaVote.objects.create(idea=self.idea, user=self.user)
        with self.assertRaises(IntegrityError):
            IdeaVote.objects.create(idea=self.idea, user=self.user)

    def test_member_can_change_idea_status(self):
        member = User.objects.create_user(email='member@example.com', password='Password123', display_name='Член', role=User.Role.MEMBER, is_active=True)
        self.client.force_login(member)
        response = self.client.post(
            f'/ideas/{self.idea.pk}/',
            {'status': Idea.Status.IN_PROGRESS, 'status_reason': 'Має бути в роботі', 'completion_report': 'Розпочато роботу.'},
        )
        self.assertEqual(response.status_code, 302)
        self.idea.refresh_from_db()
        self.assertEqual(self.idea.status, Idea.Status.IN_PROGRESS)



class ParliamentEventTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            email='student@khul.ukr.education',
            password='Password123',
            display_name='Учень',
            is_active=True,
        )
        self.member = User.objects.create_user(
            email='member@khul.ukr.education',
            password='Password123',
            display_name='Парламентарій',
            role=User.Role.MEMBER,
            is_active=True,
        )
        self.idea = Idea.objects.create(
            title='Шкільний кіновечір',
            body='Організувати кіновечір для учнів.',
            author=self.student,
            moderation_status=Idea.ModerationStatus.APPROVED,
        )

    def test_student_cannot_create_event_from_idea(self):
        self.client.force_login(self.student)
        response = self.client.get(f'/ideas/{self.idea.pk}/event/')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Event.objects.count(), 0)

    def test_parliamentarian_can_create_future_event(self):
        self.client.force_login(self.member)
        starts_at = (timezone.localtime(timezone.now() + timedelta(days=2))).strftime('%Y-%m-%dT%H:%M')
        response = self.client.post(
            f'/ideas/{self.idea.pk}/event/',
            {
                'title': 'Шкільний кіновечір',
                'description': 'Перегляд фільму.',
                'starts_at': starts_at,
            },
        )
        self.assertEqual(response.status_code, 302)
        event = Event.objects.get()
        self.assertEqual(event.source_idea, self.idea)
        self.assertEqual(event.created_by, self.member)
        self.assertContains(self.client.get('/'), 'Шкільний кіновечір')



class IdeaDeletionTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            email='student@khul.ukr.education',
            password='Password123',
            display_name='Учень',
            is_active=True,
        )
        self.member = User.objects.create_user(
            email='member@khul.ukr.education',
            password='Password123',
            display_name='Парламентарій',
            role=User.Role.MEMBER,
            is_active=True,
        )
        self.admin = User.objects.create_user(
            email='ye74@khul.ukr.education',
            password='Password123',
            display_name='Адміністратор',
            role=User.Role.SECRETARY,
            is_active=True,
        )
        self.idea = Idea.objects.create(
            title='Тестова ідея',
            body='Опис ідеї',
            author=self.student,
        )

    def test_student_cannot_delete_idea(self):
        self.client.force_login(self.student)
        response = self.client.post(f'/ideas/{self.idea.pk}/delete/')
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Idea.objects.filter(pk=self.idea.pk).exists())

    def test_parliamentarian_can_delete_idea(self):
        self.client.force_login(self.member)
        response = self.client.post(f'/ideas/{self.idea.pk}/delete/')
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Idea.objects.filter(pk=self.idea.pk).exists())

    def test_primary_admin_can_delete_idea(self):
        self.client.force_login(self.admin)
        response = self.client.post(f'/ideas/{self.idea.pk}/delete/')
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Idea.objects.filter(pk=self.idea.pk).exists())

    def test_delete_requires_post(self):
        self.client.force_login(self.member)
        response = self.client.get(f'/ideas/{self.idea.pk}/delete/')
        self.assertEqual(response.status_code, 405)
        self.assertTrue(Idea.objects.filter(pk=self.idea.pk).exists())
