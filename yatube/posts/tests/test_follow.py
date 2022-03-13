import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.cache import cache
from django.test import Client, TestCase
from django.test import override_settings
from django.urls import reverse

from posts.models import Follow, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TestFollowing(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.follower = User.objects.create_user(username='follower')
        cls.author = User.objects.create_user(username='author')
        cls.one_post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
        )
        cls.sub = Follow.objects.create(user=cls.follower, author=cls.author)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.follower)

    def test_follow_for_authorized(self):
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertIn(self.one_post, response.context['page_obj'])

    def test_follow_creates_data(self):
        another_author = User.objects.create_user(username='another_author')
        number_of_follows = Follow.objects.filter(
            user=self.follower,
            author=another_author
        ).count()
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': another_author}
        ))
        after_following = Follow.objects.filter(
            user=self.follower,
            author=another_author
        ).count()
        self.assertEqual(number_of_follows + 1, after_following)

    def test_unfollow_for_authorized(self):
        self.sub.delete()
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertNotIn(self.one_post, response.context['page_obj'])

    def test_unfollow_delete_data(self):
        number_of_follows = Follow.objects.filter(
            user=self.follower,
            author=self.author
        ).count()
        self.authorized_client.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.author}
        ))
        after_following = Follow.objects.filter(
            user=self.follower,
            author=self.author
        ).count()
        self.assertEqual(number_of_follows, after_following + 1)

    def test_new_post_for_followers_exist_not_for_others(self):
        self.unfollowed_user = User.objects.create_user(username='unfollowed')
        response_follower = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        self.assertIn(self.one_post, response_follower.context['page_obj'])
        self.authorized_client.force_login(self.unfollowed_user)
        response_unfollower = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        self.assertNotIn(
            self.one_post,
            response_unfollower.context['page_obj']
        )
