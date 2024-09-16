from io import StringIO
import uuid

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from api.pagination import WithLimitPagination
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (
    AvatarSerializer,
    TagSerializer,
    IngredientSerializer,
    RecipeSerializer,
    ItemSerializer,
    FollowSerializer
)
from api.constants import BASE_URL_SHORT_LINK, MAX_LENGTH_SHORT_URL
from api.filters import IngredientFilter, RecipesFilter
from recipes.models import Tag, Ingredient, Recipe, RecipeIngredient
from shopping_cart.models import ShoppingCart
from favorite.models import Favorite
from follow.models import Follow


User = get_user_model()


class CustomUserViewSet(UserViewSet):
    """Вьюсет для модели пользователя."""

    pagination_class = WithLimitPagination

    def get_queryset(self):
        return User.objects.all()

    @action(methods=['put', 'delete'], detail=False, url_path='me/avatar')
    def set_or_delete_avatar(self, request):
        if request.method == 'PUT':
            serializers = AvatarSerializer(
                instance=request.user,
                data=request.data,
                partial=True
            )
            serializers.is_valid(raise_exception=True)
            serializers.save()
            return Response(serializers.data, status=status.HTTP_200_OK)
        request.user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_permissions(self):
        if self.action == 'me':
            return (permissions.IsAuthenticated(),)
        return super().get_permissions()


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для модели тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для модели ингредиентов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для модели рецептов."""

    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = (IsAuthorOrReadOnly,)
    pagination_class = WithLimitPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipesFilter

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_short_link(self, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)

        if not recipe.short_link:
            short_link = str(uuid.uuid4())[:MAX_LENGTH_SHORT_URL]
            recipe.short_link = short_link
            recipe.save()

        return Response(
            {'short-link': BASE_URL_SHORT_LINK + recipe.short_link}
        )

    @action(detail=False, methods=['get'], url_path='download_shopping_cart')
    def download_shopping_cart(self, request):
        recipes = Recipe.objects.filter(
            shopping_cart__user=request.user
        )
        ingredients = set()
        ingredient_amounts = {}

        for recipe in recipes:
            for recipe_ingredient in RecipeIngredient.objects.filter(
                recipe=recipe
            ):
                ingredient = recipe_ingredient.ingredient
                ingredients.add(ingredient)

                if ingredient.id not in ingredient_amounts:
                    ingredient_amounts[ingredient.id] = (
                        recipe_ingredient.amount
                    )
                else:
                    ingredient_amounts[ingredient.id] += (
                        recipe_ingredient.amount
                    )

        ingredient_list = [
            {
                'name': ingredient.name,
                'measurement_unit': ingredient.measurement_unit,
                'amount': ingredient_amounts[ingredient.id]
            } for ingredient in ingredients
        ]

        output = StringIO()
        output.write(
            f"Список ингредиентов из корзины покупок пользователя "
            f"{request.user.username}:\n\n"
        )

        for ingredient in ingredient_list:
            output.write(f"- {ingredient['name']} "
                         f"({ingredient['measurement_unit']}) - "
                         f"{ingredient['amount']}\n")

        response = HttpResponse(
            output.getvalue(),
            content_type='text/plain',
            status=status.HTTP_200_OK,
        )

        filename = f"{request.user.username}_shopping_cart.txt"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        return response


class RecipeRedirectView(APIView):
    """Представление для редиректа по короткому URL."""

    def get(self, request, short_link):
        recipe = get_object_or_404(Recipe, short_link=short_link)
        return redirect(reverse('recipes-detail', args=[recipe.id]))


class ItemViewSet(viewsets.ViewSet):
    """Базовый вьюсет для объектов списка покупок и избранного."""

    permission_classes = [permissions.IsAuthenticated]

    def get_data(self, request, obj, action):
        recipe_id = self.kwargs.get('pk')
        recipe = get_object_or_404(Recipe, id=recipe_id)
        obj_container, _ = obj.objects.get_or_create(user=request.user)

        if action == 'add':
            if recipe in obj_container.recipes.all():
                return Response(status=status.HTTP_400_BAD_REQUEST)

            obj_container.recipes.add(recipe)
            serializer = ItemSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if recipe not in obj_container.recipes.all():
            return Response(status=status.HTTP_400_BAD_REQUEST)

        obj_container.recipes.remove(recipe)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShoppingCartViewSet(ItemViewSet):
    """Вьюсет для модели списка покупок."""

    def get_queryset(self):
        return self.request.user.shopping_cart.recipes.all()

    def create(self, request, *args, **kwargs):
        return self.get_data(request, ShoppingCart, 'add')

    def destroy(self, request, *args, **kwargs):
        return self.get_data(request, ShoppingCart, 'remove')


class FavoriteViewSet(ItemViewSet):
    """Вьюсет для модели избранного."""

    def get_queryset(self):
        return self.request.user.favorite.recipes.all()

    def create(self, request, *args, **kwargs):
        return self.get_data(request, Favorite, 'add')

    def destroy(self, request, *args, **kwargs):
        return self.get_data(request, Favorite, 'remove')


class FollowViewSet(viewsets.ViewSet):
    """Вьюсет для модели Follow."""

    permission_classes = [permissions.IsAuthenticated]
    pagination_class = WithLimitPagination

    def create(self, request, *args, **kwargs):
        following = get_object_or_404(User, id=kwargs.get('pk'))
        user = request.user

        if following == user:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={'errors': 'Нельзя подписаться на самого себя'}
            )

        _, follow_status = Follow.objects.get_or_create(
            user=user, following=following
        )

        if not follow_status:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={'errors': 'Такая подписка уже существует'}
            )

        serializer = FollowSerializer(following, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        following = get_object_or_404(User, id=kwargs.get('pk'))
        user = request.user
        follow = Follow.objects.filter(user=user, following=following)

        if not follow.exists():
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={'errors': 'Такой подписки не существует'}
            )

        follow.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def list(self, request):
        queryset = User.objects.filter(following__user=request.user)
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(queryset, request)
        serializer = FollowSerializer(
            result_page, many=True, context={'request': request}
        )
        return paginator.get_paginated_response(serializer.data)
