from django_filters import rest_framework as filters

from recipes.models import Ingredient, Recipe, Tag


class IngredientFilter(filters.FilterSet):
    """Фильтр для ингредиентов."""

    name = filters.CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipesFilter(filters.FilterSet):
    """Фильтр для рецептов."""

    is_favorited = filters.BooleanFilter(
        method='filter_by_user_relation'
    )
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_by_user_relation'
    )
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all()
    )

    class Meta:
        model = Recipe
        fields = ('author', 'tags', 'is_favorited', 'is_in_shopping_cart')

    def filter_by_user_relation(self, queryset, name, value):
        user = self.request.user

        if not user.is_authenticated:
            return queryset

        if name == 'is_favorited':
            related_field = 'favorite__user'
        elif name == 'is_in_shopping_cart':
            related_field = 'shopping_cart__user'
        else:
            return queryset

        if value and user.is_authenticated:
            return queryset.filter(**{related_field: user})
        return queryset
