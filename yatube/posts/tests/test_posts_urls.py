from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, Client
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()


class URLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
        )
        cls.urls_to_templates = {
            '/': 'posts/index.html',
            f'/group/{cls.group.slug}/': 'posts/group_list.html',
            f'/profile/{cls.user}/': 'posts/profile.html',
            f'/posts/{cls.post.id}': 'posts/post_detail.html',
        }

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(URLTests.user)

    def test_available_for_everyone(self):
        for url in URLTests.urls_to_templates:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unexisting_page_return_status404_and_uses_custom_template(self):
        response_unexisting = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response_unexisting.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response_unexisting, 'core/404.html')

    def test_url_uses_correct_template(self):
        for url, template in URLTests.urls_to_templates.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_post_edit_only_author(self):
        self.posts_creator = User.objects.create_user(username='posts_creator')
        self.second_authorized_client = Client()
        self.second_authorized_client.force_login(self.posts_creator)
        self.created_post = Post.objects.create(
            text='Пост, созданный создателем постов',
            author=self.posts_creator,
        )
        response = (
            self.second_authorized_client
                .get(f'/posts/{self.created_post.id}/edit/')
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        response = (self.authorized_client
                    .get(f'/posts/{self.created_post.id}/edit/'))
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.created_post.id}
            )
        )

    def test_create_post_available_for_authorized(self):
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_post_url_redirect_anonymous_on_login(self):
        response = self.guest_client.get('/create/')
        self.assertRedirects(response, '/auth/login/?next=/create/')
