from http import HTTPStatus

from django.core.files.uploadedfile import SimpleUploadedFile

from api.tests.base import (
    DOWNLOAD_CART_URL,
    IMAGE_BYTES,
    INGREDIENTS_URL,
    RECIPES_URL,
    TAGS_URL,
    BaseAPITestCase,
)
from recipes.models import Favorite, Recipe


class TestContent(BaseAPITestCase):

    def test_recipe_list_has_pagination_keys(self):
        response = self.client.get(RECIPES_URL)
        for key in ('count', 'next', 'previous', 'results'):
            with self.subTest(key=key):
                self.assertIn(key, response.data)

    def test_recipe_detail_has_expected_fields(self):
        response = self.client.get(self.recipe_url)
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )
        for field in fields:
            with self.subTest(field=field):
                self.assertIn(field, response.data)

    def test_is_favorited_true_after_adding(self):
        Favorite.objects.create(user=self.author, recipe=self.recipe)
        response = self.author_client.get(self.recipe_url)
        self.assertTrue(response.data['is_favorited'])

    def test_filter_recipes_by_tag(self):
        response = self.client.get(RECIPES_URL, {'tags': self.tag.slug})
        self.assertEqual(response.data['count'], 1)

    def test_ingredient_search_by_name_start(self):
        response = self.client.get(INGREDIENTS_URL, {'name': 'Му'})
        names = [item['name'] for item in response.data]
        self.assertIn('Мука', names)

    def test_shopping_cart_download_sums_products(self):
        self.author_client.post(self.cart_url)
        response = self.author_client.get(DOWNLOAD_CART_URL)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        content = response.content.decode()
        self.assertIn('Мука', content)
        self.assertIn('100', content)

    def test_tags_list_has_expected_fields(self):
        response = self.client.get(TAGS_URL)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        for field in ('id', 'name', 'slug'):
            with self.subTest(field=field):
                self.assertIn(field, response.data[0])

    def test_get_link_returns_short_link(self):
        response = self.client.get(self.get_link_url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn('short-link', response.data)

    def test_pagination_respects_limit(self):
        Recipe.objects.create(
            author=self.author,
            name='Второй рецепт',
            text='Описание',
            cooking_time=5,
            image=SimpleUploadedFile('t.png', IMAGE_BYTES, 'image/png'),
        )
        response = self.client.get(RECIPES_URL, {'limit': 1})
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['count'], 2)
