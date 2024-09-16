from django.contrib import admin
from shopping_cart.models import ShoppingCart


class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user',)


admin.site.register(ShoppingCart, ShoppingCartAdmin)
