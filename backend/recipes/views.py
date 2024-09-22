from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404

from recipes.models import Recipe


def short_link_redirect(request, short_link):
    """Представление для редиректа по короткому URL."""
    recipe = get_object_or_404(Recipe, short_link=short_link)
    recipe_url = request.build_absolute_uri(f'/recipes/{recipe.id}/')

    if not recipe_url.startswith('https'):
        recipe_url = recipe_url.replace('http', 'https')

    return HttpResponseRedirect(recipe_url)
