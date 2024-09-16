from django.contrib.auth import get_user_model
from django.db import models

from recipes.models import Recipe

User = get_user_model()


class Favorite(models.Model):
    """Избранное."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )
    recipes = models.ManyToManyField(Recipe, through='FavoriteItem')

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'
        default_related_name = 'favorite'


class FavoriteItem(models.Model):
    """Элемент избранного"""

    favorite = models.ForeignKey(Favorite, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['favorite', 'recipe'],
                name='unique_favorite_item',
            )
        ]
