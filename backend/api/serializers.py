from django.db import transaction
from djoser.serializers import UserSerializer as DjoserUserSerializer
from rest_framework import serializers

from api.fields import Base64ImageField
from recipes.constants import MIN_AMOUNT
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


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'


class UserSerializer(DjoserUserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta(DjoserUserSerializer.Meta):
        fields = (
            *DjoserUserSerializer.Meta.fields,
            'is_subscribed',
            'avatar',
        )

    def get_is_subscribed(self, author):
        request = self.context.get('request')
        return (
            request is not None
            and request.user.is_authenticated
            and request.user.subscriptions.filter(author=author).exists()
        )


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = fields


class UserWithRecipesSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(read_only=True, default=0)

    class Meta(UserSerializer.Meta):
        fields = (*UserSerializer.Meta.fields, 'recipes', 'recipes_count')

    def get_recipes(self, author):
        request = self.context.get('request')
        recipes = author.recipes.all()
        limit = request.query_params.get('recipes_limit') if request else None
        if limit:
            try:
                recipes = recipes[:int(limit)]
            except ValueError:
                pass
        return RecipeMinifiedSerializer(
            recipes,
            many=True,
            context=self.context,
        ).data


class RecipeProductReadSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='product.id', read_only=True)
    name = serializers.CharField(source='product.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='product.measurement_unit',
        read_only=True,
    )

    class Meta:
        model = RecipeProduct
        fields = ('id', 'name', 'measurement_unit', 'amount')
        read_only_fields = ('amount',)


class RecipeReadSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = RecipeProductReadSerializer(
        many=True,
        read_only=True,
        source='recipe_products',
    )
    is_favorited = serializers.BooleanField(read_only=True, default=False)
    is_in_shopping_cart = serializers.BooleanField(
        read_only=True,
        default=False,
    )

    class Meta:
        model = Recipe
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


class RecipeProductWriteSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    amount = serializers.IntegerField(
        min_value=MIN_AMOUNT,
        error_messages={
            'min_value': f'Количество не может быть меньше {MIN_AMOUNT}.',
        },
    )


class RecipeWriteSerializer(serializers.ModelSerializer):
    ingredients = RecipeProductWriteSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
        )

    def validate(self, data):
        for field in ('ingredients', 'tags'):
            if field not in data:
                raise serializers.ValidationError(
                    {field: 'Обязательное поле.'}
                )
        return data

    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise serializers.ValidationError(
                'Нужен хотя бы один продукт.'
            )
        products = [ingredient['id'] for ingredient in ingredients]
        if len(products) != len(set(products)):
            raise serializers.ValidationError(
                'Продукты не должны повторяться.'
            )
        return ingredients

    def validate_tags(self, tags):
        if not tags:
            raise serializers.ValidationError('Нужен хотя бы один тег.')
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError(
                'Теги не должны повторяться.'
            )
        return tags

    @staticmethod
    def set_ingredients(recipe, ingredients):
        RecipeProduct.objects.bulk_create(
            RecipeProduct(
                recipe=recipe,
                product=ingredient['id'],
                amount=ingredient['amount'],
            )
            for ingredient in ingredients
        )

    @transaction.atomic
    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(
            author=self.context['request'].user,
            **validated_data,
        )
        recipe.tags.set(tags)
        self.set_ingredients(recipe, ingredients)
        return recipe

    @transaction.atomic
    def update(self, recipe, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe.tags.set(tags)
        recipe.recipe_products.all().delete()
        self.set_ingredients(recipe, ingredients)
        return super().update(recipe, validated_data)

    def to_representation(self, recipe):
        return RecipeReadSerializer(recipe, context=self.context).data


class UserRecipeRelationSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('user', 'recipe')

    def validate(self, data):
        if self.Meta.model.objects.filter(
            user=data['user'],
            recipe=data['recipe'],
        ).exists():
            raise serializers.ValidationError(
                f'{self.Meta.model._meta.verbose_name}: рецепт уже добавлен.'
            )
        return data

    def to_representation(self, relation):
        return RecipeMinifiedSerializer(
            relation.recipe,
            context=self.context,
        ).data


class FavoriteSerializer(UserRecipeRelationSerializer):
    class Meta(UserRecipeRelationSerializer.Meta):
        model = Favorite


class ShoppingCartSerializer(UserRecipeRelationSerializer):
    class Meta(UserRecipeRelationSerializer.Meta):
        model = ShoppingCart


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ('user', 'author')

    def validate(self, data):
        if data['user'] == data['author']:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя.'
            )
        if data['user'].subscriptions.filter(author=data['author']).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на этого пользователя.'
            )
        return data

    def to_representation(self, subscription):
        return UserWithRecipesSerializer(
            subscription.author,
            context=self.context,
        ).data
