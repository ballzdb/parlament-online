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


class ParliamentDecisionPageTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='author@example.com',
            password='Password123',
            display_name='Автор',
            is_active=True,
        )

    def test_public_page_shows_decisions_and_hides_undecided_ideas(self):
        Idea.objects.create(
            title='Виконана ідея',
            body='Опис виконаної ідеї',
            status=Idea.Status.DONE,
            completion_report='Опублікований звіт',
            author=self.user,
        )
        Idea.objects.create(
            title='Відхилена ідея',
            body='Опис відхиленої ідеї',
            status=Idea.Status.REJECTED,
            status_reason='Причина рішення',
            author=self.user,
        )
        Idea.objects.create(
            title='Ідея на розгляді',
            body='Ще немає рішення',
            status=Idea.Status.UNDER_REVIEW,
            author=self.user,
        )

        response = self.client.get('/decisions/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Виконана ідея')
        self.assertContains(response, 'Опублікований звіт')
        self.assertContains(response, 'Відхилена ідея')
        self.assertContains(response, 'Причина рішення')
        self.assertNotContains(response, 'Ідея на розгляді')
