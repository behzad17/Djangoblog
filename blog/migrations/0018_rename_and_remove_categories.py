"""
Migration to rename categories and remove unwanted categories.

This migration:
1. Renames existing categories to new names
2. Reassigns posts from removed categories to "Platform Updates"
3. Deletes removed categories
"""
from django.db import migrations
from django.utils.text import slugify


def rename_and_remove_categories(apps, schema_editor):
    """
    Rename categories and handle removed categories.
    """
    Category = apps.get_model('blog', 'Category')
    Post = apps.get_model('blog', 'Post')
    
    # Category rename mappings: old_name -> new_name
    # Note: "News & Politics" -> "Platform Updates" is handled separately above
    rename_map = {
        'Economy': 'Careers & Economy',
        'Immigration & Integration': 'Law & Integration',
        'Job Market': 'Life in Sweden',
        'Laws': 'Skills & Learning',
        'Events': 'Events & Announcements',
        'Photo': 'Photo Gallery',
        'Buying & Selling': 'Public Services',
        'Health': 'Stories & Experiences',
        'Swedish Language': 'Community & Engagement',
    }
    
    # Categories to remove
    categories_to_remove = [
        'Education',
        'Art',
        'Film',
        'History',
        'Music',
        'Sports',
        'Services',
    ]
    
    # First, handle "News & Politics" -> "Platform Updates" rename separately
    # This ensures Platform Updates exists before we reassign posts
    try:
        news_politics = Category.objects.get(name='News & Politics')
        news_politics.name = 'Platform Updates'
        news_politics.slug = 'platform-updates'
        news_politics.save()
        platform_updates = news_politics
    except Category.DoesNotExist:
        # Check if Platform Updates already exists
        try:
            platform_updates = Category.objects.get(name='Platform Updates')
        except Category.DoesNotExist:
            # Create new if neither exists
            platform_updates = Category.objects.create(
                name='Platform Updates',
                slug='platform-updates',
                description=''
            )
    
    # Rename other categories (excluding News & Politics which we already handled)
    for old_name, new_name in rename_map.items():
        try:
            category = Category.objects.get(name=old_name)
            category.name = new_name
            category.slug = slugify(new_name)
            category.save()
            print(f"Renamed: {old_name} -> {new_name}")
        except Category.DoesNotExist:
            print(f"Category not found for renaming: {old_name}")
    
    # Reassign posts from removed categories and delete categories
    for category_name in categories_to_remove:
        try:
            category = Category.objects.get(name=category_name)
            # Reassign all posts to Platform Updates
            Post.objects.filter(category=category).update(category=platform_updates)
            print(f"Reassigned posts from '{category_name}' to 'Platform Updates'")
            # Delete the category
            category.delete()
            print(f"Deleted category: {category_name}")
        except Category.DoesNotExist:
            print(f"Category not found for deletion: {category_name}")


def reverse_migration(apps, schema_editor):
    """
    Reverse migration - restore original category names.
    Note: This won't restore deleted categories or reassigned posts.
    """
    Category = apps.get_model('blog', 'Category')
    
    # Reverse rename mappings: new_name -> old_name
    reverse_rename_map = {
        'Careers & Economy': 'Economy',
        'Law & Integration': 'Immigration & Integration',
        'Life in Sweden': 'Job Market',
        'Skills & Learning': 'Laws',
        'Platform Updates': 'News & Politics',
        'Events & Announcements': 'Events',
        'Photo Gallery': 'Photo',
        'Public Services': 'Buying & Selling',
        'Stories & Experiences': 'Health',
        'Community & Engagement': 'Swedish Language',
    }
    
    for new_name, old_name in reverse_rename_map.items():
        try:
            category = Category.objects.get(name=new_name)
            category.name = old_name
            category.slug = slugify(old_name)
            category.save()
        except Category.DoesNotExist:
            pass


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0017_post_event_end_date_post_event_start_date'),
    ]

    operations = [
        migrations.RunPython(rename_and_remove_categories, reverse_migration),
    ]

