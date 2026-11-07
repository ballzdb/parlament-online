from django.test import TestCase

from accounts.models import Commission, User
from kanban.models import KanbanCard


class KanbanAccessTests(TestCase):
    def setUp(self):
        self.commission = Commission.objects.create(name='Навчання', slug='navchannia')
        self.card = KanbanCard.objects.create(
            commission=self.commission,
            title='Підготовити опитування',
            description='Опис',
            status='todo',
        )

    def test_student_view_is_read_only(self):
        student = User.objects.create_user(email='student@example.com', password='Password123', role=User.Role.STUDENT, is_active=True)
        self.client.force_login(student)
        response = self.client.get('/kanban/navchannia/')
        self.assertEqual(response.status_code, 200)

    def test_member_can_edit_card(self):
        member = User.objects.create_user(email='member@example.com', password='Password123', role=User.Role.MEMBER, is_active=True)
        self.client.force_login(member)
        response = self.client.post(
            f'/kanban/card/{self.card.pk}/edit/',
            {'title': 'Підготовити опитування', 'description': 'Опис', 'assignee': '', 'due_date': '', 'status': 'in_progress'},
        )
        self.assertEqual(response.status_code, 302)
        self.card.refresh_from_db()
        self.assertEqual(self.card.status, 'in_progress')
