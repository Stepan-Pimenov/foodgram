import io

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from PIL import Image

from recipes.models import Product, Recipe, RecipeProduct, Tag

User = get_user_model()

PASSWORD = 'TestUser2026'

ADMIN = {
    'email': 'admin@email.ru',
    'username': 'admin',
    'first_name': 'Admin',
    'last_name': 'Admin',
    'password': 'admin',
}

USERS = (
    ('gandalf@middleearth.me', 'gandalf', 'Гэндальф', 'Серый'),
    ('yoda@jedi.sw', 'yoda', 'Йода', 'Магистр'),
    ('aragorn@gondor.me', 'aragorn', 'Арагорн', 'Элессар'),
)

RECIPES = (
    ('Лембас эльфийский', 'Путевой хлеб эльфов.', 15),
    ('Похлёбка Сэма', 'Сытная еда для долгого пути в Мордор.', 40),
    ('Синий коктейль с Татуина', 'Освежающий напиток джедая.', 5),
)

COLORS = (
    (198, 93, 76),
    (76, 120, 198),
    (120, 160, 90),
)


class Command(BaseCommand):
    help = 'Создаёт тестовых пользователей и рецепты'

    def handle(self, *args, **options):
        if not Product.objects.exists() or not Tag.objects.exists():
            self.stdout.write(self.style.ERROR(
                'Нет продуктов/тегов - сначала выполните import_data.'
            ))
            return
        self.create_admin()
        tags = list(Tag.objects.all())
        products = list(Product.objects.all()[:3])
        for user_data, recipe_data, color in zip(USERS, RECIPES, COLORS):
            user = self.create_user(*user_data)
            self.create_recipe(user, recipe_data, tags, products, color)
        self.stdout.write(self.style.SUCCESS('Тестовые данные готовы.'))

    def create_admin(self):
        if not User.objects.filter(username=ADMIN['username']).exists():
            User.objects.create_superuser(**ADMIN)

    def create_user(self, email, username, first_name, last_name):
        user, _ = User.objects.get_or_create(
            username=username,
            defaults={
                'email': email,
                'first_name': first_name,
                'last_name': last_name,
            },
        )
        user.set_password(PASSWORD)
        user.save()
        return user

    def create_recipe(self, author, recipe_data, tags, products, color):
        if Recipe.objects.filter(author=author).exists():
            return
        name, text, cooking_time = recipe_data
        recipe = Recipe.objects.create(
            author=author,
            name=name,
            text=text,
            cooking_time=cooking_time,
            image=ContentFile(
                self.image_bytes(color),
                name=f'{author.username}.png',
            ),
        )
        recipe.tags.set(tags[:2])
        RecipeProduct.objects.bulk_create(
            RecipeProduct(recipe=recipe, product=product, amount=100)
            for product in products
        )

    def image_bytes(self, color):
        buffer = io.BytesIO()
        Image.new('RGB', (300, 300), color).save(buffer, format='PNG')
        return buffer.getvalue()
