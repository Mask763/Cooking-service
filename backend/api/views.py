from django.contrib.auth import get_user_model
from djoser.views import UserViewSet
from rest_framework import status, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from api.pagination import UsersPagination
from api.serializers import (
    AvatarSerializer,
    TagSerializer,
    IngredientSerializer,
    RecipeSerializer
)
from recipes.models import Tag, Ingredient, Recipe


User = get_user_model()

class CustomUserViewSet(UserViewSet):
    """Вьюсет для модели пользователя."""

    pagination_class = UsersPagination

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


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для модели рецептов."""

    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
