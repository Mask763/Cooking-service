import django_filters

from recipes.models import Ingredient, Recipe, Tag


class IngredientFilter(django_filters.FilterSet):
    """Фильтр для ингредиентов."""

    name = django_filters.CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipesFilter(django_filters.FilterSet):
    """Фильтр для рецептов."""

    author = django_filters.NumberFilter(
        field_name='author__id',
        lookup_expr='exact',
        label='Автор'
    )
    is_favorited = django_filters.NumberFilter(
        method='filter_by_user_relation'
    )
    is_in_shopping_cart = django_filters.NumberFilter(
        method='filter_by_user_relation'
    )
    tags = django_filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all()
    )

    class Meta:
        model = Recipe
        fields = ('author', 'tags', 'is_favorited', 'is_in_shopping_cart')

    def filter_by_user_relation(self, queryset, name, value):
        value = int(value)

        if value not in (0, 1):
            raise ValueError('Значение фильтра должно быть 0 или 1')

        user = self.request.user

        if not user.is_authenticated:
            return queryset.none() if value else queryset

        if name == 'is_favorited':
            related_field = 'favorite__user'
        elif name == 'is_in_shopping_cart':
            related_field = 'shopping_cart__user'
        else:
            return queryset

        if value:
            return queryset.filter(**{related_field: user})
        return queryset.exclude(**{related_field: user})
