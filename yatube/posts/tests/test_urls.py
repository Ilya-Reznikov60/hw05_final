from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from http import HTTPStatus
from django.urls import reverse
from django.core.cache import cache

from ..models import Group, Post

from posts.tests.constants import (
    INDEX_URL_NAME,
    GROUP_LIST_URL_NAME,
    PROFILE_URL_NAME,
    POST_DETAIL_URL_NAME,
    POST_EDIT_URL_NAME,
    POST_CREATE_POST_URL_NAME,
    INDEX_TEMPLATE,
    GROUP_LIST_TEMPLATE,
    PROFILE_TEMPLATE,
    POST_DETAIL_TEMPLATE,
    POST_EDIT_TEMPLATE,
    POST_CREATE_TEMPLATE,
    AUTHOR_USERNAME,
    GROUP_TITLE,
    GROUP_SLUG,
    GROUP_DESCRIPTION,
    POST_TEXT,
    NO_AUTHOR_USERNAME,
)


User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=AUTHOR_USERNAME)
        cls.group = Group.objects.create(
            title=GROUP_TITLE,
            slug=GROUP_SLUG,
            description=GROUP_DESCRIPTION,
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text=POST_TEXT,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.no_author = User.objects.create_user(
            username=NO_AUTHOR_USERNAME)
        self.no_author_client = Client()
        self.no_author_client.force_login(self.no_author)
        cache.clear()

    def test_urls_exists_at_desired_location_guest(self):
        """Страницы, которые доступны любому пользователю"""
        url_names = {
            INDEX_URL_NAME: ({}),
            GROUP_LIST_URL_NAME: (
                {'slug': self.group.slug}
            ),
            PROFILE_URL_NAME: (
                {'username': self.user.username}
            ),
            POST_DETAIL_URL_NAME: (
                {'post_id': self.post.pk}
            ),
        }
        for adress, params in url_names.items():
            kwargs = params
            with self.subTest(adress=adress):
                response = self.guest_client.get(
                    reverse(adress, kwargs=kwargs))
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_exists_at_desired_location_authorized(self):
        """Страница 'posts:post_create' доступна авторизованному пользователю,
        страница 'posts:post_edit' доступна автору поста."""
        url_names = {
            POST_CREATE_POST_URL_NAME: (
                {}
            ),
            POST_EDIT_URL_NAME: (
                {'post_id': self.post.pk}
            ),
        }
        for adress, params in url_names.items():
            kwargs = params
            with self.subTest(adress=adress):
                response = self.authorized_client.get(
                    reverse(adress, kwargs=kwargs))
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unexisting_page_return_404(self):
        """Страница /unexisting_page/ не существует."""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_redirect_anonymous_on_login_page(self):
        """Страницы, которые перенаправят анонимного пользователя
        на страницу логина."""
        url_names = {
            POST_CREATE_POST_URL_NAME: (
                {}
            ),
            POST_EDIT_URL_NAME: (
                {'post_id': self.post.pk}
            ),
        }
        for adress, params in url_names.items():
            kwargs = params
            with self.subTest(adress=adress):
                response = self.guest_client.get(
                    reverse(adress, kwargs=kwargs), follow=True)
                self.assertRedirects(
                    response, reverse('users:login')
                    + '?next=' + reverse(adress, kwargs=kwargs)
                )

    def test_post_edit_url_redirect_no_author_authorized(self):
        """Страница 'posts:post_edit' перенаправляет
        авторизованного пользователя,не являющегося автором поста
          на страницу 'posts:post_detail'"""
        url_patterns = {
            POST_EDIT_URL_NAME: (
                {'post_id': self.post.pk}
            )
        }
        for url_name, params in url_patterns.items():
            with self.subTest(url_name=url_name):
                kwargs = params
        response = self.no_author_client.get(
            reverse(url_name, kwargs=kwargs), follow=True)
        url_patterns = {
            POST_DETAIL_URL_NAME: (
                {'post_id': self.post.pk}
            )
        }
        for url_name, params in url_patterns.items():
            with self.subTest(url_name=url_name):
                kwargs = params
                self.assertRedirects(
                    response, reverse(url_name, kwargs=kwargs))

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        url_names_templates = {
            INDEX_URL_NAME: (
                INDEX_TEMPLATE,
                {}
            ),
            GROUP_LIST_URL_NAME: (
                GROUP_LIST_TEMPLATE,
                {'slug': self.group.slug}
            ),
            PROFILE_URL_NAME: (
                PROFILE_TEMPLATE,
                {'username': self.user.username}
            ),
            POST_DETAIL_URL_NAME: (
                POST_DETAIL_TEMPLATE,
                {'post_id': self.post.pk}
            ),
            POST_EDIT_URL_NAME: (
                POST_EDIT_TEMPLATE,
                {'post_id': self.post.pk}
            ),
            POST_CREATE_POST_URL_NAME: (
                POST_CREATE_TEMPLATE,
                {}
            ),
        }
        for adress, params in url_names_templates.items():
            template, kwargs = params
            with self.subTest(adress=adress):
                response = self.authorized_client.get(
                    reverse(adress, kwargs=kwargs))
                self.assertTemplateUsed(response, template)
