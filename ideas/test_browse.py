from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from ideas.models import Idea


class IdeaCatalogueTests(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(
            email='catalogue@example.com',
            password='Password123',
            display_name='Автор ідей',
            is_active=True,
        )

    def make_idea(self, title, body, moderation_status=Idea.ModerationStatus.APPROVED):
        return Idea.objects.create(
            title=title,
            body=body,
            author=self.author,
            moderation_status=moderation_status,
        )

    def test_search_matches_title_and_description(self):
        self.make_idea('Reading corner', 'A quiet room for independent study.')
        self.make_idea('Sports day', 'A school-wide athletics event.')

        response = self.client.get(reverse('ideas:list'), {'q': 'independent study'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Reading corner')
        self.assertNotContains(response, 'Sports day')
        self.assertEqual(response.context['result_count'], 1)

    def test_anonymous_catalogue_hides_pending_ideas(self):
        self.make_idea('Public idea', 'Visible to everyone.')
        self.make_idea(
            'Private draft',
            'Waiting for a moderator.',
            moderation_status=Idea.ModerationStatus.PENDING,
        )

        response = self.client.get(reverse('ideas:list'))

        self.assertContains(response, 'Public idea')
        self.assertNotContains(response, 'Private draft')
        self.assertEqual(response.context['result_count'], 1)

    def test_catalogue_paginates_after_nine_ideas(self):
        for number in range(10):
            self.make_idea(f'Idea {number}', f'Description {number}')

        first_page = self.client.get(reverse('ideas:list'))
        second_page = self.client.get(reverse('ideas:list'), {'page': '2'})

        self.assertEqual(first_page.status_code, 200)
        self.assertEqual(len(first_page.context['ideas']), 9)
        self.assertEqual(first_page.context['page_obj'].paginator.num_pages, 2)
        self.assertEqual(len(second_page.context['ideas']), 1)
