from django.test import TestCase

from accounts.models import User
from ideas.models import Idea
from .models import Notification


class IdeaNotificationTests(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(
            email='author@example.com',
            password='Password123',
            display_name='Автор',
            is_active=True,
        )
        self.member = User.objects.create_user(
            email='member@example.com',
            password='Password123',
            display_name='Член парламенту',
            role=User.Role.MEMBER,
            is_active=True,
        )
        self.idea = Idea.objects.create(
            title='Покращити бібліотеку',
            body='Опис ідеї',
            author=self.author,
        )

    def test_status_change_notifies_author_and_marks_read_when_opened(self):
        self.assertNotEqual(self.author.pk, self.member.pk)
        self.assertEqual(self.member.role, User.Role.MEMBER)
        self.client.force_login(self.member)

        response = self.client.post(
            f'/ideas/{self.idea.pk}/',
            {
                'status': Idea.Status.IN_PROGRESS,
                'status_reason': '',
                'completion_report': '',
            },
        )

        self.assertRedirects(response, f'/ideas/{self.idea.pk}/')
        self.idea.refresh_from_db()
        self.assertEqual(self.idea.status, Idea.Status.IN_PROGRESS)
        notification = Notification.objects.get(recipient=self.author, idea=self.idea)
        self.assertEqual(notification.previous_status, Idea.Status.SUBMITTED)
        self.assertEqual(notification.new_status, Idea.Status.IN_PROGRESS)

        self.client.force_login(self.author)
        inbox = self.client.get('/notifications/')
        self.assertContains(inbox, 'Покращити бібліотеку')
        self.assertContains(inbox, 'Непрочитані сповіщення: 1')

        opened = self.client.post(f'/notifications/{notification.pk}/open/')
        self.assertRedirects(opened, f'/ideas/{self.idea.pk}/')
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)

    def test_unchanged_status_does_not_create_notification(self):
        self.idea.status = Idea.Status.IN_PROGRESS
        self.idea.save(update_fields=['status'])
        self.client.force_login(self.member)

        self.client.post(
            f'/ideas/{self.idea.pk}/',
            {
                'status': Idea.Status.IN_PROGRESS,
                'status_reason': '',
                'completion_report': '',
            },
        )

        self.assertFalse(Notification.objects.exists())

    def test_editor_does_not_receive_a_notification_for_own_idea(self):
        own_idea = Idea.objects.create(
            title='Ідея члена парламенту',
            body='Опис',
            author=self.member,
        )
        self.client.force_login(self.member)

        self.client.post(
            f'/ideas/{own_idea.pk}/',
            {
                'status': Idea.Status.IN_PROGRESS,
                'status_reason': '',
                'completion_report': '',
            },
        )

        self.assertFalse(Notification.objects.exists())

    def test_users_cannot_read_or_mark_another_users_notification(self):
        notification = Notification.objects.create(
            recipient=self.author,
            idea=self.idea,
            previous_status=Idea.Status.SUBMITTED,
            new_status=Idea.Status.IN_PROGRESS,
        )
        self.client.force_login(self.member)

        self.assertNotContains(self.client.get('/notifications/'), 'Покращити бібліотеку')
        self.assertEqual(self.client.post(f'/notifications/{notification.pk}/open/').status_code, 404)
        notification.refresh_from_db()
        self.assertFalse(notification.is_read)

    def test_notification_open_requires_post(self):
        notification = Notification.objects.create(
            recipient=self.author,
            idea=self.idea,
            previous_status=Idea.Status.SUBMITTED,
            new_status=Idea.Status.IN_PROGRESS,
        )
        self.client.force_login(self.author)

        self.assertEqual(self.client.get(f'/notifications/{notification.pk}/open/').status_code, 405)
        notification.refresh_from_db()
        self.assertFalse(notification.is_read)
