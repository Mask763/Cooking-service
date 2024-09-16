import json

from django.core.management.base import BaseCommand

from recipes.models import Tag


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            'json_file', type=str, help='The JSON file to load'
        )

    def handle(self, *args, **kwargs):
        json_file = kwargs['json_file']

        with open(json_file, 'r', encoding='utf-8') as file:
            data = json.load(file)

            for item in data:
                Tag.objects.create(
                    name=item['name'],
                    slug=item['slug'],
                )
        self.stdout.write(
            self.style.SUCCESS('Successfully loaded ingredients from JSON')
        )
