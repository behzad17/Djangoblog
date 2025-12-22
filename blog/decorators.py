from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse


def site_verified_required(view_func):
    """
    Decorator to require site verification for write actions.
    
    Users must have is_site_verified=True to perform write actions.
    Redirects to complete_setup page if not verified.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            # Let @login_required handle this
            return view_func(request, *args, **kwargs)
        
        # Check if user has site verification
        if hasattr(request.user, 'profile'):
            if not request.user.profile.is_site_verified:
                messages.warning(
                    request,
                    'لطفاً ابتدا تنظیمات حساب کاربری خود را تکمیل کنید.'
                )
                return redirect('complete_setup')
        else:
            # No profile exists, redirect to setup
            messages.warning(
                request,
                'لطفاً ابتدا تنظیمات حساب کاربری خود را تکمیل کنید.'
            )
            return redirect('complete_setup')
        
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view

