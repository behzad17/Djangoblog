"""
Management command to create initial ad categories.
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
        'خدمات مالی': 'economi',
        'خدمات اداری و اجتماعی': 'social-zendegi',
        'خدمات شغلی و حرفه‌ای': 'work-services',
        'رفاه و سرگرمی': 'leisure',
        'رستوران، کافه و مواد غذایی': 'food-restaurant',
        'خدمات پزشکی و سلامت': 'health-welfare',
        'بهداشت و زیبایی': 'beauty-appliances',
        'خدمات حقوقی': 'legal-financial',
        'خدمات آموزشی': 'mozsh-zbn-o-dr',
        'فناوری و توسعه وب': 'fnor-o-khdmt-dgtl',
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
    help = 'Creates initial ad categories'

    def handle(self, *args, **options):
        categories = [
            "خدمات مالی",
            "خدمات اداری و اجتماعی",
            "خدمات شغلی و حرفه‌ای",
            "رفاه و سرگرمی",
            "رستوران، کافه و مواد غذایی",
            "خدمات پزشکی و سلامت",
            "بهداشت و زیبایی",
            "خدمات حقوقی",
            "خدمات آموزشی",
            "فناوری و توسعه وب",
        ]

        created_count = 0
        updated_count = 0
        for category_name in categories:
            slug = create_slug_from_persian(category_name)
            # Use name as the unique identifier since it's the unique field
            try:
                category, created = AdCategory.objects.get_or_create(
                    name=category_name,
                    defaults={'slug': slug}
                )
                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'Created category: {category_name} (slug: {slug})')
                    )
                else:
                    # Update slug if it's missing, empty, or incorrect
                    if not category.slug or category.slug == '' or category.slug != slug:
                        # Check if the slug is already taken by another category
                        existing_with_slug = AdCategory.objects.filter(slug=slug).exclude(pk=category.pk).first()
                        if existing_with_slug:
                            # Generate a unique slug
                            base_slug = slug
                            counter = 1
                            while AdCategory.objects.filter(slug=slug).exclude(pk=category.pk).exists():
                                slug = f"{base_slug}-{counter}"
                                counter += 1
                        category.slug = slug
                        category.save()
                        updated_count += 1
                        self.stdout.write(
                            self.style.WARNING(f'Updated slug for category: {category_name} -> {slug}')
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(f'Category already exists: {category_name}')
                        )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error processing {category_name}: {str(e)}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully processed {len(categories)} categories. '
                f'Created {created_count} new categories. '
                f'Updated {updated_count} existing categories.'
            )
        )

