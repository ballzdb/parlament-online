from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings

from accounts.models import User

from .middleware import AnalyticsAccessMiddleware


class AnalyticsAccessMiddlewareTests(TestCase):
    protected_paths = ('/analytics/', '/analytics/export.csv', '/analytics/classes/')

    def create_user(self, email, role):
        return User.objects.create_user(
            email=email,
            password='Password123!',
            role=role,
            is_active=True,
        )

    def test_guest_and_student_cannot_access_analytics(self):
        for path in self.protected_paths:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 302)

        student = self.create_user('student@example.com', User.Role.STUDENT)
        self.client.force_login(student)
        for path in self.protected_paths:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 403)

    def test_parliamentarian_and_secretary_pass_the_access_gate(self):
        middleware = AnalyticsAccessMiddleware(lambda request: HttpResponse(status=200))

        for role in (User.Role.MEMBER, User.Role.SECRETARY):
            user = self.create_user(f'{role}@example.com', role)
            for path in self.protected_paths:
                request = RequestFactory().get(path)
                request.user = user
                with self.subTest(role=role, path=path):
                    self.assertEqual(middleware(request).status_code, 200)


class AnalyticsAccessMiddlewarePathTests(SimpleTestCase):
    def test_anonymous_analytics_collection_remains_public(self):
        middleware = AnalyticsAccessMiddleware(lambda request: HttpResponse(status=202))
        request = RequestFactory().post('/analytics/anonymous-event/')
        request.user = AnonymousUser()

        self.assertEqual(middleware(request).status_code, 202)


class AnalyticsClassPrivacyTests(TestCase):
    def setUp(self):
        member = User.objects.create_user(
            email='member@example.com',
            password='Password123!',
            role=User.Role.MEMBER,
            is_active=True,
        )
        self.client.force_login(member)

    @override_settings(TOTAL_STUDENTS=10)
    def test_classes_with_fewer_than_five_students_are_hidden(self):
        for number in range(4):
            User.objects.create_user(
                email=f'student-{number}@example.com',
                password='Password123!',
                grade=9,
                class_letter='А',
                is_active=True,
            )

        response = self.client.get('/analytics/classes/')

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, '9-А')

    @override_settings(TOTAL_STUDENTS=0)
    def test_unknown_school_size_is_explained(self):
        response = self.client.get('/analytics/classes/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Загальну кількість учнів ліцею не задано.')
