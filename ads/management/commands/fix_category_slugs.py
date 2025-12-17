"""
Management command to fix categories with empty or missing slugs.
"""
from django.core.management.base import BaseCommand
from ads.models import AdCategory
from django.utils.text import slugify


class Command(BaseCommand):
    help = 'Fixes categories with empty or missing slugs'

    def handle(self, *args, **options):
        categories = AdCategory.objects.filter(slug__isnull=True) | AdCategory.objects.filter(slug='')
        
        if not categories.exists():
            self.stdout.write(
                self.style.SUCCESS('No categories with empty slugs found.')
            )
            return
        
        fixed_count = 0
        for category in categories:
            if not category.name:
                self.stdout.write(
                    self.style.WARNING(f'Skipping category {category.id} - no name')
                )
                continue
            
            base_slug = slugify(category.name)
            slug = base_slug
            counter = 1
            
            # Ensure slug is unique
            while AdCategory.objects.filter(slug=slug).exclude(pk=category.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            category.slug = slug
            category.save()
            fixed_count += 1
            self.stdout.write(
                self.style.SUCCESS(f'Fixed category "{category.name}" -> slug: {slug}')
            )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nFixed {fixed_count} categories with empty slugs.'
            )
        )

