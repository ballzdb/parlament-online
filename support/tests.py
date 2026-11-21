from django.test import TestCase

from .models import FAQ


class SupportPageTests(TestCase):
    def test_support_page_shows_default_faq_when_database_is_empty(self):
        response = self.client.get('/support/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Як подати ідею?')
        self.assertContains(response, 'Чому моєї ідеї немає в загальному списку?')
        self.assertContains(response, 'Не надсилайте пароль')

    def test_support_page_prefers_faq_entries_managed_in_admin(self):
        FAQ.objects.create(
            question='Спеціальне запитання',
            answer='Відповідь адміністратора.',
            order=1,
        )

        response = self.client.get('/support/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Спеціальне запитання')
        self.assertContains(response, 'Відповідь адміністратора.')
        self.assertNotContains(response, 'Як подати ідею?')
