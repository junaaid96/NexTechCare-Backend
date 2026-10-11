"""Demo mode: one-click demo accounts with server-side guards.

Demo users are identified by the `demo_` username prefix. Their data is wiped
and re-created by `python manage.py seed_demo` (also run nightly by Vercel Cron
through /profiles/demo/reset/). Guards keep demo sessions from touching real
users or destroying data.
"""
from rest_framework.exceptions import PermissionDenied

DEMO_PREFIX = 'demo_'
DEMO_ACCOUNTS = {'C': 'demo_customer', 'E': 'demo_engineer', 'A': 'demo_admin'}
DEMO_MESSAGE = 'This action is disabled in the demo. Create a free account to try it for real.'


def is_demo(user):
    return bool(user and user.is_authenticated and user.username.startswith(DEMO_PREFIX))


def is_demo_username(username):
    return (username or '').startswith(DEMO_PREFIX)


def block_if_demo(request, message=DEMO_MESSAGE):
    if is_demo(request.user):
        raise PermissionDenied(message)
