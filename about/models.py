"""
Models for the 'About' section and collaboration requests.
"""

from django.db import models
from django.template import Origin, TemplateDoesNotExist
from django.template.loaders.base import Loader as BaseLoader


class Loader(BaseLoader):
    """
    Custom loader to load templates from a plain Python dictionary.
    """
    def __init__(self, engine, templates_dict):
        self.templates_dict = templates_dict
        super().__init__(engine)

    def get_contents(self, origin):
        try:
            return self.templates_dict[origin.name]
        except KeyError:
            raise TemplateDoesNotExist(origin)

    def get_template_sources(self, template_name):
        yield Origin(
            name=template_name,
            template_name=template_name,
            loader=self,
        )


class About(models.Model):
    """
    Model representing the 'About' section content.
    """
    title = models.CharField(max_length=200)
    content = models.TextField()

    def __str__(self):
        return self.title


class CollaborateRequest(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} - {self.email}"

