from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Comment, Group, Post

User = get_user_model()


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание'
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post_correct(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый введенный текст',
            'group': 1
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:profile',
                kwargs={'username': PostCreateFormTests.user}
            )
        )
        created_post = Post.objects.get(pk=1)
        self.assertEqual(created_post.author, self.user)
        self.assertEqual(created_post.text, form_data['text'])
        self.assertEqual(created_post.group, self.group)
        self.assertEqual(Post.objects.count(), posts_count + 1)

    def test_do_not_create_post_anonymous_user(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый введенный текст',
        }
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            '/auth/login/?next=%2Fcreate%2F'
        )
        self.assertEqual(Post.objects.count(), posts_count)

    def test_post_edit_correct(self):
        self.post = Post.objects.create(
            author=self.user,
            text='Неизмененный пост',
            group=self.group
        )
        edit_form_data = {
            'text': 'Измененный пост'
        }
        self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=edit_form_data,
            follow=True
        )
        self.assertEqual(Post.objects.get(pk=1).text, edit_form_data['text'])

    def test_cannot_add_comments_by_anonymous(self):
        self.one_post = Post.objects.create(
            author=self.user,
            text='Тестовый пост',
            group=self.group
        )
        comments_count = Comment.objects.filter(
            post__id=self.one_post.id
        ).count()
        self.guest_client.get(reverse(
            'posts:add_comment',
            kwargs={'post_id': self.one_post.id}),
            data={'text': 'это комментарий'})
        self.assertEqual(
            comments_count,
            Comment.objects.filter(post__id=self.one_post.id).count()
        )

    def test_comments_shows_on_page_after_creating(self):
        self.one_post = Post.objects.create(
            author=self.user,
            text='Тестовый пост',
            group=self.group
        )
        comments_count = Comment.objects.filter(
            post__id=self.one_post.id
        ).count()
        self.authorized_client.post(reverse(
            'posts:add_comment',
            kwargs={'post_id': self.one_post.id}),
            data={'text': 'это комментарий'}
        )
        self.assertEqual(
            Comment.objects.filter(post__id=self.one_post.id).count(),
            comments_count + 1
        )
