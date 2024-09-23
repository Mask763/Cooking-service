from django.contrib import admin

from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag


class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug')
    search_fields = ('name',)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'author', 'favorite_count')
    list_filter = ('tags',)
    search_fields = ('name', 'author__username')
    readonly_fields = ('short_link',)
    inlines = (RecipeIngredientInline,)

    def favorite_count(self, obj):
        return obj.favorite.count()

    favorite_count.short_description = 'Количество добавлений в избранное'


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name',)


admin.site.register(Tag, TagAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Ingredient, IngredientAdmin)
