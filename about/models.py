"""
Models for the 'About' section and collaboration requests.
"""

from django.db import models


class About(models.Model):
    """
    Model representing the 'About' section content.
    """
    title = models.CharField(max_length=200)
    content = models.TextField(default="Welcome to our platform — a space created with purpose and heart.\nThis website is founded by a former journalist who now works in the field of integration, supporting immigrants in Sweden. The idea behind this platform is to build a dedicated space for Iranians living in Sweden — a place where voices can be heard, experiences can be shared, and a sense of community can grow.\n\nOur mission is to create a media hub where anyone, regardless of background or experience, can publish their personal stories, insights, and perspectives. Whether you're navigating life as a newcomer or sharing years of experience, your voice matters here.\n\nThis site aspires to become a central place for communication, connection, and support — a Stella of storytelling and solidarity among the Iranian community in Sweden.\n\nTogether, let's bring people closer.")
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class CollaborateRequest(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} - {self.email}"

