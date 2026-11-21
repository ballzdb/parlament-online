from django.test import TestCase

from accounts.models import AuditLog, User
from appeals.models import Appeal
from ideas.models import Idea


class ModerationAppealTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            email='appeal-author@khul.ukr.education',
            password='Password123',
            display_name='Автор ідеї',
            is_active=True,
        )
        self.other_student = User.objects.create_user(
            email='other-student@khul.ukr.education',
            password='Password123',
            display_name='Інший учень',
            is_active=True,
        )
        self.secretary = User.objects.create_user(
            email='appeal-secretary@khul.ukr.education',
            password='Password123',
            display_name='Секретар',
            role=User.Role.SECRETARY,
            is_active=True,
        )
        self.member = User.objects.create_user(
            email='appeal-member@khul.ukr.education',
            password='Password123',
            role=User.Role.MEMBER,
            is_active=True,
        )
        self.idea = Idea.objects.create(
            title='Відхилена ініціатива',
            body='Опис ініціативи',
            author=self.student,
            moderation_status=Idea.ModerationStatus.REJECTED,
            moderation_reason='Потрібно надати більше деталей.',
        )

    def test_author_can_submit_private_appeal_for_own_rejected_idea(self):
        self.client.force_login(self.student)
        response = self.client.post(
            f'/appeals/create/?idea={self.idea.pk}',
            {
                'related_idea_id': self.idea.pk,
                'kind': Appeal.Kind.MODERATION,
                'subject': 'Прошу переглянути рішення',
                'body': 'Додаю пояснення до своєї пропозиції.',
                'visibility': Appeal.Visibility.PUBLIC,
            },
        )
        self.assertEqual(response.status_code, 302)
        appeal = Appeal.objects.get(author=self.student)
        self.assertEqual(appeal.kind, Appeal.Kind.MODERATION)
        self.assertEqual(appeal.visibility, Appeal.Visibility.PRIVATE)
        self.assertEqual(appeal.related_idea, self.idea)

        self.client.force_login(self.other_student)
        self.assertNotContains(self.client.get('/appeals/'), 'Прошу переглянути рішення')
        self.client.force_login(self.student)
        self.assertContains(self.client.get('/appeals/'), 'Прошу переглянути рішення')
        self.client.force_login(self.secretary)
        self.assertContains(self.client.get('/appeals/'), 'Прошу переглянути рішення')

    def test_student_cannot_appeal_another_students_idea(self):
        self.client.force_login(self.other_student)
        self.assertEqual(self.client.get(f'/appeals/create/?idea={self.idea.pk}').status_code, 404)
        response = self.client.post(
            f'/appeals/create/?idea={self.idea.pk}',
            {
                'related_idea_id': self.idea.pk,
                'kind': Appeal.Kind.MODERATION,
                'subject': 'Тест',
                'body': 'Тестове звернення',
            },
        )
        self.assertEqual(response.status_code, 404)

    def test_moderation_appeal_kind_cannot_be_used_without_rejected_idea(self):
        self.client.force_login(self.student)
        response = self.client.post('/appeals/create/', {
            'kind': Appeal.Kind.MODERATION,
            'subject': 'Оскарження',
            'body': 'Спроба створити звернення без прив’язки.',
            'visibility': Appeal.Visibility.PRIVATE,
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Appeal.objects.exists())

    def test_only_secretary_can_manage_and_reply_to_appeal(self):
        appeal = Appeal.objects.create(
            author=self.student,
            related_idea=self.idea,
            kind=Appeal.Kind.MODERATION,
            subject='Переглянути рішення',
            body='Прошу переглянути рішення.',
            visibility=Appeal.Visibility.PRIVATE,
        )
        self.client.force_login(self.member)
        self.assertEqual(self.client.get(f'/appeals/{appeal.pk}/manage/').status_code, 403)

        self.client.force_login(self.secretary)
        response = self.client.post(f'/appeals/{appeal.pk}/manage/', {
            'status': Appeal.Status.RESOLVED,
            'public_answer': 'Рішення переглянуто. Дякуємо за уточнення.',
        })
        self.assertEqual(response.status_code, 302)
        appeal.refresh_from_db()
        self.assertEqual(appeal.status, Appeal.Status.RESOLVED)
        self.assertEqual(appeal.public_answer, 'Рішення переглянуто. Дякуємо за уточнення.')
        self.assertTrue(AuditLog.objects.filter(action='appeal_updated', user=self.secretary).exists())

        self.client.force_login(self.student)
        self.assertContains(self.client.get('/appeals/'), 'Рішення переглянуто. Дякуємо за уточнення.')

    def test_rejected_idea_detail_offers_appeal_link_to_its_author(self):
        self.client.force_login(self.student)
        response = self.client.get(f'/ideas/{self.idea.pk}/')
        self.assertContains(response, 'Оскаржити рішення')
        self.client.force_login(self.other_student)
        self.assertEqual(self.client.get(f'/ideas/{self.idea.pk}/').status_code, 404)
