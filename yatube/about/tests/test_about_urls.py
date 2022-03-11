from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from http import HTTPStatus

User = get_user_model()


class UsersURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')

    def setUp(self):
        self.guest_client = Client()

    def test_about_available_urls_in_app_users(self):
        available_for_all_urls = {
            '/about/author/': HTTPStatus.OK,
            '/about/tech/': HTTPStatus.OK,
        }
        for address, http_status in available_for_all_urls.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, http_status)

    def test_url_uses_correct_template(self):
        url_to_template = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html',
        }
        for url, template in url_to_template.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)
