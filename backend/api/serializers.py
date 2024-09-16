import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from djoser.serializers import UserSerializer as DjoserUserSerializer
from rest_framework import serializers

from api.constants import REQUIRED_FIELDS_FOR_UPDATE
from follow.models import Follow
from recipes.models import Ingredient, Recipe, Tag, RecipeIngredient


User = get_user_model()


class Base64ImageField(serializers.ImageField):
    """Сериализатор для полей типа ImageField."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


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
        if request is None or request.user.is_anonymous:
            return False
        return Follow.objects.filter(
            user=request.user, following=obj
        ).exists()


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


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов."""

    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(many=True)
    image = Base64ImageField(required=True, allow_null=False)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

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
        read_only_fields = (
            'author',
            'is_favorited',
            'is_in_shopping_cart',
        )

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['tags'] = TagSerializer(instance.tags.all(), many=True).data
        return ret

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return obj.favorite.filter(user=request.user).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        print(request)
        if request is None or request.user.is_anonymous:
            return False
        return obj.shopping_cart.filter(user=request.user).exists()

    def validate_ingredients(self, data):
        if not len(data):
            raise serializers.ValidationError(
                'Необходимо указать ингредиенты.'
            )

        for ingredient in data:
            if ingredient['amount'] <= 0:
                raise serializers.ValidationError(
                    'Количество должно быть больше нуля.'
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

        tags = [tag for tag in data]

        if len(tags) != len(set(tags)):
            raise serializers.ValidationError(
                'Теги должны быть уникальными.'
            )

        return data

    def validate_cooking_time(self, data):
        if data <= 0:
            raise serializers.ValidationError(
                'Время приготовления должно быть больше нуля.'
            )
        return data

    def validate_image(self, data):
        if data is None:
            raise serializers.ValidationError(
                'Поле "image" не может быть пустым.'
            )
        return data

    def create(self, validated_data):
        tags_data = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags_data)

        for ingredient_data in ingredients_data:
            ingredient_id = ingredient_data['ingredient']['id']
            amount = ingredient_data['amount']
            RecipeIngredient.objects.create(
                recipe=recipe, ingredient=ingredient_id, amount=amount
            )
        return recipe

    def update(self, instance, validated_data):
        for field in REQUIRED_FIELDS_FOR_UPDATE:
            if field not in validated_data:
                raise serializers.ValidationError(
                    f'Поле "{field}" не может быть пустым.'
                )

        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.image = validated_data.get('image', instance.image)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time
        )
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        ingredients_list = []
        instance.ingredients.all().delete()

        for ingredient_data in ingredients_data:
            ingredient_id = ingredient_data['ingredient']['id']
            amount = ingredient_data['amount']
            current_ingredient, _ = RecipeIngredient.objects.get_or_create(
                recipe=instance, ingredient=ingredient_id, amount=amount
            )
            ingredients_list.append(current_ingredient)

        instance.tags.set(tags_data)
        instance.ingredients.set(ingredients_list)
        instance.save()
        return instance


class ItemSerializer(serializers.ModelSerializer):
    """Сериализатор для объектов списка покупок и избранного."""

    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('id', 'name', 'image', 'cooking_time')


class RecipeShortSerializer(serializers.ModelSerializer):
    """Сериализатор для короткого отображения рецептов."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FollowSerializer(serializers.ModelSerializer):
    """Сериализатор для подписок."""

    recipes = serializers.SerializerMethodField()
    is_subscribed = serializers.BooleanField(default=True)
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
