"""
Captcha helpers.

We use django-simple-captcha for signup. This module provides a digits-only
challenge to make the captcha clearer and easier for users.
"""

from __future__ import annotations

import secrets

from django.conf import settings


def numeric_challenge():
    """
    Digits-only CAPTCHA challenge.

    Returns a tuple (challenge, response). We keep them identical so the user
    simply types what they see.
    """

    length = getattr(settings, "CAPTCHA_LENGTH", 4) or 4
    code = "".join(str(secrets.randbelow(10)) for _ in range(int(length)))
    return code, code


