from datetime import timedelta

from django.core import mail
from django.core.management import call_command
from django.test import Client, TestCase, override_settings
from django.utils import timezone


from accounts.models import User
from .models import AnonymousMetric


class ClassStatisticsTests(TestCase):
    def setUp(self):
        parliamentarian = User.objects.create_user(
            email='parliamentarian@example.com',
            password='Password123!',
            role=User.Role.MEMBER,
            is_active=True,
        )
        self.client.force_login(parliamentarian)

    def create_student(self, email, **kwargs):
        kwargs.setdefault('is_active', True)
        return User.objects.create_user(
            email=email,
            password='Password123!',
            **kwargs,
        )

    @override_settings(TOTAL_STUDENTS=10)
    def test_parliament_page_shows_anonymous_counts_and_school_coverage(self):
        self.create_student('one@example.com', grade=9, class_letter='А', display_name='Учениця')
        self.create_student('two@example.com', grade=9, class_letter='А')
        self.create_student('student-4@example.com', grade=9, class_letter='А')
        self.create_student('student-5@example.com', grade=9, class_letter='А')
        self.create_student('student-6@example.com', grade=9, class_letter='А')
        self.create_student('three@example.com', grade=10, class_letter='Б')
        self.create_student('inactive@example.com', grade=9, class_letter='А', is_active=False)
        self.create_student(
            'member@example.com',
            grade=9,
            class_letter='А',
            role=User.Role.MEMBER,
        )

        response = self.client.get('/analytics/classes/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Парламент за класами')
        self.assertContains(response, '60%')
        self.assertContains(response, '9-А')
        self.assertNotContains(response, '10-Б')
        self.assertContains(response, '5 учнів')
        self.assertNotContains(response, 'one@example.com')
        self.assertNotContains(response, 'Учениця')

    @override_settings(TOTAL_STUDENTS=0)
    def test_page_handles_missing_class_data_and_unknown_school_size(self):
        self.create_student('no-grade@example.com')

        response = self.client.get('/analytics/classes/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '1')
        self.assertContains(response, 'Поки немає активних учнів із зазначеним класом.')
        self.assertNotContains(response, 'від загальної кількості учнів ліцею')


class AnonymousAnalyticsTests(TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        response = self.client.get('/')
        self.csrf_token = str(response.context['csrf_token'])

    def post_metric(self, payload, consent='yes'):
        return self.client.post(
            '/analytics/anonymous-event/',
            data=payload,
            content_type='application/json',
            HTTP_X_CSRFTOKEN=self.csrf_token,
            HTTP_X_ANONYMOUS_ANALYTICS_CONSENT=consent,
        )

    def test_collection_requires_consent_and_aggregates_only_section_counts(self):
        denied_response = self.post_metric('{"section":"home"}', consent='no')
        self.assertEqual(denied_response.status_code, 403)
        self.assertEqual(AnonymousMetric.objects.count(), 0)

        first_response = self.post_metric('{"section":"home"}')
        second_response = self.post_metric('{"section":"home"}')

        self.assertEqual(first_response.status_code, 202)
        self.assertEqual(second_response.status_code, 202)
        self.assertEqual(AnonymousMetric.objects.count(), 1)
        metric = AnonymousMetric.objects.get()
        self.assertEqual(metric.page_views, 2)
        self.assertEqual(metric.section, AnonymousMetric.Section.HOME)
        self.assertEqual(
            {field.name for field in AnonymousMetric._meta.fields},
            {'id', 'date', 'section', 'page_views'},
        )

    def test_invalid_sections_and_non_post_requests_are_rejected(self):
        response = self.post_metric('{"section":"/accounts/login/?email=private"}')
        missing_consent = self.post_metric('{"section":"home"}', consent='')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(missing_consent.status_code, 403)
        self.assertEqual(self.client.get('/analytics/anonymous-event/').status_code, 405)
        self.assertEqual(AnonymousMetric.objects.count(), 0)

    def test_collection_requires_csrf_token(self):
        response = Client(enforce_csrf_checks=True).post(
            '/analytics/anonymous-event/',
            data='{"section":"home"}',
            content_type='application/json',
            HTTP_X_ANONYMOUS_ANALYTICS_CONSENT='yes',
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(AnonymousMetric.objects.count(), 0)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_daily_report_is_sent_only_to_designated_recipient(self):
        report_date = timezone.localdate() - timedelta(days=1)
        AnonymousMetric.objects.create(
            date=report_date,
            section=AnonymousMetric.Section.IDEAS,
            page_views=12,
        )
        AnonymousMetric.objects.create(
            date=report_date,
            section=AnonymousMetric.Section.HOME,
            page_views=8,
        )

        call_command('send_anonymous_report')

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['ye74@khul.ukr.education'])
        self.assertIn('Головна: 8', mail.outbox[0].body)
        self.assertIn('Ідеї: 12', mail.outbox[0].body)
