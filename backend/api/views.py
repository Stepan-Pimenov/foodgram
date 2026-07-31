import io

from django.db.models import (
    BooleanField,
    Count,
    Exists,
    F,
    OuterRef,
    Sum,
    Value,
)
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from api.filters import IngredientFilter, RecipeFilter
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (
    AvatarSerializer,
    FavoriteSerializer,
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    ShoppingCartSerializer,
    SubscriptionSerializer,
    TagSerializer,
    UserWithRecipesSerializer,
)
from recipes.models import (
    Favorite,
    Product,
    Recipe,
    RecipeProduct,
    ShoppingCart,
    Tag,
    User,
)
from recipes.utils import to_base36


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(ReadOnlyModelViewSet):
    queryset = Product.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class RecipeViewSet(ModelViewSet):
    permission_classes = (IsAuthorOrReadOnly,)
    http_method_names = ('get', 'post', 'patch', 'delete')
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_queryset(self):
        user = self.request.user
        recipes = Recipe.objects.select_related('author').prefetch_related(
            'tags',
            'recipe_products__product',
        )
        if user.is_authenticated:
            is_favorited = Exists(
                Favorite.objects.filter(user=user, recipe=OuterRef('pk')),
            )
            is_in_shopping_cart = Exists(
                ShoppingCart.objects.filter(
                    user=user,
                    recipe=OuterRef('pk'),
                ),
            )
        else:
            is_favorited = Value(False, output_field=BooleanField())
            is_in_shopping_cart = Value(False, output_field=BooleanField())
        return recipes.annotate(
            is_favorited=is_favorited,
            is_in_shopping_cart=is_in_shopping_cart,
        )

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeReadSerializer
        return RecipeWriteSerializer

    @action(detail=True, url_path='get-link')
    def get_link(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        short_link = request.build_absolute_uri(
            reverse('short-link', args=(to_base36(recipe.pk),))
        )
        return Response({'short-link': short_link})

    def add_to_list(self, serializer_class, request, pk):
        serializer = serializer_class(
            data={'user': request.user.id, 'recipe': pk},
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def remove_from_list(self, model, request, pk):
        deleted, _ = model.objects.filter(
            user=request.user,
            recipe_id=pk,
        ).delete()
        return Response(
            status=status.HTTP_204_NO_CONTENT if deleted
            else status.HTTP_400_BAD_REQUEST
        )

    @action(
        detail=True,
        methods=('post',),
        permission_classes=(IsAuthenticated,),
    )
    def favorite(self, request, pk=None):
        return self.add_to_list(FavoriteSerializer, request, pk)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        return self.remove_from_list(Favorite, request, pk)

    @action(
        detail=True,
        methods=('post',),
        permission_classes=(IsAuthenticated,),
    )
    def shopping_cart(self, request, pk=None):
        return self.add_to_list(ShoppingCartSerializer, request, pk)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        return self.remove_from_list(ShoppingCart, request, pk)

    @action(detail=False, permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request):
        products = RecipeProduct.objects.filter(
            recipe__shopping_carts__user=request.user,
        ).values(
            name=F('product__name'),
            unit=F('product__measurement_unit'),
        ).annotate(total=Sum('amount')).order_by('name')
        content = self.build_shopping_list(request.user, products)
        return FileResponse(
            io.BytesIO(content.encode('utf-8')),
            as_attachment=True,
            filename='shopping_list.txt',
            content_type='text/plain; charset=utf-8',
        )

    def build_shopping_list(self, user, products):
        product_lines = [
            f'{number}. {item["name"].capitalize()} '
            f'({item["unit"]}) - {item["total"]}'
            for number, item in enumerate(products, start=1)
        ]
        recipes = Recipe.objects.filter(
            shopping_carts__user=user,
        ).values_list('name', flat=True)
        return '\n'.join((
            'Список покупок',
            '',
            'Продукты:',
            *product_lines,
            '',
            'Рецепты в списке:',
            *(f'- {name}' for name in recipes),
            '',
        ))


class UserViewSet(DjoserUserViewSet):

    @action(detail=False, permission_classes=(IsAuthenticated,))
    def me(self, request):
        serializer = self.get_serializer(
            request.user,
            context={'request': request},
        )
        return Response(serializer.data)

    @action(
        detail=False,
        methods=('put',),
        url_path='me/avatar',
        permission_classes=(IsAuthenticated,),
    )
    def avatar(self, request):
        serializer = AvatarSerializer(request.user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @avatar.mapping.delete
    def delete_avatar(self, request):
        request.user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, permission_classes=(IsAuthenticated,))
    def subscriptions(self, request):
        authors = User.objects.filter(
            subscriptions_to_author__user=request.user,
        ).annotate(recipes_count=Count('recipes')).order_by('username')
        page = self.paginate_queryset(authors)
        serializer = UserWithRecipesSerializer(
            page,
            many=True,
            context={'request': request},
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=('post',),
        permission_classes=(IsAuthenticated,),
    )
    def subscribe(self, request, id=None):
        serializer = SubscriptionSerializer(
            data={'user': request.user.id, 'author': id},
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, id=None):
        deleted, _ = request.user.subscriptions.filter(author_id=id).delete()
        return Response(
            status=status.HTTP_204_NO_CONTENT if deleted
            else status.HTTP_400_BAD_REQUEST
        )
