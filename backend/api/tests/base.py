import base64
import io

from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image
from rest_framework.test import APIClient, APITestCase

from recipes.models import Product, Recipe, RecipeProduct, Tag, User


def make_image_bytes():
    buffer = io.BytesIO()
    Image.new('RGB', (1, 1)).save(buffer, format='PNG')
    return buffer.getvalue()


IMAGE_BYTES = make_image_bytes()
BASE64_IMAGE = 'data:image/png;base64,' + base64.b64encode(
    IMAGE_BYTES
).decode()

USERS_URL = reverse('users-list')
ME_URL = reverse('users-me')
SUBSCRIPTIONS_URL = reverse('users-subscriptions')
TAGS_URL = reverse('tags-list')
INGREDIENTS_URL = reverse('ingredients-list')
RECIPES_URL = reverse('recipes-list')
DOWNLOAD_CART_URL = reverse('recipes-download-shopping-cart')


class BaseAPITestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create_user(
            email='frodo@shire.me',
            username='frodo',
            first_name='Фродо',
            last_name='Бэггинс',
            password='OneRing2026Rules',
        )
        cls.other = User.objects.create_user(
            email='luke@jedi.sw',
            username='luke',
            first_name='Люк',
            last_name='Скайуокер',
            password='UseTheForce2026',
        )
        cls.author_client = APIClient()
        cls.author_client.force_authenticate(cls.author)
        cls.other_client = APIClient()
        cls.other_client.force_authenticate(cls.other)
        cls.tag = Tag.objects.create(name='Завтрак', slug='breakfast')
        cls.product = Product.objects.create(
            name='Мука',
            measurement_unit='г',
        )
        cls.recipe = Recipe.objects.create(
            author=cls.author,
            name='Лембас эльфийский',
            text='Путевой хлеб эльфов.',
            cooking_time=10,
            image=SimpleUploadedFile(
                'test.png',
                IMAGE_BYTES,
                content_type='image/png',
            ),
        )
        cls.recipe.tags.set((cls.tag,))
        RecipeProduct.objects.create(
            recipe=cls.recipe,
            product=cls.product,
            amount=100,
        )
        cls.recipe_url = reverse('recipes-detail', args=(cls.recipe.id,))
        cls.favorite_url = reverse('recipes-favorite', args=(cls.recipe.id,))
        cls.cart_url = reverse(
            'recipes-shopping-cart',
            args=(cls.recipe.id,),
        )
        cls.get_link_url = reverse(
            'recipes-get-link',
            args=(cls.recipe.id,),
        )
        cls.subscribe_url = reverse('users-subscribe', args=(cls.other.id,))
        cls.recipe_data = {
            'ingredients': ({'id': cls.product.id, 'amount': 50},),
            'tags': (cls.tag.id,),
            'image': BASE64_IMAGE,
            'name': 'Похлёбка Сэма',
            'text': 'Сытная еда для долгого пути.',
            'cooking_time': 5,
        }
