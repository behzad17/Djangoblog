"""
Management command to check Google OAuth setup and show required redirect URIs.

Usage:
    python manage.py check_oauth_setup
    python manage.py check_oauth_setup --fix-site-domain
"""
from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from django.conf import settings
from allauth.socialaccount.models import SocialApp


class Command(BaseCommand):
    help = 'Check Google OAuth setup and display required redirect URIs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix-site-domain',
            action='store_true',
            help='Automatically update Site domain based on environment',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('Google OAuth Setup Check'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write()

        # Check Site configuration
        self.stdout.write(self.style.WARNING('1. Django Sites Framework Configuration:'))
        self.stdout.write('-' * 70)
        try:
            site = Site.objects.get(id=settings.SITE_ID)
            self.stdout.write(f'   Current Site ID: {site.id}')
            self.stdout.write(f'   Current Domain: {site.domain}')
            self.stdout.write(f'   Current Name: {site.name}')
            
            # Determine what the domain should be
            if not settings.DEBUG:
                # Production: prefer custom domain, fallback to Heroku
                if 'peyvand.se' in settings.ALLOWED_HOSTS:
                    recommended_domain = 'peyvand.se'
                elif 'djangoblog17-173e7e5e5186.herokuapp.com' in settings.ALLOWED_HOSTS:
                    recommended_domain = 'djangoblog17-173e7e5e5186.herokuapp.com'
                else:
                    recommended_domain = settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'example.com'
            else:
                # Development
                recommended_domain = 'localhost:8000'
            
            if site.domain != recommended_domain:
                self.stdout.write(self.style.WARNING(
                    f'   ⚠️  Domain mismatch! Recommended: {recommended_domain}'
                ))
                if options['fix_site_domain']:
                    site.domain = recommended_domain
                    site.name = 'Peyvand' if not settings.DEBUG else 'Peyvand (Development)'
                    site.save()
                    self.stdout.write(self.style.SUCCESS(
                        f'   ✓ Fixed: Updated domain to {recommended_domain}'
                    ))
                else:
                    self.stdout.write(self.style.WARNING(
                        '   Run with --fix-site-domain to automatically update'
                    ))
            else:
                self.stdout.write(self.style.SUCCESS('   ✓ Domain is correctly configured'))
            
        except Site.DoesNotExist:
            self.stdout.write(self.style.ERROR('   ✗ Site not found!'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ✗ Error: {e}'))
        
        self.stdout.write()

        # Check SocialApp configuration
        self.stdout.write(self.style.WARNING('2. Google OAuth App Configuration:'))
        self.stdout.write('-' * 70)
        try:
            social_app = SocialApp.objects.get(provider='google')
            self.stdout.write(f'   Provider: {social_app.provider}')
            self.stdout.write(f'   Name: {social_app.name}')
            self.stdout.write(f'   Client ID: {social_app.client_id[:20]}...' if social_app.client_id else '   Client ID: Not set')
            self.stdout.write(self.style.SUCCESS('   ✓ Google OAuth app is configured'))
        except SocialApp.DoesNotExist:
            self.stdout.write(self.style.ERROR('   ✗ Google OAuth app not found in database!'))
            self.stdout.write('   You need to create it in Django Admin:')
            self.stdout.write('   - Go to /admin/socialaccount/socialapp/')
            self.stdout.write('   - Add new Social Application')
            self.stdout.write('   - Provider: Google')
            self.stdout.write('   - Name: Google')
            self.stdout.write('   - Client ID: (from Google Cloud Console)')
            self.stdout.write('   - Secret key: (from Google Cloud Console)')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ✗ Error: {e}'))
        
        self.stdout.write()

        # Show required redirect URIs
        self.stdout.write(self.style.WARNING('3. Required Redirect URIs for Google Cloud Console:'))
        self.stdout.write('-' * 70)
        self.stdout.write('   Add these EXACT URIs to your Google OAuth 2.0 Client ID:')
        self.stdout.write('   (Google Cloud Console > APIs & Services > Credentials)')
        self.stdout.write()
        
        # Get current site domain
        try:
            site = Site.objects.get(id=settings.SITE_ID)
            current_domain = site.domain
        except:
            current_domain = 'example.com'
        
        # Generate redirect URIs for all environments
        domains = []
        if not settings.DEBUG:
            # Production domains
            if 'peyvand.se' in settings.ALLOWED_HOSTS:
                domains.append('peyvand.se')
            if 'www.peyvand.se' in settings.ALLOWED_HOSTS:
                domains.append('www.peyvand.se')
            if 'djangoblog17-173e7e5e5186.herokuapp.com' in settings.ALLOWED_HOSTS:
                domains.append('djangoblog17-173e7e5e5186.herokuapp.com')
        else:
            # Development domains
            domains.extend(['localhost:8000', '127.0.0.1:8000'])
        
        # Also include current site domain if not already in list
        if current_domain not in domains:
            domains.append(current_domain)
        
        redirect_uris = []
        for domain in sorted(set(domains)):
            if 'localhost' in domain or '127.0.0.1' in domain:
                protocol = 'http'
            else:
                protocol = 'https'
            redirect_uri = f"{protocol}://{domain}/accounts/google/login/callback/"
            redirect_uris.append(redirect_uri)
            self.stdout.write(self.style.SUCCESS(f'   {redirect_uri}'))
        
        self.stdout.write()
        self.stdout.write(self.style.WARNING('4. Instructions:'))
        self.stdout.write('-' * 70)
        self.stdout.write('   1. Go to: https://console.cloud.google.com/apis/credentials')
        self.stdout.write('   2. Click on your OAuth 2.0 Client ID')
        self.stdout.write('   3. Under "Authorized redirect URIs", click "ADD URI"')
        self.stdout.write('   4. Add ALL the URIs listed above (one by one)')
        self.stdout.write('   5. Click "SAVE"')
        self.stdout.write()
        self.stdout.write('   Important Notes:')
        self.stdout.write('   - URIs must match EXACTLY (including trailing slash)')
        self.stdout.write('   - Use https:// for production, http:// for localhost')
        self.stdout.write('   - No wildcards allowed')
        self.stdout.write()
        
        # Check if credentials are set
        self.stdout.write(self.style.WARNING('5. Environment Variables:'))
        self.stdout.write('-' * 70)
        import os
        google_client_id = os.environ.get("GOOGLE_CLIENT_ID")
        google_client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
        
        if google_client_id:
            self.stdout.write(self.style.SUCCESS('   ✓ GOOGLE_CLIENT_ID is set'))
        else:
            self.stdout.write(self.style.ERROR('   ✗ GOOGLE_CLIENT_ID is NOT set'))
        
        if google_client_secret:
            self.stdout.write(self.style.SUCCESS('   ✓ GOOGLE_CLIENT_SECRET is set'))
        else:
            self.stdout.write(self.style.ERROR('   ✗ GOOGLE_CLIENT_SECRET is NOT set'))
        
        self.stdout.write()
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('Check complete!'))
        self.stdout.write(self.style.SUCCESS('=' * 70))

