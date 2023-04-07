from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse


User = get_user_model()


class UserCreateFormTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_signup_form(self):
        """Валидная форма создает нового пользователя."""
        users_count = User.objects.count()
        form_data = {
            'first_name': 'test-name',
            'last_name': 'test-last-name',
            'username': 'test-user',
            'email': 'test@mail.ru',
            'password1': 'Testpassword123',
            'password2': 'Testpassword123',
        }
        response = self.guest_client.post(
            reverse('users:signup'),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response, reverse('posts:index'))
        self.assertEqual(User.objects.count(), users_count + 1)
