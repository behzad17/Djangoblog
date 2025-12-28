from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse
from .models import About
from .forms import CollaborateForm


def about_me(request):
    about = About.objects.all().order_by('-updated_on').first()
    
    if request.method == "POST":
        collaborate_form = CollaborateForm(data=request.POST)
        if collaborate_form.is_valid():
            collaborate_form.save()
            messages.add_message(request, messages.SUCCESS, "Collaboration request received! I endeavour to respond within 2 working days.")
            # Redirect to prevent form resubmission (PRG pattern)
            return redirect(reverse('about') + '#contact')
        else:
            # Invalid form: render with errors
            return render(
                request,
                "about/about.html",
                {
                    "about": about,
                    "collaborate_form": collaborate_form
                },
            )
    
    # GET request: render with empty form
    collaborate_form = CollaborateForm()
    return render(
        request,
        "about/about.html",
        {
            "about": about,
            "collaborate_form": collaborate_form
        },
    )


def terms_and_conditions(request):
    """View for Terms and Conditions page."""
    return render(request, "about/terms.html")


def member_guide(request):
    """View for Member Guide page."""
    return render(request, "about/member_guide.html")


def integritetspolicy(request):
    """View for Integritetspolicy (Privacy Policy) page."""
    return render(request, "about/integritetspolicy.html")
    
