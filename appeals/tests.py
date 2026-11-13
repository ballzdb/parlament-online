from django.test import TestCase

from accounts.models import User

from .models import Appeal


class AppealSubmissionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='student@khul.ukr.education',
            password='Password123!',
            display_name='Учениця Тестова',
            is_active=True,
        )

    def test_signed_in_student_can_submit_public_appeal_anonymously(self):
        self.client.force_login(self.user)
        response = self.client.post(
            '/appeals/create/',
            {
                'kind': Appeal.Kind.PROPOSAL,
                'subject': 'Потрібен тихий простір',
                'body': 'Прошу облаштувати місце для навчання.',
                'visibility': Appeal.Visibility.PUBLIC,
            },
        )

        self.assertRedirects(response, '/appeals/')
        appeal = Appeal.objects.get(subject='Потрібен тихий простір')
        self.assertEqual(appeal.author, self.user)
        self.assertEqual(appeal.status, Appeal.Status.NEW)

        self.client.logout()
        response = self.client.get('/appeals/')
        self.assertContains(response, appeal.subject)
        self.assertContains(response, 'Авторство приховане')
        self.assertNotContains(response, self.user.email)
        self.assertNotContains(response, self.user.display_name)

    def test_submission_requires_login(self):
        response = self.client.get('/appeals/create/')
        self.assertRedirects(response, '/accounts/login/?next=/appeals/create/')

    def test_student_sees_public_appeals_and_own_private_appeals(self):
        other_user = User.objects.create_user(
            email='other@khul.ukr.education',
            password='Password123!',
            is_active=True,
        )
        public_appeal = Appeal.objects.create(author=other_user, subject='Публічне', body='Видиме')
        own_private_appeal = Appeal.objects.create(
            author=self.user,
            subject='Приватне моє',
            body='Тільки для мене',
            visibility=Appeal.Visibility.PRIVATE,
        )
        Appeal.objects.create(
            author=other_user,
            subject='Приватне чуже',
            body='Не показувати',
            visibility=Appeal.Visibility.PRIVATE,
        )
        self.client.force_login(self.user)

        response = self.client.get('/appeals/')

        self.assertContains(response, public_appeal.subject)
        self.assertContains(response, own_private_appeal.subject)
        self.assertNotContains(response, 'Приватне чуже')

    def test_private_appeal_text_is_not_shown_on_homepage_to_guests_or_other_students(self):
        private_appeal = Appeal.objects.create(
            author=self.user,
            subject='Приватна тема',
            body='Унікальний приватний текст звернення',
            visibility=Appeal.Visibility.PRIVATE,
        )
        public_appeal = Appeal.objects.create(
            author=self.user,
            subject='Публічна тема',
            body='Публічний текст звернення',
            visibility=Appeal.Visibility.PUBLIC,
        )

        guest_response = self.client.get('/')
        self.assertNotContains(guest_response, private_appeal.body)
        self.assertContains(guest_response, public_appeal.body)

        other_student = User.objects.create_user(
            email='other@khul.ukr.education',
            password='Password123!',
            is_active=True,
        )
        self.client.force_login(other_student)
        student_response = self.client.get('/')
        self.assertNotContains(student_response, private_appeal.body)
        self.assertContains(student_response, public_appeal.body)

    def test_secretary_can_see_author_of_anonymous_submission(self):
        appeal = Appeal.objects.create(author=self.user, subject='Анонімне звернення', body='Текст')
        secretary = User.objects.create_user(
            email='secretary@khul.ukr.education',
            password='Password123!',
            is_active=True,
            role=User.Role.SECRETARY,
        )
        self.client.force_login(secretary)

        response = self.client.get('/appeals/')

        self.assertContains(response, appeal.subject)
        self.assertContains(response, self.user.email)

# Create your tests here.
