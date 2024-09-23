from django.contrib.auth import get_user_model
from django.db import transaction
from djoser.serializers import UserSerializer as DjoserUserSerializer
from rest_framework import serializers

from api.constants import REQUIRED_FIELDS_FOR_UPDATE
from api.serializers_fields import Base64ImageField
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import Follow


User = get_user_model()


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для аватара."""

    avatar = Base64ImageField(required=True, allow_null=False)

    def validate(self, data):
        if data.get('avatar') is None:
            raise serializers.ValidationError(
                'Поле "avatar" не может быть пустым.'
            )
        return data

    class Meta:
        model = User
        fields = ('avatar',)


class UserSerializer(DjoserUserSerializer):
    """Сериализатор для пользователя."""

    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta(DjoserUserSerializer.Meta):
        model = User
        fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'is_subscribed',
            'avatar',
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return (
            request
            and request.user.is_authenticated
            and Follow.objects.filter(
                user=request.user, following=obj
            ).exists()
        )


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов."""

    class Meta:
        model = Tag
        fields = ('id', 'slug', 'name')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


# Для добавления ингредиентов в рецепты нужны поля id и amount,
# но при этом при POST запросе на создание рецепта должны вернуться все 4 поля.
class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов с ингредиентами."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(), source='ingredient.id'
    )
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit', read_only=True
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount', 'measurement_unit', 'name')


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения рецептов."""

    tags = TagSerializer(many=True)
    author = UserSerializer()
    ingredients = RecipeIngredientSerializer(many=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'author',
            'image',
            'text',
            'ingredients',
            'tags',
            'cooking_time',
            'is_favorited',
            'is_in_shopping_cart',
        )

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        return (
            request
            and request.user.is_authenticated
            and obj.favorite.filter(user=request.user).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        return (
            request
            and request.user.is_authenticated
            and obj.shopping_cart.filter(user=request.user).exists()
        )


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для записи рецептов."""

    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    ingredients = RecipeIngredientSerializer(many=True)
    image = Base64ImageField(required=True, allow_null=False)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'text',
            'ingredients',
            'tags',
            'cooking_time',
        )

    def validate_ingredients(self, data):
        if not len(data):
            raise serializers.ValidationError(
                'Необходимо указать ингредиенты.'
            )

        ingredients = [ingredient['ingredient']['id'] for ingredient in data]

        if len(ingredients) != len(set(ingredients)):
            raise serializers.ValidationError(
                'Ингредиенты должны быть уникальными.'
            )

        return data

    def validate_tags(self, data):
        if not len(data):
            raise serializers.ValidationError(
                'Необходимо указать теги.'
            )

        if len(data) != len(set(data)):
            raise serializers.ValidationError(
                'Теги должны быть уникальными.'
            )

        return data

    def validate_image(self, data):
        if data is None:
            raise serializers.ValidationError(
                'Поле "image" не может быть пустым.'
            )
        return data

    def validate(self, data):
        for field in REQUIRED_FIELDS_FOR_UPDATE:
            if field not in data:
                raise serializers.ValidationError(
                    f'Поле "{field}" не может быть пустым.'
                )

        return data

    def create_recipe_ingredients(self, ingredients_data, recipe):
        """Вспомогательная функция для добавления ингредиентов в рецепт."""
        recipe_ingredients = [
            RecipeIngredient(
                ingredient=ingredient_data['ingredient']['id'],
                amount=ingredient_data['amount'],
                recipe=recipe
            )
            for ingredient_data in ingredients_data
        ]
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

    @transaction.atomic
    def create(self, validated_data):
        tags_data = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')
        request = self.context.get('request')
        recipe = Recipe.objects.create(
            **validated_data,
            author=request.user
        )
        recipe.tags.set(tags_data)
        self.create_recipe_ingredients(ingredients_data, recipe)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        instance.tags.set(tags_data)
        # В модели рецепта не определено поле с ингредиентами,
        # связь настроена через промежуточную таблицу,
        # метод clear не поддерживается
        instance.ingredients.all().delete()
        self.create_recipe_ingredients(ingredients_data, instance)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return RecipeReadSerializer(instance, context=self.context).data


class RecipeShortSerializer(serializers.ModelSerializer):
    """Сериализатор для короткого отображения рецептов."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления рецептов в избранное."""

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')

    def validate(self, data):
        user_id = data['user']
        recipe_id = data['recipe']

        if Favorite.objects.filter(user=user_id, recipe=recipe_id).exists():
            raise serializers.ValidationError(
                'Рецепт уже добавлен в избранное.'
            )

        return data

    def to_representation(self, instance):
        return RecipeShortSerializer(instance.recipe).data


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления рецептов в список покупок."""

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')

    def validate(self, data):
        user_id = data['user']
        recipe_id = data['recipe']

        if ShoppingCart.objects.filter(
            user=user_id, recipe=recipe_id
        ).exists():
            raise serializers.ValidationError(
                'Рецепт уже добавлен в список покупок.'
            )

        return data

    def to_representation(self, instance):
        return RecipeShortSerializer(instance.recipe).data


class FollowSerializer(serializers.ModelSerializer):
    """Сериализатор для подписок."""

    class Meta:
        model = Follow
        fields = ('user', 'following')

    def validate(self, data):
        user_id = data['user']
        following_id = data['following']

        if user_id == following_id:
            raise serializers.ValidationError(
                'Нельзя подписаться на себя.'
            )

        if Follow.objects.filter(
            user=user_id, following=following_id
        ).exists():
            raise serializers.ValidationError(
                'Такая подписка уже существует.'
            )

        return data

    def to_representation(self, instance):
        return FollowListSerializer(
            instance.following, context=self.context
        ).data


class FollowListSerializer(UserSerializer):
    """Сериализатор для списка подписок."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'is_subscribed',
            'recipes_count',
            'avatar',
            'recipes',
        )
        read_only_fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'is_subscribed',
            'recipes_count',
            'avatar',
            'recipes'
        )

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        if limit:
            recipes = obj.recipes.all()[:int(limit)]
        else:
            recipes = obj.recipes.all()
        return RecipeShortSerializer(recipes, many=True).data
