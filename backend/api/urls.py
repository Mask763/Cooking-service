from django.urls import include, path
from rest_framework import routers

from .views import (CustomUserViewSet, FavoriteViewSet, FollowViewSet,
                    IngredientViewSet, RecipeViewSet, ShoppingCartViewSet,
                    TagViewSet)

v1_router = routers.DefaultRouter()
v1_router.register('users', CustomUserViewSet, basename='users')
v1_router.register('tags', TagViewSet, basename='tags')
v1_router.register('ingredients', IngredientViewSet, basename='ingredients')
v1_router.register('recipes', RecipeViewSet, basename='recipes')

urlpatterns = [
    path('users/<int:pk>/subscribe/',
         FollowViewSet.as_view({'post': 'create', 'delete': 'destroy'}),
         name='subscribe'),
    path('users/subscriptions/',
         FollowViewSet.as_view({'get': 'list'}),
         name='subscriptions'),
    path('', include(v1_router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
    path('recipes/<int:pk>/shopping_cart/',
         ShoppingCartViewSet.as_view({'post': 'create', 'delete': 'destroy'}),
         name='shopping_cart'),
    path('recipes/<int:pk>/favorite/',
         FavoriteViewSet.as_view({'post': 'create', 'delete': 'destroy'}),
         name='favorite')
]
