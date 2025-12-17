"""
Management command to fix categories with empty or missing slugs.
"""
from django.core.management.base import BaseCommand
from ads.models import AdCategory
from django.utils.text import slugify
import re


def create_slug_from_persian(text):
    """
    Create a slug from Persian text by transliterating to English.
    Falls back to a simple slug if transliteration fails.
    """
    # Persian to English transliteration map
    transliteration_map = {
        'وسایل نقلیه': 'vehicles',
        'مسکن': 'housing',
        'کار و خدمات': 'work-services',
        'اوقات فراغت': 'leisure',
        'غذا و رستوران': 'food-restaurant',
        'سلامت و رفاه': 'health-welfare',
        'وسایل منزل': 'home-appliances',
        'حقوقی و مالی': 'legal-financial',
    }
    
    # Check if we have a direct mapping
    if text in transliteration_map:
        return transliteration_map[text]
    
    # Fallback: try slugify, if empty use a simple replacement
    slug = slugify(text)
    if not slug:
        # Create a simple slug from the text
        slug = text.lower().replace(' ', '-').replace('و', '-')
        slug = re.sub(r'[^\w\-]', '', slug)
        if not slug:
            slug = f'category-{hash(text) % 10000}'
    
    return slug


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
            
            base_slug = create_slug_from_persian(category.name)
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

