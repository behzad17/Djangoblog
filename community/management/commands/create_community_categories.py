"""Create initial community discussion categories."""
from django.core.management.base import BaseCommand

from community.models import CommunityCategory


class Command(BaseCommand):
    help = 'Creates initial community discussion categories'

    def handle(self, *args, **options):
        categories = [
            ('مهاجرت و اقامت', 'immigration-residency', 1),
            ('کار و تحصیل', 'work-education', 2),
            ('زندگی روزمره', 'daily-life', 3),
            ('حقوق و قوانین', 'law-legal', 4),
            ('سلامت', 'health', 5),
            ('فرهنگ و رویدادها', 'culture-events', 6),
            ('خرید و فروش', 'buy-sell', 7),
            ('عمومی', 'general', 8),
        ]

        created_count = 0
        for name, slug, display_order in categories:
            category, created = CommunityCategory.objects.get_or_create(
                slug=slug,
                defaults={
                    'name': name,
                    'display_order': display_order,
                    'is_active': True,
                },
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created category: {name} ({slug})')
                )
            else:
                updated = False
                if category.name != name:
                    category.name = name
                    updated = True
                if category.display_order != display_order:
                    category.display_order = display_order
                    updated = True
                if not category.is_active:
                    category.is_active = True
                    updated = True
                if updated:
                    category.save()
                    self.stdout.write(
                        self.style.WARNING(f'Updated category: {name} ({slug})')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'Category already exists: {name}')
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nProcessed {len(categories)} categories. '
                f'Created {created_count} new categories.'
            )
        )
