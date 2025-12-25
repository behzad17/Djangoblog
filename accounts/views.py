"""
Account views for user account management.
"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def account_settings(request):
    """
    Account settings page that provides links to change password and email.
    """
    return render(request, 'account/settings.html')

