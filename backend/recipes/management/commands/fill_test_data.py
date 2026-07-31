from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from recipes.models import Product, Recipe, RecipeProduct, Tag

User = get_user_model()

PASSWORD = 'TestUser2026'
IMAGES_DIR = settings.BASE_DIR / 'data' / 'images'

ADMINS = (
    {
        'email': 'admin@email.ru',
        'username': 'admin',
        'first_name': 'Admin',
        'last_name': 'Admin',
        'password': 'admin',
    },
    {
        'email': 'review@admin.ru',
        'username': 'review',
        'first_name': 'Review',
        'last_name': 'Reviewer',
        'password': 'review1admin',
    },
)

USERS = (
    ('gandalf@middleearth.me', 'gandalf', 'Гэндальф', 'Серый'),
    ('yoda@jedi.sw', 'yoda', 'Йода', 'Магистр'),
    ('aragorn@gondor.me', 'aragorn', 'Арагорн', 'Элессар'),
    ('dweller@vault111.fo', 'vault_dweller', 'Выходец', 'Убежища'),
    ('geralt@rivia.tw', 'geralt', 'Геральт', 'Ривийский'),
)

# username, название, описание, время, картинка,
# ((ключ ингредиента, количество), ...), (слаги тегов, ...)
RECIPES = (
    (
        'gandalf', 'Лембас эльфийский',
        'Путевой хлеб эльфов. Замесить муку с мёдом и молоком, запечь. '
        'Один ломтик насыщает путника на целый день.',
        15, 'lembas.jpg',
        (('пшеничная мука', 250), ('мед', 50), ('молоко', 100),
         ('сливочное масло', 50)),
        ('breakfast',),
    ),
    (
        'yoda', 'Похлёбка Сэма',
        'Сытная похлёбка для долгой дороги в Мордор. Потушить картофель '
        'с луком и морковью на воде до мягкости.',
        40, 'pohlebka.jpg',
        (('картофель', 500), ('лук репчатый', 100), ('морковь', 100),
         ('вода', 500)),
        ('lunch', 'dinner'),
    ),
    (
        'aragorn', 'Синий коктейль с Татуина',
        'Синее молоко Татуина. Взбить молоко с мёдом и подать '
        'охлаждённым. Любимый напиток джедаев.',
        5, 'cocktail.jpg',
        (('молоко', 200), ('мед', 30)),
        ('breakfast',),
    ),
    (
        'vault_dweller', 'Завёрнутый в таинственное мясо ядерник',
        'Таинственное мясо Пустоши, обжаренное с луком и чесноком и '
        'завёрнутое в лепёшку. Что за мясо - лучше не спрашивать.',
        45, 'nuka_meat_wrap.jpg',
        (('говядина', 300), ('лук репчатый', 80), ('чеснок', 10),
         ('пшеничная мука', 150)),
        ('dinner',),
    ),
    (
        'vault_dweller', 'Идеально сохранившийся пирог',
        'Пирог, переживший ядерную войну без единой трещинки. Песочное '
        'тесто из муки, масла, яиц и сахара. Срок годности - века.',
        60, 'preserved_pie.jpg',
        (('пшеничная мука', 300), ('сливочное масло', 150), ('яйц', 2),
         ('сахар', 100)),
        ('breakfast',),
    ),
    (
        'vault_dweller', 'Тошковый суп',
        'Суп из тошки - мутантного родича картофеля и помидора. Отварить '
        'овощи с морковью на воде. Согревает после рейда по Пустоши.',
        35, 'tato_soup.jpg',
        (('картофель', 400), ('помидор', 200), ('морковь', 100),
         ('вода', 600)),
        ('lunch',),
    ),
    (
        'vault_dweller', 'Флоут с ядер-колой',
        'Ледяной десертный напиток Пустоши. Взбить молоко с сахаром и '
        'мёдом, подать очень холодным. Плюс к настроению гарантирован.',
        5, 'nuka_float.jpg',
        (('молоко', 200), ('сахар', 60), ('мед', 20)),
        ('breakfast',),
    ),
    (
        'geralt', 'Жареная крупа Blaviken Inn',
        'Гречка, обжаренная с грибами и луком, как в таверне Блавикена. '
        'Простой ужин ведьмака после охоты на чудовищ.',
        30, 'blaviken_grain.jpg',
        (('гречневая крупа', 200), ('грибы', 150), ('лук репчатый', 80),
         ('растительное масло', 30)),
        ('lunch', 'dinner'),
    ),
    (
        'geralt', 'Суп Уайта',
        'Белый суп на сметане с картофелем, луком и укропом. Наваристо '
        'и по-оксенфуртски уютно.',
        40, 'white_soup.jpg',
        (('картофель', 300), ('сметана', 100), ('лук репчатый', 80),
         ('укроп', 15), ('вода', 500)),
        ('lunch', 'dinner'),
    ),
    (
        'geralt', 'Куриный сэндвич',
        'Поджаренный хлеб с куриным филе, сыром и помидором. Быстрый '
        'перекус между контрактами на монстров.',
        15, 'chicken_sandwich.jpg',
        (('хлеб', 100), ('куриное филе', 150), ('сыр', 50),
         ('помидор', 50)),
        ('breakfast', 'lunch'),
    ),
    (
        'gandalf', 'Рецепт пива',
        'Домашнее светлое. Затереть солод в тёплой воде, отварить сусло '
        'с хмелем около часа, охладить, внести дрожжи и оставить '
        'бродить неделю. Терпение вознаграждается.',
        90, 'beer.jpg',
        (('солод', 1000), ('хмель', 30), ('дрожжи', 10), ('вода', 5000),
         ('сахар', 200)),
        ('dinner',),
    ),
)


class Command(BaseCommand):
    help = 'Создаёт тестовых пользователей и рецепты'

    def handle(self, *args, **options):
        if not Product.objects.exists() or not Tag.objects.exists():
            self.stdout.write(self.style.ERROR(
                'Нет продуктов/тегов - сначала выполните import_data.'
            ))
            return
        for admin in ADMINS:
            self.create_admin(admin)
        users = {}
        for email, username, first_name, last_name in USERS:
            users[username] = self.create_user(
                email, username, first_name, last_name,
            )
        for recipe_data in RECIPES:
            self.create_recipe(users, recipe_data)
        self.stdout.write(self.style.SUCCESS('Тестовые данные готовы.'))

    def create_admin(self, data):
        if not User.objects.filter(username=data['username']).exists():
            User.objects.create_superuser(**data)

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

    @staticmethod
    def find_product(keyword):
        for lookup in ('iexact', 'istartswith', 'icontains'):
            product = Product.objects.filter(
                **{f'name__{lookup}': keyword},
            ).order_by('name').first()
            if product:
                return product
        return None

    def create_recipe(self, users, recipe_data):
        username, name, text, cooking_time, image_name, \
            ingredients, tag_slugs = recipe_data
        recipe, created = Recipe.objects.get_or_create(
            author=users[username],
            name=name,
            defaults={'text': text, 'cooking_time': cooking_time},
        )
        if not created:
            return
        with open(IMAGES_DIR / image_name, 'rb') as image:
            recipe.image.save(image_name, ContentFile(image.read()))
        recipe.tags.set(Tag.objects.filter(slug__in=tag_slugs))
        used = set()
        recipe_products = []
        for keyword, amount in ingredients:
            product = self.find_product(keyword)
            if product and product.id not in used:
                used.add(product.id)
                recipe_products.append(RecipeProduct(
                    recipe=recipe,
                    product=product,
                    amount=amount,
                ))
        RecipeProduct.objects.bulk_create(recipe_products)
