import json

from django.core.management.base import BaseCommand

from recipes.models import Tag


class Command(BaseCommand):
    """Команда для загрузки тегов из JSON."""

    def handle(self, *args, **kwargs):
        json_file_path = 'recipes/data/tags.json'

        with open(json_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            tags = [Tag(**item) for item in data]
            Tag.objects.bulk_create(tags)

        self.stdout.write(
            self.style.SUCCESS('Successfully loaded tags from JSON')
        )
