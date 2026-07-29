import base64
from http import HTTPStatus
from io import BytesIO

from django.urls import reverse
from PIL import Image

from api.fields import MAX_IMAGE_SIDE
from api.tests.base import (
    AVATAR_URL,
    BASE64_IMAGE,
    RECIPES_URL,
    BaseAPITestCase,
)
from recipes.models import Favorite, Recipe, ShoppingCart, Subscription


class TestRecipeCreate(BaseAPITestCase):

    def test_author_can_create_recipe(self):
        Recipe.objects.all().delete()
        response = self.author_client.post(
            RECIPES_URL,
            self.recipe_data,
            format='json',
        )
        self.assertEqual(response.status_code, HTTPStatus.CREATED)
        self.assertEqual(Recipe.objects.count(), 1)
        recipe = Recipe.objects.get()
        self.assertEqual(recipe.name, self.recipe_data['name'])
        self.assertEqual(recipe.text, self.recipe_data['text'])
        self.assertEqual(
            recipe.cooking_time,
            self.recipe_data['cooking_time'],
        )
        self.assertEqual(recipe.author, self.author)

    def test_anonymous_cannot_create_recipe(self):
        count = Recipe.objects.count()
        response = self.client.post(
            RECIPES_URL,
            self.recipe_data,
            format='json',
        )
        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED)
        self.assertEqual(Recipe.objects.count(), count)

    def test_create_without_tags_fails(self):
        count = Recipe.objects.count()
        response = self.author_client.post(
            RECIPES_URL,
            {**self.recipe_data, 'tags': ()},
            format='json',
        )
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
        self.assertEqual(Recipe.objects.count(), count)

    def test_create_without_ingredients_fails(self):
        count = Recipe.objects.count()
        response = self.author_client.post(
            RECIPES_URL,
            {**self.recipe_data, 'ingredients': ()},
            format='json',
        )
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
        self.assertEqual(Recipe.objects.count(), count)

    def test_create_with_duplicate_ingredients_fails(self):
        response = self.author_client.post(
            RECIPES_URL,
            {
                **self.recipe_data,
                'ingredients': (
                    {'id': self.product.id, 'amount': 1},
                    {'id': self.product.id, 'amount': 2},
                ),
            },
            format='json',
        )
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

    def test_create_with_cooking_time_below_one_fails(self):
        response = self.author_client.post(
            RECIPES_URL,
            {**self.recipe_data, 'cooking_time': 0},
            format='json',
        )
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

    def test_big_uploaded_image_is_compressed(self):
        buffer = BytesIO()
        Image.new('RGB', (2000, 2000)).save(buffer, format='PNG')
        big_image = 'data:image/png;base64,' + base64.b64encode(
            buffer.getvalue()
        ).decode()
        self.author_client.post(
            RECIPES_URL,
            {**self.recipe_data, 'image': big_image},
            format='json',
        )
        recipe = Recipe.objects.latest('pub_date')
        with Image.open(recipe.image.path) as image:
            self.assertLessEqual(max(image.size), MAX_IMAGE_SIDE)


class TestRecipeEditDelete(BaseAPITestCase):

    def test_author_can_edit_own_recipe(self):
        response = self.author_client.patch(
            self.recipe_url,
            {**self.recipe_data, 'name': 'Обновлённый'},
            format='json',
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.name, 'Обновлённый')

    def test_other_user_cannot_edit_recipe(self):
        response = self.other_client.patch(
            self.recipe_url,
            self.recipe_data,
            format='json',
        )
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.name, 'Лембас эльфийский')

    def test_anonymous_cannot_edit_recipe(self):
        response = self.client.patch(
            self.recipe_url,
            self.recipe_data,
            format='json',
        )
        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED)

    def test_author_can_delete_own_recipe(self):
        response = self.author_client.delete(self.recipe_url)
        self.assertEqual(response.status_code, HTTPStatus.NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=self.recipe.id).exists())

    def test_other_user_cannot_delete_recipe(self):
        response = self.other_client.delete(self.recipe_url)
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertTrue(Recipe.objects.filter(id=self.recipe.id).exists())


class TestFavorite(BaseAPITestCase):

    def test_add_recipe_to_favorite(self):
        response = self.author_client.post(self.favorite_url)
        self.assertEqual(response.status_code, HTTPStatus.CREATED)
        self.assertTrue(
            Favorite.objects.filter(
                user=self.author,
                recipe=self.recipe,
            ).exists()
        )

    def test_add_to_favorite_twice_fails(self):
        self.author_client.post(self.favorite_url)
        response = self.author_client.post(self.favorite_url)
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

    def test_remove_recipe_from_favorite(self):
        Favorite.objects.create(user=self.author, recipe=self.recipe)
        response = self.author_client.delete(self.favorite_url)
        self.assertEqual(response.status_code, HTTPStatus.NO_CONTENT)
        self.assertFalse(
            Favorite.objects.filter(
                user=self.author,
                recipe=self.recipe,
            ).exists()
        )

    def test_anonymous_cannot_favorite(self):
        response = self.client.post(self.favorite_url)
        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED)


class TestShoppingCart(BaseAPITestCase):

    def test_add_recipe_to_cart(self):
        response = self.author_client.post(self.cart_url)
        self.assertEqual(response.status_code, HTTPStatus.CREATED)
        self.assertTrue(
            ShoppingCart.objects.filter(
                user=self.author,
                recipe=self.recipe,
            ).exists()
        )

    def test_add_to_cart_twice_fails(self):
        self.author_client.post(self.cart_url)
        response = self.author_client.post(self.cart_url)
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

    def test_remove_recipe_from_cart(self):
        ShoppingCart.objects.create(user=self.author, recipe=self.recipe)
        response = self.author_client.delete(self.cart_url)
        self.assertEqual(response.status_code, HTTPStatus.NO_CONTENT)
        self.assertFalse(
            ShoppingCart.objects.filter(
                user=self.author,
                recipe=self.recipe,
            ).exists()
        )

    def test_anonymous_cannot_add_to_cart(self):
        response = self.client.post(self.cart_url)
        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED)


class TestSubscription(BaseAPITestCase):

    def test_subscribe_to_other_user(self):
        response = self.author_client.post(self.subscribe_url)
        self.assertEqual(response.status_code, HTTPStatus.CREATED)
        self.assertTrue(
            Subscription.objects.filter(
                user=self.author,
                author=self.other,
            ).exists()
        )

    def test_cannot_subscribe_to_self(self):
        response = self.author_client.post(
            reverse('users-subscribe', args=(self.author.id,))
        )
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

    def test_cannot_subscribe_twice(self):
        self.author_client.post(self.subscribe_url)
        response = self.author_client.post(self.subscribe_url)
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

    def test_unsubscribe_from_user(self):
        Subscription.objects.create(user=self.author, author=self.other)
        response = self.author_client.delete(self.subscribe_url)
        self.assertEqual(response.status_code, HTTPStatus.NO_CONTENT)
        self.assertFalse(
            Subscription.objects.filter(
                user=self.author,
                author=self.other,
            ).exists()
        )

    def test_anonymous_cannot_subscribe(self):
        response = self.client.post(self.subscribe_url)
        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED)


class TestAvatar(BaseAPITestCase):

    def test_set_avatar(self):
        response = self.author_client.put(
            AVATAR_URL,
            {'avatar': BASE64_IMAGE},
            format='json',
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn('avatar', response.data)

    def test_delete_avatar(self):
        self.author_client.put(
            AVATAR_URL,
            {'avatar': BASE64_IMAGE},
            format='json',
        )
        response = self.author_client.delete(AVATAR_URL)
        self.assertEqual(response.status_code, HTTPStatus.NO_CONTENT)
