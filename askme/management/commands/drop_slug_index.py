"""
Management command to drop existing slug indexes from askme_moderator table.

This command is useful when preparing to run migration 0003_add_expert_profile_fields
and there are leftover indexes from previous failed migration attempts.
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Drops existing slug-related indexes from askme_moderator table'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be dropped without actually dropping',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # List of known index names that might exist
        index_names = [
            'askme_moderator_slug_9dcc5146_like',
            'askme_moderator_slug_idx',
            'askme_moderator_slug_unique',
        ]
        
        with connection.cursor() as cursor:
            # First, find all slug-related indexes
            cursor.execute("""
                SELECT indexname 
                FROM pg_indexes 
                WHERE tablename = 'askme_moderator' 
                AND indexname LIKE '%slug%';
            """)
            found_indexes = [row[0] for row in cursor.fetchall()]
            
            # Combine known indexes with found indexes
            all_indexes = list(set(index_names + found_indexes))
            
            if not all_indexes:
                self.stdout.write(
                    self.style.SUCCESS('No slug-related indexes found. Nothing to drop.')
                )
                return
            
            self.stdout.write(
                self.style.WARNING(f'Found {len(all_indexes)} slug-related index(es):')
            )
            for idx in all_indexes:
                self.stdout.write(f'  - {idx}')
            
            if dry_run:
                self.stdout.write(
                    self.style.WARNING('\nDRY RUN: Would drop the above indexes.')
                )
                return
            
            # Drop each index
            dropped_count = 0
            for index_name in all_indexes:
                try:
                    # Try dropping with schema qualification
                    cursor.execute(f'DROP INDEX IF EXISTS public.{index_name};')
                    # Also try without schema (in case it's already qualified)
                    cursor.execute(f'DROP INDEX IF EXISTS {index_name};')
                    
                    # Check if index still exists
                    cursor.execute("""
                        SELECT COUNT(*) 
                        FROM pg_indexes 
                        WHERE indexname = %s AND tablename = 'askme_moderator';
                    """, [index_name])
                    still_exists = cursor.fetchone()[0] > 0
                    
                    if not still_exists:
                        self.stdout.write(
                            self.style.SUCCESS(f'✓ Dropped index: {index_name}')
                        )
                        dropped_count += 1
                    else:
                        # Try with CASCADE in case there are dependencies
                        try:
                            cursor.execute(f'DROP INDEX IF EXISTS {index_name} CASCADE;')
                            cursor.execute("""
                                SELECT COUNT(*) 
                                FROM pg_indexes 
                                WHERE indexname = %s AND tablename = 'askme_moderator';
                            """, [index_name])
                            if cursor.fetchone()[0] == 0:
                                self.stdout.write(
                                    self.style.SUCCESS(f'✓ Dropped index (with CASCADE): {index_name}')
                                )
                                dropped_count += 1
                            else:
                                self.stdout.write(
                                    self.style.WARNING(f'  Could not drop index: {index_name}')
                                )
                        except Exception as e2:
                            self.stdout.write(
                                self.style.WARNING(f'  Could not drop index {index_name}: {e2}')
                            )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'✗ Error dropping {index_name}: {e}')
                    )
            
            if dropped_count > 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'\nSuccessfully dropped {dropped_count} index(es). '
                        'You can now run: python manage.py migrate askme'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING('\nNo indexes were dropped.')
                )

