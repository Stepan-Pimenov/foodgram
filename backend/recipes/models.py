from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db import models

from recipes.constants import (
    MAX_EMAIL_LENGTH,
    MAX_MEASUREMENT_UNIT_LENGTH,
    MAX_NAME_LENGTH,
    MAX_PRODUCT_NAME_LENGTH,
    MAX_RECIPE_NAME_LENGTH,
    MAX_STR_LENGTH,
    MAX_TAG_NAME_LENGTH,
    MAX_TAG_SLUG_LENGTH,
    MIN_AMOUNT,
    MIN_COOKING_TIME,
)


class User(AbstractUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name')

    email = models.EmailField(
        'Адрес электронной почты',
        max_length=MAX_EMAIL_LENGTH,
        unique=True,
    )
    first_name = models.CharField('Имя', max_length=MAX_NAME_LENGTH)
    last_name = models.CharField('Фамилия', max_length=MAX_NAME_LENGTH)
    avatar = models.ImageField(
        'Аватар',
        upload_to='users/avatars/',
        null=True,
        blank=True,
        default=None,
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.username[:MAX_STR_LENGTH]


class Subscription(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions_to_author',
        verbose_name='Автор',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'author'),
                name='unique_subscription',
            ),
            models.CheckConstraint(
                condition=~models.Q(user=models.F('author')),
                name='prevent_self_subscription',
            ),
        )

    def __str__(self):
        return f'{self.user} -> {self.author}'[:MAX_STR_LENGTH]


class Tag(models.Model):
    name = models.CharField(
        'Название',
        max_length=MAX_TAG_NAME_LENGTH,
        unique=True,
    )
    slug = models.SlugField(
        'Слаг',
        max_length=MAX_TAG_SLUG_LENGTH,
        unique=True,
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)

    def __str__(self):
        return self.name[:MAX_STR_LENGTH]


class Product(models.Model):
    name = models.CharField(
        'Название',
        max_length=MAX_PRODUCT_NAME_LENGTH,
        db_index=True,
    )
    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=MAX_MEASUREMENT_UNIT_LENGTH,
    )

    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'
        ordering = ('name',)
        constraints = (
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_product',
            ),
        )

    def __str__(self):
        return f'{self.name[:MAX_STR_LENGTH]}, {self.measurement_unit}'


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор',
    )
    name = models.CharField('Название', max_length=MAX_RECIPE_NAME_LENGTH)
    image = models.ImageField('Картинка', upload_to='recipes/images/')
    text = models.TextField('Описание')
    products = models.ManyToManyField(
        Product,
        through='RecipeProduct',
        related_name='recipes',
        verbose_name='Продукты',
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Теги',
    )
    cooking_time = models.PositiveIntegerField(
        'Время приготовления (мин)',
        validators=(MinValueValidator(MIN_COOKING_TIME),),
    )
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True)

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def __str__(self):
        return self.name[:MAX_STR_LENGTH]


class RecipeProduct(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_products',
        verbose_name='Рецепт',
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='recipe_products',
        verbose_name='Продукт',
    )
    amount = models.PositiveIntegerField(
        'Количество',
        validators=(MinValueValidator(MIN_AMOUNT),),
    )

    class Meta:
        verbose_name = 'Продукт в рецепте'
        verbose_name_plural = 'Продукты в рецептах'
        constraints = (
            models.UniqueConstraint(
                fields=('recipe', 'product'),
                name='unique_recipe_product',
            ),
        )

    def __str__(self):
        return f'{self.product} - {self.amount}'


class UserRecipeRelation(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )

    class Meta:
        abstract = True
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='%(app_label)s_%(class)s_unique',
            ),
        )

    def __str__(self):
        return f'{self._meta.verbose_name}: {self.user} - {self.recipe}'


class Favorite(UserRecipeRelation):

    class Meta(UserRecipeRelation.Meta):
        default_related_name = 'favorites'
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'


class ShoppingCart(UserRecipeRelation):

    class Meta(UserRecipeRelation.Meta):
        default_related_name = 'shopping_carts'
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
