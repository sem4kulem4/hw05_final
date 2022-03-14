import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, override_settings, TestCase
from django.urls import reverse

from posts.models import Comment, Group, Post

User = get_user_model()

FIRST_POST_ID = 1
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
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

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post_correct(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый введенный текст',
            'group': self.group.id
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
                kwargs={'username': self.user}
            )
        )
        created_post = Post.objects.get(pk=FIRST_POST_ID)
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
        self.assertEqual(Post.objects.get(pk=self.post.id).text, edit_form_data['text'])

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

    def test_image_saved(self):
        self.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        self.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=self.small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый введенный текст',
            'image': self.uploaded
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        response = self.authorized_client.get(
            reverse(
                    'posts:post_detail',
                    kwargs={'post_id': FIRST_POST_ID}
            )
        )
        self.assertEqual(response.context.get('post').image, 'posts/small.gif')
