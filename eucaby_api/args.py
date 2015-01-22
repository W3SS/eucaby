"""Request arguments for API."""

import re
from eucaby_api.utils import reqparse


EMAIL_REGEX_PATTERN = '^[A-Z0-9\._%+-]+@[A-Z0-9\.-]+\.[A-Z]{2,4}$'  # pylint: disable=anomalous-backslash-in-string
POINT_REGEX_PATTERN = '-?[0-9]+\.?[0-9]*'  # pylint: disable=anomalous-backslash-in-string
LATLNG_REGEX_PATTERN = '^{p},{p}$'.format(p=POINT_REGEX_PATTERN)
EMAIL_REGEX = re.compile(EMAIL_REGEX_PATTERN, flags=re.IGNORECASE)
LATLNG_REGEX = re.compile(LATLNG_REGEX_PATTERN)

INVALID_EMAIL = 'Invalid email'
INVALID_LATLNG = 'Missing or invalid latlng parameter'
MISSING_EMAIL_USERNAME = 'Missing email or username parameters'
MISSING_EMAIL_USERNAME_REQ = 'Missing request_id, email or username parameters'


class ValidationError(Exception):
    pass


def email(s):
    """Validates email."""
    if EMAIL_REGEX.match(s):
        return s
    raise ValidationError("Invalid email")


def latlng(s):
    """Validates latlng."""
    if LATLNG_REGEX.match(s):
        return s
    raise ValidationError("Latlng should have format: <lat>,<lng>")


REQUEST_LOCATION_ARGS = [
    reqparse.Argument(name='email', type=email, help=INVALID_EMAIL),
    reqparse.Argument(name='username', type=str, help=MISSING_EMAIL_USERNAME)
]

NOTIFY_LOCATION_ARGS = [
    reqparse.Argument(name='email', type=email, help=INVALID_EMAIL),
    reqparse.Argument(name='username', type=str),
    reqparse.Argument(name='request_id', type=str),
    reqparse.Argument(name='latlng', type=latlng, required=True,
                      help=INVALID_LATLNG),
]