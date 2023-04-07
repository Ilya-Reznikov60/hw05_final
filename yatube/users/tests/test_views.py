from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django import forms


User = get_user_model()


class UserPagesTests(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='test-author')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

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

    def test_signup_page_show_correct_context(self):
        """Шаблон signup сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('users:signup'))
        form_fields = {
            'first_name': forms.fields.CharField,
            'last_name': forms.fields.CharField,
            'username': forms.fields.CharField,
            'email': forms.fields.EmailField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)
                self.assertIsNone(form_field.initial)
