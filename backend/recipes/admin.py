from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.urls import reverse
from django.utils.safestring import mark_safe

from recipes.models import (
    Favorite,
    Product,
    Recipe,
    RecipeProduct,
    ShoppingCart,
    Subscription,
    Tag,
    User,
)

FAST_COOKING_TIME = 15
MEDIUM_COOKING_TIME = 40


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        'id',
        'username',
        'email',
        'first_name',
        'last_name',
        'recipes_count',
        'subscribers_count',
    )
    search_fields = ('email', 'username')
    list_filter = ('is_staff', 'is_superuser')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Аватар', {'fields': ('avatar',)}),
    )

    @admin.display(description='Рецептов')
    def recipes_count(self, user):
        return user.recipes.count()

    @admin.display(description='Подписчиков')
    def subscribers_count(self, user):
        return user.author_subscriptions.count()


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug')
    search_fields = ('name', 'slug')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit', 'recipes_count')
    search_fields = ('name',)
    list_filter = ('measurement_unit',)

    @admin.display(description='В рецептах')
    def recipes_count(self, product):
        return product.recipes.count()


class CookingTimeFilter(admin.SimpleListFilter):
    title = 'Время готовки'
    parameter_name = 'cooking_time_group'

    def lookups(self, request, model_admin):
        return (
            ('fast', f'до {FAST_COOKING_TIME} мин'),
            ('medium', f'{FAST_COOKING_TIME}-{MEDIUM_COOKING_TIME} мин'),
            ('slow', f'от {MEDIUM_COOKING_TIME} мин'),
        )

    def queryset(self, request, recipes):
        if self.value() == 'fast':
            return recipes.filter(cooking_time__lt=FAST_COOKING_TIME)
        if self.value() == 'medium':
            return recipes.filter(
                cooking_time__gte=FAST_COOKING_TIME,
                cooking_time__lt=MEDIUM_COOKING_TIME,
            )
        if self.value() == 'slow':
            return recipes.filter(cooking_time__gte=MEDIUM_COOKING_TIME)
        return recipes


class RecipeProductInline(admin.TabularInline):
    model = RecipeProduct
    min_num = 1
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'author_link',
        'cooking_time',
        'products_list',
        'tags_list',
        'favorites_count',
        'pub_date',
    )
    search_fields = ('name', 'author__username')
    list_filter = ('tags', 'pub_date', CookingTimeFilter)
    readonly_fields = ('favorites_count', 'image_preview')
    inlines = (RecipeProductInline,)

    @admin.display(description='Автор')
    def author_link(self, recipe):
        url = reverse('admin:recipes_user_change', args=(recipe.author.id,))
        return mark_safe(f'<a href="{url}">{recipe.author.username}</a>')

    @admin.display(description='Продукты')
    def products_list(self, recipe):
        return ', '.join(
            product.name for product in recipe.products.all()
        )

    @admin.display(description='Теги')
    def tags_list(self, recipe):
        return ', '.join(tag.name for tag in recipe.tags.all())

    @admin.display(description='В избранном')
    def favorites_count(self, recipe):
        return recipe.favorites.count() if recipe.pk else 0

    @admin.display(description='Превью')
    def image_preview(self, recipe):
        return mark_safe(f'<img src="{recipe.image.url}" width="80">')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'author')
    search_fields = ('user__username', 'author__username')


class UserRecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    search_fields = ('user__username', 'recipe__name')


@admin.register(Favorite)
class FavoriteAdmin(UserRecipeAdmin):
    pass


@admin.register(ShoppingCart)
class ShoppingCartAdmin(UserRecipeAdmin):
    pass
