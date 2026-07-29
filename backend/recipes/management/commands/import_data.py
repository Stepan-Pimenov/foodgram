import json

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Product, Tag

DATA_DIR = settings.BASE_DIR / 'data'


class Command(BaseCommand):
    help = 'Загружает продукты и теги из папки data'

    def handle(self, *args, **options):
        self.load('ingredients.json', Product)
        self.load('tags.json', Tag)

    def load(self, filename, model):
        with open(DATA_DIR / filename, encoding='utf-8') as file:
            items = json.load(file)
        model.objects.bulk_create(
            (model(**item) for item in items),
            ignore_conflicts=True,
        )
        self.stdout.write(
            self.style.SUCCESS(
                f'{model._meta.verbose_name_plural}: обработано {len(items)}.'
            )
        )
