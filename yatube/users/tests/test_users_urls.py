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
        self.authorized_client = Client()
        self.authorized_client.force_login(UsersURLTests.user)

    def test_about_available_urls_in_app_users(self):
        available_for_all_urls = {
            '/auth/signup/': HTTPStatus.OK,
            '/auth/logout/': HTTPStatus.OK,
            '/auth/login/': HTTPStatus.OK,
            '/auth/password_reset/': HTTPStatus.OK,
            '/auth/password_reset/done/': HTTPStatus.OK,
            '/auth/reset/<uidb64>/<token>/': HTTPStatus.OK,
            '/auth/reset/done/': HTTPStatus.OK,
            '/auth/password_change/': HTTPStatus.OK,
            '/auth/password_change/done/': HTTPStatus.OK

        }
        for address, http_status in available_for_all_urls.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                if '/password_change/' in address:
                    response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, http_status)

    def test_url_uses_correct_template(self):
        url_to_template = {
            '/auth/signup/': 'users/signup.html',
            '/auth/logout/': 'users/logged_out.html',
            '/auth/login/': 'users/login.html',
            '/auth/password_reset/': 'users/password_reset_form.html',
            '/auth/password_reset/done/': 'users/password_reset_done.html',
            '/auth/reset/<uidb64>/<token>/':
                'users/password_reset_confirm.html',
            '/auth/reset/done/': 'users/password_reset_complete.html',
            '/auth/password_change/': 'users/password_change_form.html',
            '/auth/password_change/done/': 'users/password_change_done.html',

        }
        for url, template in url_to_template.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                if '/password_change/' in url:
                    response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)
