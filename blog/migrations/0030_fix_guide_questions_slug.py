"""
Data migration to fix the slug for "پرسش و راهنمایی" category.

Changes slug from "Guide-Questions" to "guide-questions" to maintain
consistency with lowercase kebab-case slugs used throughout the project.
"""

from django.db import migrations


def fix_guide_questions_slug(apps, schema_editor):
    """
    Update the slug for "پرسش و راهنمایی" category from "Guide-Questions" to "guide-questions".
    
    IDEMPOTENT: Only updates if the slug is currently "Guide-Questions".
    Safe to run multiple times.
    """
    Category = apps.get_model('blog', 'Category')
    
    # Find the category by its Persian name
    try:
        category = Category.objects.get(name='پرسش و راهنمایی')
        
        # Only update if slug is currently "Guide-Questions"
        # This makes the migration idempotent
        if category.slug == 'Guide-Questions':
            category.slug = 'guide-questions'
            category.save(update_fields=['slug'])
            print(f"Updated slug for category '{category.name}': Guide-Questions -> guide-questions")
        elif category.slug == 'guide-questions':
            print(f"Slug for category '{category.name}' is already correct: guide-questions")
        else:
            print(f"Warning: Category '{category.name}' has unexpected slug: {category.slug}")
    except Category.DoesNotExist:
        print("Category 'پرسش و راهنمایی' not found. Skipping slug update.")
    except Category.MultipleObjectsReturned:
        print("Error: Multiple categories found with name 'پرسش و راهنمایی'. Manual intervention required.")


def reverse_fix_guide_questions_slug(apps, schema_editor):
    """
    Reverse migration: Change slug back from "guide-questions" to "Guide-Questions".
    
    IDEMPOTENT: Only updates if the slug is currently "guide-questions".
    """
    Category = apps.get_model('blog', 'Category')
    
    try:
        category = Category.objects.get(name='پرسش و راهنمایی')
        
        # Only reverse if slug is currently "guide-questions"
        if category.slug == 'guide-questions':
            category.slug = 'Guide-Questions'
            category.save(update_fields=['slug'])
            print(f"Reverted slug for category '{category.name}': guide-questions -> Guide-Questions")
        else:
            print(f"Category '{category.name}' has slug '{category.slug}', not reverting.")
    except Category.DoesNotExist:
        print("Category 'پرسش و راهنمایی' not found. Skipping reverse migration.")
    except Category.MultipleObjectsReturned:
        print("Error: Multiple categories found with name 'پرسش و راهنمایی'. Manual intervention required.")


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0029_alter_postviewcount_options_and_more'),
    ]

    operations = [
        migrations.RunPython(
            fix_guide_questions_slug,
            reverse_code=reverse_fix_guide_questions_slug
        ),
    ]

