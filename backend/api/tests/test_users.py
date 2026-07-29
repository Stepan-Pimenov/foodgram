from http import HTTPStatus

from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from api.tests.base import (
    LOGIN_URL,
    LOGOUT_URL,
    ME_URL,
    SET_PASSWORD_URL,
    USERS_URL,
    BaseAPITestCase,
)
from recipes.models import User


class TestRegistration(BaseAPITestCase):

    def setUp(self):
        self.new_user = {
            'email': 'sam@shire.me',
            'username': 'sam',
            'first_name': 'Сэм',
            'last_name': 'Гэмджи',
            'password': 'PotatoesBoil2026',
        }

    def test_registration_creates_user(self):
        count = User.objects.count()
        response = self.client.post(USERS_URL, self.new_user, format='json')
        self.assertEqual(response.status_code, HTTPStatus.CREATED)
        self.assertEqual(User.objects.count(), count + 1)
        self.assertTrue(User.objects.filter(username='sam').exists())

    def test_registration_response_hides_password(self):
        response = self.client.post(USERS_URL, self.new_user, format='json')
        self.assertNotIn('password', response.data)

    def test_registration_without_email_fails(self):
        count = User.objects.count()
        self.new_user.pop('email')
        response = self.client.post(USERS_URL, self.new_user, format='json')
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
        self.assertEqual(User.objects.count(), count)

    def test_registration_duplicate_email_fails(self):
        self.new_user['email'] = self.author.email
        response = self.client.post(USERS_URL, self.new_user, format='json')
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)


class TestToken(BaseAPITestCase):

    def test_login_returns_token(self):
        response = self.client.post(
            LOGIN_URL,
            {'email': self.author.email, 'password': 'OneRing2026Rules'},
            format='json',
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn('auth_token', response.data)

    def test_login_wrong_password_fails(self):
        response = self.client.post(
            LOGIN_URL,
            {'email': self.author.email, 'password': 'wrong-password'},
            format='json',
        )
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

    def test_logout_deletes_token(self):
        token = Token.objects.create(user=self.other)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        response = client.post(LOGOUT_URL)
        self.assertEqual(response.status_code, HTTPStatus.NO_CONTENT)
        self.assertFalse(Token.objects.filter(user=self.other).exists())


class TestPassword(BaseAPITestCase):

    def test_set_password_success(self):
        response = self.author_client.post(
            SET_PASSWORD_URL,
            {
                'new_password': 'BrandNewPass2026',
                'current_password': 'OneRing2026Rules',
            },
            format='json',
        )
        self.assertEqual(response.status_code, HTTPStatus.NO_CONTENT)

    def test_set_password_wrong_current_fails(self):
        response = self.author_client.post(
            SET_PASSWORD_URL,
            {
                'new_password': 'BrandNewPass2026',
                'current_password': 'wrong-password',
            },
            format='json',
        )
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)


class TestUserProfile(BaseAPITestCase):

    def test_me_returns_current_user(self):
        response = self.author_client.get(ME_URL)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.data['email'], self.author.email)

    def test_user_detail_public(self):
        response = self.client.get(self.author_url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.data['username'], self.author.username)

    def test_user_has_expected_fields(self):
        response = self.client.get(self.author_url)
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )
        for field in fields:
            with self.subTest(field=field):
                self.assertIn(field, response.data)
