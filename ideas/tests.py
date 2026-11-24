from datetime import timedelta

from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from accounts.models import Commission, User
from ideas.models import Event, Idea, IdeaVote
from moderation.models import ModerationEntry


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


class PublicIdeaDetailTests(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(
            email='public-detail-author@example.com',
            password='Password123',
            is_active=True,
        )
        self.approved = Idea.objects.create(
            title='Відкрита учнівська ініціатива',
            body='Опис, доступний усім відвідувачам.',
            author=self.author,
            moderation_status=Idea.ModerationStatus.APPROVED,
        )
        self.pending = Idea.objects.create(
            title='Приватна ідея на модерації',
            body='Цей текст не має бути публічним.',
            author=self.author,
            moderation_status=Idea.ModerationStatus.PENDING,
        )

    def test_anonymous_visitor_can_read_published_idea(self):
        response = self.client.get(f'/ideas/{self.approved.pk}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.approved.title)
        self.assertContains(response, 'увійдіть до облікового запису')

    def test_anonymous_visitor_cannot_read_pending_idea(self):
        response = self.client.get(f'/ideas/{self.pending.pk}/')
        self.assertEqual(response.status_code, 404)

    def test_anonymous_visitor_cannot_vote(self):
        response = self.client.post(f'/ideas/{self.approved.pk}/', {'vote': '1'})
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
        self.approved.refresh_from_db()
        self.assertEqual(self.approved.vote_count, 0)
        self.assertFalse(IdeaVote.objects.filter(idea=self.approved).exists())


class PublicProfilePrivacyTests(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(
            email='private-address@example.com',
            password='Password123',
            display_name='',
            is_active=True,
        )
        self.idea = Idea.objects.create(
            title='Публічна ідея без відкритої пошти',
            body='Зміст публічної ініціативи.',
            author=self.author,
            moderation_status=Idea.ModerationStatus.APPROVED,
        )

    def test_public_idea_pages_do_not_expose_author_email(self):
        for path in ('/', '/ideas/', f'/ideas/{self.idea.pk}/'):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'Учень')
            self.assertNotContains(response, self.author.email)

    def test_public_event_page_does_not_expose_creator_email(self):
        event = Event.objects.create(
            title='Відкритий захід',
            starts_at=timezone.now() + timedelta(days=1),
            created_by=self.author,
        )
        response = self.client.get(f'/ideas/events/{event.pk}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Представник самоврядування')
        self.assertNotContains(response, self.author.email)


    def test_public_moderation_history_does_not_expose_staff_email(self):
        staff_email = 'moderator-private@example.com'
        ModerationEntry.objects.create(
            target_type='idea',
            target_id=self.approved.pk,
            verdict={
                'action': 'approve',
                'actor_email': staff_email,
                'actor_name': staff_email,
                'reason': 'Перевірено.',
            },
        )
        response = self.client.get(f'/ideas/{self.approved.pk}/')
        self.assertContains(response, 'Історія модерації')
        self.assertNotContains(response, staff_email)
