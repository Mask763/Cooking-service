from io import StringIO

from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from api.filters import IngredientFilter, RecipesFilter
from api.pagination import WithLimitPagination
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (AvatarSerializer, FavoriteSerializer,
                             FollowListSerializer, FollowSerializer,
                             IngredientSerializer, RecipeReadSerializer,
                             RecipeWriteSerializer, ShoppingCartSerializer,
                             TagSerializer)
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import Follow


User = get_user_model()


class ApplicationUserViewSet(UserViewSet):
    """Вьюсет для модели пользователя."""

    queryset = User.objects.all()
    pagination_class = WithLimitPagination

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

    @action(methods=['get'], detail=False, url_path='subscriptions')
    def subscriptions(self, request):
        queryset = User.objects.filter(following__user=request.user)
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(queryset, request)
        serializer = FollowListSerializer(
            result_page, many=True, context={'request': request}
        )
        return paginator.get_paginated_response(serializer.data)

    @action(methods=['post', 'delete'], detail=True, url_path='subscribe')
    def subscribe(self, request, id):
        following = get_object_or_404(User, id=id)
        user = request.user

        if request.method == 'POST':
            data = {'user': user.id, 'following': following.id}
            serializer = FollowSerializer(
                data=data, context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        follow = Follow.objects.filter(user=user, following=following)
        result = follow.delete()

        if not result[0]:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={'errors': 'Такой подписки не существует'}
            )

        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_permissions(self):
        if self.action == 'me':
            return (permissions.IsAuthenticated(),)
        return super().get_permissions()


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для модели тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для модели ингредиентов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для модели рецептов."""

    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrReadOnly,)
    pagination_class = WithLimitPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipesFilter

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def add_to_model(self, request, pk, serializer):
        """Добавление рецепта в избранное или покупки."""
        recipe = get_object_or_404(Recipe, pk=pk)
        data = {'user': request.user.id, 'recipe': recipe.id}
        serializer = serializer(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_from_model(self, request, pk, model):
        """Удаление рецепта из избранного или покупок."""
        recipe = get_object_or_404(Recipe, pk=pk)
        user = request.user
        result = model.objects.filter(user=user, recipe=recipe).delete()

        if not result[0]:
            return Response(
                data={'errors': 'Такой рецепт не найден.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'], url_path='favorite')
    def favorite(self, request, pk):
        if request.method == 'POST':
            return self.add_to_model(request, pk, FavoriteSerializer)
        return self.delete_from_model(request, pk, Favorite)

    @action(detail=True, methods=['post', 'delete'], url_path='shopping_cart')
    def shopping_cart(self, request, pk):
        if request.method == 'POST':
            return self.add_to_model(request, pk, ShoppingCartSerializer)
        return self.delete_from_model(request, pk, ShoppingCart)

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_short_link(self, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        return Response(
            {'short-link': (
                request.build_absolute_uri('/s/')
                + recipe.short_link
            )}
        )

    @action(detail=False, methods=['get'], url_path='download_shopping_cart')
    def download_shopping_cart(self, request):
        ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_cart__user=request.user
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(
            total_amount=Sum('amount')
        ).order_by(
            'ingredient__name'
        )
        output = StringIO()
        output.write(
            f"Список ингредиентов из корзины покупок пользователя "
            f"{request.user.username}:\n\n"
        )

        for ingredient in ingredients:
            output.write(f"- {ingredient['ingredient__name']} "
                         f"({ingredient['ingredient__measurement_unit']}) - "
                         f"{ingredient['total_amount']}\n")

        response = HttpResponse(
            output.getvalue(),
            content_type='text/plain',
            status=status.HTTP_200_OK,
        )

        filename = f"{request.user.username}_shopping_cart.txt"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        return response
