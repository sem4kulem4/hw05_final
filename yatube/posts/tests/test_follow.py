import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.cache import cache
from django.test import Client, TestCase
from django.test import override_settings
from django.urls import reverse

from posts.models import Comment, Follow, Group, Post

User = get_user_model()

FIRST_PAGE_POSTS = 10
SECOND_PAGE_POSTS = 4
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
            text='Тестовый пост'
        )
        cls.sub = Follow.objects.create(user=cls.follower, author=cls.author)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.follower)

    def test_follow_for_authorized(self):
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertIn(self.one_post, response.context['page_obj'])

    def test_unfollow_for_authorized(self):
        self.sub.delete()
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertNotIn(self.one_post, response.context['page_obj'])

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
