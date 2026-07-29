from http import HTTPStatus

from api.tests.base import (
    DOWNLOAD_CART_URL,
    INGREDIENTS_URL,
    ME_URL,
    RECIPES_URL,
    SUBSCRIPTIONS_URL,
    TAGS_URL,
    USERS_URL,
    BaseAPITestCase,
)

OK = HTTPStatus.OK
UNAUTHORIZED = HTTPStatus.UNAUTHORIZED


class TestRoutes(BaseAPITestCase):

    def test_public_pages_available_for_anonymous(self):
        urls = (
            RECIPES_URL,
            TAGS_URL,
            INGREDIENTS_URL,
            USERS_URL,
            self.recipe_url,
            self.get_link_url,
        )
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, OK)

    def test_private_pages_require_authentication(self):
        urls = (ME_URL, SUBSCRIPTIONS_URL, DOWNLOAD_CART_URL)
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(
                    self.client.get(url).status_code,
                    UNAUTHORIZED,
                )

    def test_private_pages_available_for_authenticated(self):
        urls = (ME_URL, SUBSCRIPTIONS_URL, DOWNLOAD_CART_URL)
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(
                    self.author_client.get(url).status_code,
                    OK,
                )

    def test_api_docs_available(self):
        self.assertEqual(self.client.get('/api/docs/').status_code, OK)
