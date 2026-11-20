from django.test import TestCase

from accounts.models import Commission, User
from kanban.models import KanbanCard, TaskComment


class KanbanAccessTests(TestCase):
    def setUp(self):
        self.commission, _ = Commission.objects.get_or_create(slug='navchannia', defaults={'name': 'Навчання'})
        self.card = KanbanCard.objects.create(
            commission=self.commission,
            title='Підготувати опитування',
            description='Опис',
            status='todo',
        )

    def test_student_can_view_board_and_task_but_cannot_manage(self):
        student = User.objects.create_user(email='student@example.com', password='Password123', role=User.Role.STUDENT, is_active=True)
        self.client.force_login(student)
        response = self.client.get('/kanban/navchannia/')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Створити завдання')
        detail = self.client.get(f'/kanban/card/{self.card.pk}/')
        self.assertEqual(detail.status_code, 200)
        self.assertNotContains(detail, 'Додати коментар')

    def test_member_can_edit_card_status(self):
        member = User.objects.create_user(email='member@example.com', password='Password123', role=User.Role.MEMBER, is_active=True)
        self.client.force_login(member)
        response = self.client.post(
            f'/kanban/card/{self.card.pk}/edit/',
            {'title': 'Підготувати опитування', 'description': 'Опис', 'assignee': '', 'due_date': '', 'status': 'in_progress'},
        )
        self.assertEqual(response.status_code, 302)
        self.card.refresh_from_db()
        self.assertEqual(self.card.status, 'in_progress')

    def test_member_can_create_task(self):
        member = User.objects.create_user(email='member@example.com', password='Password123', role=User.Role.MEMBER, is_active=True)
        self.client.force_login(member)
        response = self.client.post('/kanban/create/', {
            'commission': self.commission.pk,
            'title': 'Організувати зустріч',
            'description': 'Підготувати план і запросити учнів.',
            'assignee': '',
            'due_date': '',
        })
        self.assertEqual(response.status_code, 302)
        task = KanbanCard.objects.get(title='Організувати зустріч')
        self.assertEqual(task.created_by, member)
        self.assertEqual(task.commission, self.commission)

    def test_student_cannot_create_task_or_comment(self):
        student = User.objects.create_user(email='student@example.com', password='Password123', role=User.Role.STUDENT, is_active=True)
        self.client.force_login(student)
        self.assertEqual(self.client.get('/kanban/create/').status_code, 403)
        response = self.client.post(f'/kanban/card/{self.card.pk}/', {'body': 'Оновлення'})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(TaskComment.objects.count(), 0)

    def test_member_can_comment_on_task(self):
        member = User.objects.create_user(email='member@example.com', password='Password123', role=User.Role.MEMBER, is_active=True)
        self.client.force_login(member)
        response = self.client.post(f'/kanban/card/{self.card.pk}/', {'body': 'Почали готувати матеріали.'})
        self.assertEqual(response.status_code, 302)
        comment = TaskComment.objects.get(card=self.card)
        self.assertEqual(comment.author, member)
        self.assertEqual(comment.body, 'Почали готувати матеріали.')
