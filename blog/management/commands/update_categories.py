"""
Management command to update existing category names.
"""
from django.core.management.base import BaseCommand
from blog.models import Category
from django.utils.text import slugify


class Command(BaseCommand):
    help = 'Updates existing category names'

    def handle(self, *args, **options):
        # Category name updates
        updates = {
            'labor-market-job-market': 'Job Market',
            'laws-legislation': 'Laws',
        }
        
        updated_count = 0
        for old_slug, new_name in updates.items():
            try:
                category = Category.objects.get(slug=old_slug)
                category.name = new_name
                category.slug = slugify(new_name)
                category.save()
                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Updated category: {old_slug} -> {new_name}')
                )
            except Category.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'Category not found: {old_slug}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully updated {updated_count} categories.'
            )
        )

