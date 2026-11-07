from django.db import IntegrityError
from django.test import TestCase

from accounts.models import Commission, User
from ideas.models import Idea, IdeaVote


class IdeaVoteTests(TestCase):
    def setUp(self):
        self.commission = Commission.objects.create(name='Навчання', slug='navchannia')
        self.user = User.objects.create_user(email='user@example.com', password='Password123', display_name='Користувач', is_active=True)
        self.idea = Idea.objects.create(
            title='Відкрити асинхронний клуб',
            body='Мета — зібрати учнів...',
            author=self.user,
            commission=self.commission,
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
