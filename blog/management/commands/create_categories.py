"""
Management command to create initial blog categories.
"""
from django.core.management.base import BaseCommand
from blog.models import Category
from django.utils.text import slugify


class Command(BaseCommand):
    help = 'Creates initial blog categories'

    def handle(self, *args, **options):
        categories = [
            "News & Politics",
            "Economy",
            "Education",
            "Laws / Legislation",
            "Immigration & Integration",
            "Labor Market / Job Market",
            "Events",
            "Buying & Selling",
            "Services",
            "History",
            "Health",
            "Swedish Language",
            "Leisure",
            "Music",
            "Film",
            "Art",
            "Sports",
        ]

        created_count = 0
        for category_name in categories:
            slug = slugify(category_name)
            category, created = Category.objects.get_or_create(
                slug=slug,
                defaults={'name': category_name}
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created category: {category_name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Category already exists: {category_name}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully processed {len(categories)} categories. '
                f'Created {created_count} new categories.'
            )
        )

