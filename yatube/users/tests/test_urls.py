from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from http import HTTPStatus
from django.urls import reverse

User = get_user_model()


class UserURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='test-author')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls_exists_at_desired_location_guest(self):
        """Страницы, которые доступны любому пользователю."""
        url_names = (
            reverse('users:signup'),
            reverse('users:logout'),
            reverse('users:login'),
        )
        for adress in url_names:
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_exists_at_desired_location_guest_found(self):
        """Страницы, которые перенаправляют пользователя на смену пароля."""
        url_names = (
            reverse('users:password_change'),
            reverse('users:password_change_done'),
        )
        for adress in url_names:
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_exists_at_desired_location_authorized(self):
        """Страницы, которые доступны аторизованному пользователю."""
        url_names = (
            reverse('users:password_reset_form'),
            reverse('users:password_reset_done'),
            reverse('users:password_reset_confirm',
                    kwargs={'uidb64': 'uidb64', 'token': 'token'}),
            reverse('users:password_reset_complete')
        )
        for adress in url_names:
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        url_names_templates = {
            reverse('users:signup'): 'users/signup.html',
            reverse('users:login'): 'users/login.html',
            reverse('users:password_change'):
            'users/password_change_form.html',
            reverse('users:password_change_done'):
            'users/password_change_done.html',
            reverse('users:password_reset_form'):
            'users/password_reset_form.html',
            reverse('users:password_reset_done'):
            'users/password_reset_done.html',
            reverse('users:password_reset_confirm',
                    kwargs={'uidb64': 'uidb64', 'token': 'token'}):
                        'users/password_reset_confirm.html',
            reverse('users:password_reset_complete'):
            'users/password_reset_complete.html',
            reverse('users:logout'): 'users/logged_out.html',
        }
        for reverse_name, template in url_names_templates.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
