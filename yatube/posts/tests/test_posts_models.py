from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post


User = get_user_model()

CUT_OFF = 15

class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост, который должен быть больше 15 символов',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        group = PostModelTest.group
        post = PostModelTest.post
        values = (
            (group.title, str(group)),
            (post.text[:CUT_OFF], str(post)),
            (post._meta.get_field('text').help_text, 'Введите текст поста'),
            (post._meta.get_field('text').verbose_name, 'Текст'),
        )
        for val, expected in values:
            with self.subTest(val=val):
                self.assertEqual(val, expected)
