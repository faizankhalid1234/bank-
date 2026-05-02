#!/usr/bin/env python
"""Django CLI — runs from ``backend/`` so you can call ``python manage.py`` from repo root."""

import os
import sys

_BACKEND = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
sys.path.insert(0, _BACKEND)
os.chdir(_BACKEND)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alybank.settings")

try:
    from django.core.management import execute_from_command_line
except ImportError as exc:
    raise ImportError(
        "Couldn't import Django. Activate your venv and install backend/requirements.txt."
    ) from exc

if __name__ == "__main__":
    execute_from_command_line(sys.argv)
