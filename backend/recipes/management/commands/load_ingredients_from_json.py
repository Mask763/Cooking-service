import json

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    """Команда для загрузки ингредиентов из JSON."""

    def handle(self, *args, **kwargs):
        json_file_path = 'recipes/data/ingredients.json'

        with open(json_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            ingredients = [Ingredient(**item) for item in data]
            Ingredient.objects.bulk_create(ingredients)

        self.stdout.write(
            self.style.SUCCESS('Successfully loaded ingredients from JSON')
        )
