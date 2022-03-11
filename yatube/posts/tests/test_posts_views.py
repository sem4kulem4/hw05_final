import shutil
import tempfile
from http import HTTPStatus

from django import forms
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from django.test import override_settings

from posts.models import Comment, Group, Post

User = get_user_model()

FIRST_PAGE_POSTS = 10
SECOND_PAGE_POSTS = 4
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание'
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        Post.objects.bulk_create(
            objs=[
                Post(author=cls.user, text='Тестовый пост', group=cls.group, )
                for i in range(FIRST_PAGE_POSTS + SECOND_PAGE_POSTS - 1)
            ]
        )
        cls.one_post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=cls.uploaded
        )
        cls.urls_paginator = {
            'posts:index': {},
            'posts:profile': {'username': cls.user},
            'posts:group_list': {'slug': cls.group.slug}
        }
        cls.templates_and_pages_anonymous = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html': reverse(
                'posts:group_list',
                kwargs={'slug': cls.group.slug}
            ),
            'posts/profile.html': reverse(
                'posts:profile',
                kwargs={'username': cls.user}
            ),
            'posts/post_detail.html': reverse(
                'posts:post_detail',
                kwargs={'post_id': 1}
            ),
        }
        cls.templates_and_pages_authorized = {
            'posts:post_edit': {'post_id': 1},
            'posts:post_create': {},
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_about_pages_uses_correct_templates_in_anonymous(self):
        for template, reversed in self.templates_and_pages_anonymous.items():
            with self.subTest(reverse_name=reversed):
                response = self.authorized_client.get(reversed)
                self.assertTemplateUsed(response, template)
                self.assertTrue(
                    Post.objects.filter(image='posts/small.gif').exists())

    def test_about_post_edit_and_create_use_correct_template_authorized(self):
        for url, kwarg in self.templates_and_pages_authorized.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(
                    reverse(url, kwargs=kwarg)
                )
                self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_paginator_correct_context(self):
        for url, kwarg in self.urls_paginator.items():
            with self.subTest(url=url):
                response = self.client.get(
                    reverse(url, kwargs=kwarg),
                    {'page': 1}
                )
                self.assertEqual(
                    len(response.context['page_obj']),
                    FIRST_PAGE_POSTS
                )
                response = (
                    self.client
                        .get(reverse(url, kwargs=kwarg), {'page': 2})
                )
                self.assertEqual(len(
                    response.context['page_obj']),
                    SECOND_PAGE_POSTS
                )

    def test_pages_shows_correct_context(self):
        for _, url in self.templates_and_pages_anonymous.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(
                    response.context.get('post').text,
                    'Тестовый пост'
                )
                self.assertEqual(
                    response.context.get('post').author,
                    self.user
                )
                self.assertEqual(
                    response.context.get('post').group,
                    self.group
                )

    def test_post_edit_and_create_show_correct_context(self):
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for url, kwarg in self.templates_and_pages_authorized.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(
                    reverse(url, kwargs=kwarg)
                )
                for value, expected in form_fields.items():
                    with self.subTest(value=value):
                        form_field = (
                            response.context
                                .get('form')
                                .fields.get(value)
                        )
                        self.assertIsInstance(form_field, expected)

    def test_add_comments_only_by_authorized(self):
        response = self.guest_client.get('posts:add_comment', post_id=14)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_comments_shows_on_page_after_creating(self):
        comments_count = Comment.objects.filter(
            post__id=FIRST_PAGE_POSTS + SECOND_PAGE_POSTS
        ).count()
        self.test_comment = Comment.objects.create(
            post=self.one_post,
            author=self.user,
            text='это комментарий'
        )
        self.assertEqual(
            Comment.objects.filter(post__id=14).count(),
            comments_count + 1
        )

    def test_cache_works_correctly(self):
        cached_post = Post.objects.create(
            author=self.user,
            text='Пост для теста кэша',
            group=self.group,
        )
        response_first = self.guest_client.get(reverse('posts:index'))
        content_first = response_first.content
        cached_post.delete()
        response_second = self.guest_client.get(reverse('posts:index'))
        content_second = response_second.content
        self.assertTrue(content_first == content_second)
        cache.clear()
        response_third = self.guest_client.get(reverse('posts:index'))
        content_third = response_third.content
        self.assertFalse(content_first == content_third)
