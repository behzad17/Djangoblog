"""
Admin interface for User model with email sending functionality.
"""
import logging
import secrets

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import path
from django.http import HttpResponseRedirect

from .admin_email import send_admin_bulk_email

logger = logging.getLogger(__name__)

SESSION_USER_IDS = 'email_user_ids'
SESSION_USER_COUNT = 'email_user_count'
SESSION_SEND_NONCE = 'email_send_nonce'
SESSION_SEND_LOCK = 'email_send_lock'


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
        user_ids = list(queryset.values_list('id', flat=True))
        request.session[SESSION_USER_IDS] = user_ids
        request.session[SESSION_USER_COUNT] = len(user_ids)
        request.session.pop(SESSION_SEND_NONCE, None)
        request.session.pop(SESSION_SEND_LOCK, None)
        request.session.modified = True

        from django.urls import reverse
        try:
            url = reverse('admin:auth_user_send_email')
        except Exception:
            model_info = self.model._meta
            url = f"/admin/{model_info.app_label}/{model_info.model_name}/send-email/"
        return HttpResponseRedirect(url)

    send_email_action.short_description = '📧 Send email to selected users'

    def _email_form_context(self, request, users, user_count, user_emails, subject='', message=''):
        """Build template context; ensure a one-time send nonce exists in session."""
        if request.method != 'POST':
            request.session[SESSION_SEND_NONCE] = secrets.token_urlsafe(32)
            request.session.modified = True
        return {
            'users': users,
            'user_count': user_count,
            'user_emails': user_emails,
            'subject': subject,
            'message': message,
            'send_nonce': request.session.get(SESSION_SEND_NONCE, ''),
        }

    def _clear_email_session(self, request):
        request.session.pop(SESSION_USER_IDS, None)
        request.session.pop(SESSION_USER_COUNT, None)
        request.session.pop(SESSION_SEND_NONCE, None)
        request.session.pop(SESSION_SEND_LOCK, None)
        request.session.modified = True

    def _validate_send_nonce(self, request):
        """
        Verify POST nonce and consume it so the same form cannot be processed twice.
        Returns True if valid; False if duplicate, invalid, or concurrent send.
        """
        post_nonce = request.POST.get('send_nonce', '').strip()
        session_nonce = request.session.get(SESSION_SEND_NONCE)

        if not post_nonce or not session_nonce or post_nonce != session_nonce:
            return False

        if request.session.get(SESSION_SEND_LOCK):
            return False

        # Consume nonce before sending so a replay cannot reuse it.
        request.session.pop(SESSION_SEND_NONCE, None)
        request.session[SESSION_SEND_LOCK] = True
        request.session.modified = True
        return True

    def send_email_view(self, request):
        """View to display email form and handle email sending."""
        user_ids = request.session.get(SESSION_USER_IDS, [])
        user_count = request.session.get(SESSION_USER_COUNT, 0)

        if not user_ids:
            messages.error(request, 'No users selected. Please select users from the list first.')
            return redirect('admin:auth_user_changelist')

        users = User.objects.filter(id__in=user_ids)
        user_emails = [user.email for user in users if user.email]

        if request.method == 'POST':
            subject = request.POST.get('subject', '').strip()
            message = request.POST.get('message', '').strip()

            def form_context():
                return self._email_form_context(
                    request, users, user_count, user_emails, subject, message
                )

            if not subject:
                messages.error(request, 'Subject is required.')
                return render(
                    request,
                    'admin/accounts/user/send_email_form.html',
                    form_context(),
                )

            if not message:
                messages.error(request, 'Message is required.')
                return render(
                    request,
                    'admin/accounts/user/send_email_form.html',
                    form_context(),
                )

            if not self._validate_send_nonce(request):
                messages.warning(
                    request,
                    'This email batch was already sent or is being processed. '
                    'Please select users again if you need to send another message.',
                )
                self._clear_email_session(request)
                return redirect('admin:auth_user_changelist')

            success_count = 0
            failed_count = 0
            failed_emails = []
            sent_addresses = set()

            try:
                for user in users:
                    if not user.email:
                        failed_count += 1
                        failed_emails.append(f"{user.username} (no email)")
                        continue

                    normalized = user.email.strip().lower()
                    if normalized in sent_addresses:
                        continue
                    sent_addresses.add(normalized)

                    try:
                        send_admin_bulk_email(subject, message, user.email)
                        success_count += 1
                        logger.info(
                            "Admin bulk email sent to %s (%s) by %s",
                            user.username,
                            user.email,
                            request.user.username,
                        )
                    except Exception as e:
                        failed_count += 1
                        failed_emails.append(f"{user.username} ({user.email})")
                        logger.error(
                            "Error sending admin bulk email to %s (%s): %s",
                            user.username,
                            user.email,
                            e,
                        )
            finally:
                self._clear_email_session(request)

            if success_count > 0:
                messages.success(
                    request,
                    f'Successfully sent email to {success_count} user(s).',
                )
            if failed_count > 0:
                messages.warning(
                    request,
                    f'Failed to send email to {failed_count} user(s): {", ".join(failed_emails[:5])}'
                    + ('...' if len(failed_emails) > 5 else ''),
                )

            return redirect('admin:auth_user_changelist')

        return render(
            request,
            'admin/accounts/user/send_email_form.html',
            self._email_form_context(request, users, user_count, user_emails),
        )


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
