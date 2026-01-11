"""
Admin interface for User model with email sending functionality.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import path
from django.http import HttpResponseRedirect
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class UserAdmin(BaseUserAdmin):
    """Extended User admin with email sending action."""
    
    actions = ['send_email_action']
    
    def get_urls(self):
        """Add custom URL for email form."""
        urls = super().get_urls()
        custom_urls = [
            path(
                'send-email/',
                self.admin_site.admin_view(self.send_email_view),
                name='auth_user_send_email',
            ),
        ]
        return custom_urls + urls
    
    def send_email_action(self, request, queryset):
        """Admin action to send emails to selected users."""
        # Store selected user IDs in session
        user_ids = list(queryset.values_list('id', flat=True))
        request.session['email_user_ids'] = user_ids
        request.session['email_user_count'] = len(user_ids)
        request.session.modified = True  # Ensure session is saved
        
        # Redirect to email form
        # Build URL: /admin/auth/user/send-email/
        from django.urls import reverse
        try:
            # Try using reverse with the URL name
            url = reverse('admin:auth_user_send_email')
        except Exception:
            # Fallback: construct URL manually
            model_info = self.model._meta
            url = f"/admin/{model_info.app_label}/{model_info.model_name}/send-email/"
        return HttpResponseRedirect(url)
    
    send_email_action.short_description = '📧 Send email to selected users'
    
    def send_email_view(self, request):
        """View to display email form and handle email sending."""
        # Get user IDs from session
        user_ids = request.session.get('email_user_ids', [])
        user_count = request.session.get('email_user_count', 0)
        
        if not user_ids:
            messages.error(request, 'No users selected. Please select users from the list first.')
            return redirect('admin:auth_user_changelist')
        
        # Get users
        users = User.objects.filter(id__in=user_ids)
        user_emails = [user.email for user in users if user.email]
        
        if request.method == 'POST':
            subject = request.POST.get('subject', '').strip()
            message = request.POST.get('message', '').strip()
            
            if not subject:
                messages.error(request, 'Subject is required.')
                return render(request, 'admin/accounts/user/send_email_form.html', {
                    'users': users,
                    'user_count': user_count,
                    'user_emails': user_emails,
                    'subject': subject,
                    'message': message,
                })
            
            if not message:
                messages.error(request, 'Message is required.')
                return render(request, 'admin/accounts/user/send_email_form.html', {
                    'users': users,
                    'user_count': user_count,
                    'user_emails': user_emails,
                    'subject': subject,
                    'message': message,
                })
            
            # Send emails
            success_count = 0
            failed_count = 0
            failed_emails = []
            
            for user in users:
                if not user.email:
                    failed_count += 1
                    failed_emails.append(f"{user.username} (no email)")
                    continue
                
                try:
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        [user.email],
                        fail_silently=False,
                    )
                    success_count += 1
                    logger.info(f"Email sent to {user.username} ({user.email}) by admin {request.user.username}")
                except Exception as e:
                    failed_count += 1
                    failed_emails.append(f"{user.username} ({user.email})")
                    logger.error(f"Error sending email to {user.username} ({user.email}): {e}")
            
            # Clear session
            request.session.pop('email_user_ids', None)
            request.session.pop('email_user_count', None)
            
            # Show results
            if success_count > 0:
                messages.success(
                    request,
                    f'Successfully sent email to {success_count} user(s).'
                )
            if failed_count > 0:
                messages.warning(
                    request,
                    f'Failed to send email to {failed_count} user(s): {", ".join(failed_emails[:5])}'
                    + ('...' if len(failed_emails) > 5 else '')
                )
            
            return redirect('admin:auth_user_changelist')
        
        # GET request - show form
        return render(request, 'admin/accounts/user/send_email_form.html', {
            'users': users,
            'user_count': user_count,
            'user_emails': user_emails,
            'subject': '',
            'message': '',
        })


# Unregister default User admin and register custom one
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

