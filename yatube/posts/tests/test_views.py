import shutil
import tempfile

from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django import forms
from django.core.paginator import Page
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.core.cache import cache
from django.db.models.fields.files import ImageFieldFile

from ..models import Group, Post, Comment, Follow

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
    GROUP_TITLE_2,
    GROUP_SLUG_2,
    GROUP_DESCRIPTION_2,
    POST_TEXT_2,
    PROFILE_FOLLOW_URL_NAME,
    FOLLOW_AUTHOR_USERNAME,
    PROFILE_UNFOLLOW_URL_NAME,
    PROFILE_FOLLOW_INDEX_URL_NAME,
    NO_FOLLOW_AUTHOR_USERNAME,
)

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=AUTHOR_USERNAME)
        cls.group = Group.objects.create(
            title=GROUP_TITLE,
            slug=GROUP_SLUG,
            description=GROUP_DESCRIPTION,
        )
        TEST_COUNT = 10
        posts = (
            Post(
                author=cls.user,
                text=f'{POST_TEXT}-{i}',
                group=cls.group)
            for i in range(TEST_COUNT))
        Post.objects.bulk_create(posts)
        cls.post = Post.objects.create(
            author=cls.user,
            text=POST_TEXT,
            group=cls.group,
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post.image = uploaded
        cls.post.save()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_page_names = {
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
        for reverse_name, params in templates_page_names.items():
            with self.subTest(reverse_name=reverse_name):
                template, kwargs = params
                response = self.authorized_client.get(
                    reverse(reverse_name, kwargs=kwargs))
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)

    def test_create_post_page_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        url_patterns = {
            POST_CREATE_POST_URL_NAME: ({})
        }
        for url_name, params in url_patterns.items():
            with self.subTest(url_name=url_name):
                kwargs = params
        response = self.authorized_client.get(
            reverse(url_name, kwargs=kwargs))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        url_patterns = {
            POST_EDIT_URL_NAME: (
                {'post_id': self.post.pk}
            )
        }
        for url_name, params in url_patterns.items():
            with self.subTest(url_name=url_name):
                kwargs = params
        response = self.authorized_client.get(
            reverse(url_name, kwargs=kwargs)
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        url_patterns = {
            POST_DETAIL_URL_NAME: (
                {'post_id': self.post.pk}
            )
        }
        for url_name, params in url_patterns.items():
            with self.subTest(url_name=url_name):
                kwargs = params
                response = self.authorized_client.get(
                    reverse(url_name, kwargs=kwargs)
                )
                self.assertEqual(
                    response.context['post'].text, self.post.text
                )
                self.assertEqual(
                    response.context['post'].author, self.post.author
                )
                self.assertEqual(
                    response.context['post'].group, self.post.group
                )
                self.assertEqual(
                    response.context['post'].image, self.post.image
                )

    def test_patterns_show_correct_context(self):
        """Шаблоны index, group_list, profile
        сформированы с правильным контекстом."""
        urls_expected_post_number = {
            INDEX_URL_NAME: (
                {},
                Post.objects.all()[:10]
            ),
            GROUP_LIST_URL_NAME: (
                {'slug': self.group.slug},
                self.group.posts.all()[:10]
            ),
            PROFILE_URL_NAME: (
                {'username': self.user.username},
                self.user.posts.all()[:10]
            )
        }
        for url_name, params in urls_expected_post_number.items():
            kwargs, queryset = params
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name, kwargs=kwargs))
                self.assertEqual(response.status_code, HTTPStatus.OK)
                page_obj = response.context.get('page_obj')
                self.assertIsNotNone(page_obj)
                self.assertIsInstance(page_obj, Page)
                self.assertQuerysetEqual(
                    page_obj, queryset, lambda x: x
                )

    def test_new_post_with_group_in_correct_pages(self):
        """Новый пост с группой отображается на правильных страницах"""
        new_group = Group.objects.create(
            title=GROUP_TITLE_2,
            slug=GROUP_SLUG_2,
            description=GROUP_DESCRIPTION_2,
        )
        new_post = Post.objects.create(
            author=self.user,
            text=POST_TEXT_2,
            group=new_group,
        )
        url_patterns = {
            INDEX_URL_NAME: (
                {}
            )
        }
        for url_name, params in url_patterns.items():
            with self.subTest(url_name=url_name):
                kwargs = params
        response = self.authorized_client.get(
            reverse(url_name, kwargs=kwargs)
        )
        self.assertIn(new_post, response.context['page_obj'])
        url_patterns = {
            GROUP_LIST_URL_NAME: (
                {'slug': new_group.slug}
            )
        }
        for url_name, params in url_patterns.items():
            with self.subTest(url_name=url_name):
                kwargs = params
        response = self.authorized_client.get(
            reverse(url_name, kwargs=kwargs)
        )
        self.assertIn(new_post, response.context['page_obj'])
        url_patterns = {
            GROUP_LIST_URL_NAME: (
                {'slug': self.group.slug}
            )
        }
        for url_name, params in url_patterns.items():
            with self.subTest(url_name=url_name):
                kwargs = params
        response = self.authorized_client.get(
            reverse(url_name, kwargs=kwargs)
        )
        self.assertNotIn(new_post, response.context['page_obj'])
        url_patterns = {
            PROFILE_URL_NAME: (
                {'username': self.user.username}
            )
        }
        for url_name, params in url_patterns.items():
            with self.subTest(url_name=url_name):
                kwargs = params
        response = self.authorized_client.get(
            reverse(url_name, kwargs=kwargs)
        )
        self.assertIn(new_post, response.context['page_obj'])


class ImagePostTests(TestCase):
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
            group=cls.group,
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post.image = uploaded
        cls.post.save()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_image_post_in_context(self):
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        url_patterns = {
            POST_DETAIL_URL_NAME: (
                {'post_id': self.post.pk}
            )
        }
        for url_name, params in url_patterns.items():
            with self.subTest(url_name=url_name):
                kwargs = params
        response = self.authorized_client.get(
            reverse(url_name, kwargs=kwargs)
        )
        image = response.context['post'].image
        self.assertIsInstance(image, ImageFieldFile)
        self.assertEqual(image.file.read(), small_gif)


class CommentPostTests(TestCase):
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
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_post_detail_show_new_comment(self):
        """Шаблон post_detail отображает новый комментарий
           авторизованному пользователю."""
        comment = Comment.objects.create(
            post=self.post,
            author=self.user,
            text='Тестовый комментарий',
        )
        url_patterns = {
            POST_DETAIL_URL_NAME: (
                {'post_id': self.post.pk}
            )
        }
        for url_name, params in url_patterns.items():
            with self.subTest(url_name=url_name):
                kwargs = params
        response = self.authorized_client.get(
            reverse(url_name, kwargs=kwargs)
        )
        self.assertIn(comment, response.context['comments'])


class CacheIndexTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=AUTHOR_USERNAME)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_cache_work_at_index(self):
        """Проверяем корректность работы кэша."""
        post_cache = Post.objects.create(
            author=self.user,
            text='Тестовый пост в кэше',
        )
        url_patterns = {
            INDEX_URL_NAME: (
                {}
            )
        }
        for url_name, params in url_patterns.items():
            with self.subTest(url_name=url_name):
                kwargs = params
        response = self.authorized_client.get(
            reverse(url_name, kwargs=kwargs)
        )
        post_cache.delete()
        url_patterns = {
            INDEX_URL_NAME: (
                {}
            )
        }
        for url_name, params in url_patterns.items():
            with self.subTest(url_name=url_name):
                kwargs = params
        new_response = self.authorized_client.get(
            reverse(url_name, kwargs=kwargs)
        )
        self.assertEqual(response.content, new_response.content)


class FollowViewsTests(TestCase):
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
            group=cls.group,
        )
        cls.follow_author = User.objects.create_user(
            username=FOLLOW_AUTHOR_USERNAME)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_follow_author(self):
        """Авторизованный пользователь
        может подписываться на других пользователей."""
        url_patterns = {
            PROFILE_FOLLOW_URL_NAME: (
                {'username': self.follow_author.username}
            )
        }
        for url_name, params in url_patterns.items():
            with self.subTest(url_name=url_name):
                kwargs = params
        self.authorized_client.get(
            reverse(url_name, kwargs=kwargs)
        )
        self.assertTrue(Follow.objects.filter(
            user=self.user, author=self.follow_author
        ).exists()
        )

    def test_unfollow_author(self):
        """Авторизованный пользователь
        может удалять авторов из подписок."""
        url_patterns = {
            PROFILE_FOLLOW_URL_NAME: (
                {'username': self.follow_author.username}
            )
        }
        for url_name, params in url_patterns.items():
            with self.subTest(url_name=url_name):
                kwargs = params
        self.authorized_client.get(
            reverse(url_name, kwargs=kwargs)
        )
        url_patterns = {
            PROFILE_UNFOLLOW_URL_NAME: (
                {'username': self.follow_author.username}
            )
        }
        for url_name, params in url_patterns.items():
            with self.subTest(url_name=url_name):
                kwargs = params
        self.authorized_client.get(
            reverse(url_name, kwargs=kwargs)
        )
        self.assertFalse(Follow.objects.filter(
            user=self.user, author=self.follow_author
        ).exists()
        )

    def test_new_post_in_follow_pages(self):
        """Новая запись пользователя появляется в ленте тех,
           кто на него подписан"""
        url_patterns = {
            PROFILE_FOLLOW_URL_NAME: (
                {'username': self.follow_author.username}
            )
        }
        for url_name, params in url_patterns.items():
            with self.subTest(url_name=url_name):
                kwargs = params
        self.authorized_client.get(
            reverse(url_name, kwargs=kwargs)
        )
        new_author_post = Post.objects.create(
            author=self.follow_author,
            text=POST_TEXT,
        )
        url_patterns = {
            PROFILE_FOLLOW_INDEX_URL_NAME: (
                {}
            )
        }
        for url_name, params in url_patterns.items():
            with self.subTest(url_name=url_name):
                kwargs = params
        response = self.authorized_client.get(
            reverse(url_name, kwargs=kwargs)
        )
        self.assertIn(new_author_post, response.context['page_obj'])

    def test_new_post_no_in_unfollow_page(self):
        """Новая запись пользователя не появляется в ленте тех,
           кто на него не подписан"""
        new_author_post = Post.objects.create(
            author=self.follow_author,
            text=POST_TEXT,
        )
        no_folower_author = User.objects.create_user(
            username=NO_FOLLOW_AUTHOR_USERNAME)
        no_follow_authorized_client = Client()
        no_follow_authorized_client.force_login(no_folower_author)
        url_patterns = {
            PROFILE_FOLLOW_INDEX_URL_NAME: (
                {}
            )
        }
        for url_name, params in url_patterns.items():
            with self.subTest(url_name=url_name):
                kwargs = params
        response = no_follow_authorized_client.get(
            reverse(url_name, kwargs=kwargs)
        )
        self.assertNotIn(new_author_post, response.context['page_obj'])

    class PaginatorViewsTest(TestCase):
        @classmethod
        def setUpClass(cls):
            super().setUpClass()
            cls.user = User.objects.create_user(username=AUTHOR_USERNAME)
            cls.group = Group.objects.create(
                title=GROUP_TITLE,
                slug=GROUP_SLUG,
                description=GROUP_DESCRIPTION,
            )
            TEST_COUNT_POST = 13
            posts = (Post(
                author=cls.user,
                text=f'{POST_TEXT}-{i}',
                group=cls.group)
                for i in range(TEST_COUNT_POST)
            )
            Post.objects.bulk_create(posts)

        def setUp(self):
            self.guest_client = Client()
            self.authorized_client = Client()
            self.authorized_client.force_login(self.user)

        def test_pages_contains_ten_and_three_records(self):
            """Шаблоны index, group_list, profile передают
            необходимое количество постов на страницу"""
            pages_name = {
                INDEX_URL_NAME: (
                    {}
                ),
                GROUP_LIST_URL_NAME: (
                    {'slug': self.group.slug}
                ),
                PROFILE_URL_NAME: (
                    {'username': self.user.username}
                ),
            }
            for reverse_name, params in pages_name:
                kwargs = params
                with self.subTest(reverse_name=reverse_name):
                    response = self.authorized_client.get(
                        reverse(reverse_name, kwargs=kwargs))
                    self.assertEqual(len(response.context['page_obj'], 10))
                    response = self.authorized_client.get(
                        reverse(reverse_name, kwargs=kwargs) + '?page=2')
                    self.assertEqual(len(response.context['page_obj', 3]))
