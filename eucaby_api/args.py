"""Request arguments for API."""

import re
from flask_restful import inputs
from eucaby_api.utils import reqparse


ADMIN_EMAIL = 'alex@eucaby.com'
EMAIL_REGEX_PATTERN = '^[A-Z0-9\._%+-]+@[A-Z0-9\.-]+\.[A-Z]{2,4}$'  # pylint: disable=anomalous-backslash-in-string
POINT_REGEX_PATTERN = '-?[0-9]+\.?[0-9]*'  # pylint: disable=anomalous-backslash-in-string
LATLNG_REGEX_PATTERN = '^{p},{p}$'.format(p=POINT_REGEX_PATTERN)
EMAIL_REGEX = re.compile(EMAIL_REGEX_PATTERN, flags=re.IGNORECASE)
LATLNG_REGEX = re.compile(LATLNG_REGEX_PATTERN)

OUTGOING = 'outgoing'
INCOMING = 'incoming'
REQUEST = 'request'
NOTIFICATION = 'notification'
LOCATION = 'location'
ANDROID = 'android'
IOS = 'ios'
MISSING_PARAM = 'Missing {} parameter'
DEFAULT_ERROR = 'Something went wrong'
INVALID_EMAIL = 'Invalid email'
INVALID_LATLNG = 'Missing or invalid latlng parameter'
MISSING_EMAIL_USERNAME = 'Missing email or username parameters'
MISSING_EMAIL_USERNAME_REQ = (
    'Missing token, email or username parameters')
INVALID_ACTIVITY_TYPE = ('Activity type can be either outgoing, incoming, '
                         'request or notification')
INVALID_MESSAGE = 'Message type can be either {} or {}'.format(
    NOTIFICATION, REQUEST)
INVALID_PLATFORM = 'Platform can be either android or ios'
INVALID_INT = 'Integer type is expected'
ACTIVITY_CHOICES = [OUTGOING, INCOMING, REQUEST, NOTIFICATION]
PLATFORM_CHOICES = [ANDROID, IOS]
MESSAGE_CHOICES = [REQUEST, NOTIFICATION]
EMAIL_SUBSCRIPTION = 'email_subscription'
DAY = 60 * 60 * 24


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


def positive_int(v):
    """Validates positive."""
    # Note: There is a similar function in flask_rest/inputs.py:natural
    try:
        v = int(v)
    except ValueError:
        raise ValidationError(INVALID_INT)
    if v < 0:
        raise ValidationError(INVALID_INT)
    return v


REQUEST_LOCATION_ARGS = [
    reqparse.Argument(name='email', type=email, help=INVALID_EMAIL),
    reqparse.Argument(name='username', type=str, help=MISSING_EMAIL_USERNAME),
    reqparse.Argument(name='message', type=unicode)
]

NOTIFY_LOCATION_ARGS = [
    reqparse.Argument(name='email', type=email, help=INVALID_EMAIL),
    reqparse.Argument(name='username', type=str),
    reqparse.Argument(name='message', type=unicode),
    reqparse.Argument(name='token', type=str),
    reqparse.Argument(name='latlng', type=latlng, required=True,
                      help=INVALID_LATLNG),
]

ACTIVITY_ARGS = [
    reqparse.Argument(name='type', type=str, choices=ACTIVITY_CHOICES,
                      required=True, help=INVALID_ACTIVITY_TYPE),
    reqparse.Argument(name='offset', type=positive_int, default=0,
                      help=INVALID_INT),
    reqparse.Argument(name='limit', type=positive_int, default=200,
                      help=INVALID_INT)
]

SETTINGS_ARGS = [
    reqparse.Argument(name=EMAIL_SUBSCRIPTION, type=inputs.boolean)
]

REGISTER_DEVICE_ARGS = [
    reqparse.Argument(name='device_key', type=str, required=True,
                      help=MISSING_PARAM.format('device_key')),
    reqparse.Argument(name='platform', type=str, choices=PLATFORM_CHOICES,
                      required=True, help=INVALID_PLATFORM)
]

PUSH_TASK_ARGS = [
    reqparse.Argument(name='recipient_username', type=str, required=True,
                      help=MISSING_PARAM.format('recipient_username')),
    reqparse.Argument(name='sender_name', type=unicode),
    reqparse.Argument(name='message_type', type=str, choices=MESSAGE_CHOICES,
                      help=INVALID_MESSAGE, required=True),
    reqparse.Argument(name='message_id', type=positive_int, required=True,
                      help=MISSING_PARAM.format('message_id'))
]

MAIL_TASK_ARGS = [
    reqparse.Argument(name='subject', type=unicode, required=True,
                      help=MISSING_PARAM.format('subject')),
    reqparse.Argument(name='body', type=unicode, required=True,
                      help=MISSING_PARAM.format('body')),
    reqparse.Argument(name='recipient', type=unicode, action='append',
                      required=True, help=MISSING_PARAM.format('recipient'))
]

AUTO_ARGS = [
    reqparse.Argument(name='query', type=str, required=True,
                      help=MISSING_PARAM.format('query')),
    reqparse.Argument(name='limit', type=positive_int, default=5,
                      help=INVALID_INT)
]

