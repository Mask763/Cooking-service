from django.contrib.auth import get_user_model
from django.db import models

from recipes.models import Recipe

User = get_user_model()


class ShoppingCart(models.Model):
    """Список покупок."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )
    recipes = models.ManyToManyField(Recipe, through='ShoppingCartItem')

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        default_related_name = 'shopping_cart'


class ShoppingCartItem(models.Model):
    """Элемент списка покупок."""

    cart = models.ForeignKey(ShoppingCart, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['cart', 'recipe'],
                name='unique_shopping_cart_item',
            )
        ]
