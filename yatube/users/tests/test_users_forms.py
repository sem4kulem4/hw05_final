from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()

    def test_create_new_user_after_signup_correct(self):
        users_count = User.objects.count()
        new_user_data = {
            'first_name': 'test_name',
            'last_name': 'test_surname',
            'username': 'test_user1',
            'email': 'test_user@django.ru',
            'password1': 'qwesdffhj2022',
            'password2': 'qwesdffhj2022',
        }
        self.guest_client.post(
            reverse('users:signup'),
            data=new_user_data,
            follow=True
        )
        self.assertEqual(User.objects.count(), users_count + 1)
