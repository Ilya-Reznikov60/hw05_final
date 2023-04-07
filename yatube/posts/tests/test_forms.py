import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from ..forms import PostForm
from ..models import Post, Group, Comment

from posts.tests.constants import (
    PROFILE_URL_NAME,
    POST_DETAIL_URL_NAME,
    POST_EDIT_URL_NAME,
    POST_CREATE_POST_URL_NAME,
    AUTHOR_USERNAME,
    GROUP_TITLE,
    GROUP_SLUG,
    GROUP_DESCRIPTION,
    POST_TEXT,
    ADD_COMMENT_POST_URL_NAME,
)


User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
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
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        posts_count = Post.objects.count()
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
        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.pk,
            'image': uploaded,
        }
        url_patterns = {
            POST_CREATE_POST_URL_NAME: ({})
        }
        for url_name, params in url_patterns.items():
            with self.subTest(url_name=url_name):
                kwargs = params
        response = self.authorized_client.post(
            reverse(url_name, kwargs=kwargs),
            data=form_data,
            follow=True
        )
        url_patterns = {
            PROFILE_URL_NAME: (
                {'username': self.user.username}
            )
        }
        for url_name, params in url_patterns.items():
            with self.subTest(url_name=url_name):
                kwargs = params
        self.assertRedirects(
            response,
            reverse(
                url_name, kwargs=kwargs
            ))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                group=form_data['group'],
                author=self.user,
                image='posts/small.gif'
            ).exists()
        )

    def test_edit_post(self):
        """валидная форма изменяет Post
          с post_id в базе данных."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'ещё один тестовый текст',
            'group': self.group.pk,
        }
        url_patterns = {
            POST_EDIT_URL_NAME: (
                {'post_id': self.post.pk}
            )
        }
        for url_name, params in url_patterns.items():
            with self.subTest(url_name=url_name):
                kwargs = params
        response = self.authorized_client.post(
            reverse(url_name, kwargs=kwargs),
            data=form_data,
            follow=True
        )
        url_patterns = {
            POST_DETAIL_URL_NAME: (
                {'post_id': self.post.pk}
            )
        }
        for url_name, params in url_patterns.items():
            with self.subTest(url_name=url_name):
                kwargs = params
        self.assertRedirects(
            response,
            reverse(url_name, kwargs=kwargs)
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                group=form_data['group'],
                author=self.user,
            ).exists()
        )

    def test_form_create_comment(self):
        """Валидная форма создает Comment."""
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый комментарий',
        }
        url_patterns = {
            ADD_COMMENT_POST_URL_NAME: (
                {'post_id': self.post.pk}
            )
        }
        for url_name, params in url_patterns.items():
            with self.subTest(url_name=url_name):
                kwargs = params
        response = self.authorized_client.post(
            reverse(url_name, kwargs=kwargs),
            data=form_data,
            follow=True
        )
        url_patterns = {
            POST_DETAIL_URL_NAME: (
                {'post_id': self.post.pk}
            )
        }
        for url_name, params in url_patterns.items():
            with self.subTest(url_name=url_name):
                kwargs = params
                self.assertRedirects(
                    response,
                    reverse(url_name, kwargs=kwargs)
                )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertTrue(
            Comment.objects.filter(
                text=form_data['text'],
                author=self.user,
                post=self.post
            ).exists()
        )
