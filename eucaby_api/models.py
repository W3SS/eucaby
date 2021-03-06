"""SQL models for API service."""

import datetime
import flask
import flask_sqlalchemy
from sqlalchemy_utils.types import choice

from google.appengine.api import memcache

from eucaby_api import args as api_args
from eucaby_api.utils import utils as api_utils
from eucaby_api.utils import date as utils_date

db = flask_sqlalchemy.SQLAlchemy(session_options=dict(expire_on_commit=False))

FACEBOOK = 'facebook'
EUCABY = 'eucaby'
EUCABY_SCOPES = ['profile', 'history', 'location']

SERVICE_TYPES = [
    (EUCABY, 'Eucaby'),
    (FACEBOOK, 'Facebook')
]
PLATFORMS = [
    (api_args.ANDROID, 'Android'),
    (api_args.IOS, 'iOS')
]


class User(db.Model):

    """User model.

    Notes:
        email can be empty because Facebook user might be authenticated with
        the phone number. "This field will not be returned if no valid email
        address is available."
        See: https://developers.facebook.com/docs/graph-api/reference/v2.2/user
    """
    __tablename__ = 'auth_user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.Unicode(128))
    first_name = db.Column(db.Unicode(50), nullable=False)
    last_name = db.Column(db.Unicode(50), nullable=False)
    gender = db.Column(db.String(50))
    email = db.Column(db.Unicode(75))
    is_staff = db.Column(db.Boolean, nullable=False, default=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    is_superuser = db.Column(db.Boolean, nullable=False, default=False)
    last_login = db.Column(
        db.DateTime, nullable=False, default=datetime.datetime.now,
        onupdate=datetime.datetime.now)
    date_joined = db.Column(
        db.DateTime, nullable=False, default=datetime.datetime.now)
    # Timezone offset in minutes.
    #   Example: -420 timezone_offset is -7 timezone (US/Pacific)
    timezone_offset = db.Column(db.Integer)
    settings = db.relationship('UserSettings', uselist=False, backref='user')

    @classmethod
    def create(cls, **kwargs):
        """Creates user and related objects."""
        offset = api_utils.zone2offset(kwargs.get('timezone', 0))
        user = cls(
            username=kwargs['username'],
            first_name=unicode(kwargs.get('first_name', '')),
            last_name=unicode(kwargs.get('last_name', '')),
            email=unicode(kwargs.get('email', '')),
            gender=kwargs.get('gender'),
            timezone_offset=offset)
        db.session.add(user)
        db.session.commit()
        # Create user settings and set default values
        UserSettings.get_or_create(user.id)
        return user

    @classmethod
    def get_by_username(cls, username):
        """Returns user by username or None."""
        return cls.get_by(username=username)

    @classmethod
    def get_by_email(cls, email):
        """Returns user by email or None."""
        return cls.get_by(email=email)

    @classmethod
    def get_by(cls, **filter_params):
        """Get user by filter parameters or None."""
        filter_params.update(dict(is_active=True))
        return cls.query.filter_by(**filter_params).first()

    @property
    def name(self):
        return u'{} {}'.format(self.first_name, self.last_name)

    def to_dict(self, timezone_offset=None):
        date_joined = utils_date.timezone_date(
            self.date_joined, timezone_offset)
        return dict(
            username=self.username, name=self.name, first_name=self.first_name,
            last_name=self.last_name, gender=self.gender, email=self.email,
            date_joined=date_joined)


class UserSettings(db.Model):

    """User settings model."""
    DEFAULT_SETTINGS = {
        api_args.EMAIL_SUBSCRIPTION: True
    }

    __tablename__ = 'user_settings'
    id = db.Column(db.Integer, primary_key=True)
    # One to one relationship with User
    user_id = db.Column(
        db.Integer, db.ForeignKey('auth_user.id'), nullable=False)
    settings = db.Column(db.Text, default='{}')  # Settings in json format

    @classmethod
    def get_or_create(cls, user_id, commit=True):
        """Returns user settings object or creates a new one."""
        obj = cls.query.filter_by(user_id=user_id).first()
        if obj:
            return obj
        User.query.filter_by(id=user_id).one()  # Check if user exists
        obj = cls(user_id=user_id,
                  settings=flask.json.dumps(cls.DEFAULT_SETTINGS))
        # By default, the new object persists data
        if commit:
            db.session.add(obj)
            db.session.commit()
        return obj

    def update(self, params, commit=True):
        """Updates user settings."""
        # This should be the only way to set settings
        if params is None:  # Resets settings to default values
            self.settings = flask.json.dumps(self.DEFAULT_SETTINGS)
        elif params == {}:  # Special case for empty settings
            self.settings = '{}'
        else:
            settings = self.to_dict()
            for k, v in params.items():
                settings[k] = v
            self.settings = flask.json.dumps(settings)
        cache_key = api_utils.create_key('user_id', self.user_id, 'settings')
        memcache.set(cache_key, self.settings)
        if commit:
            db.session.add(self)
            db.session.commit()

    @classmethod
    def user_param(cls, user_id, key):
        """User settings parameter."""
        cache_key = api_utils.create_key('user_id', user_id, 'settings')
        text = memcache.get(cache_key)
        if text:
            settings = api_utils.json_to_dict(text)
            return settings.get(key)
        obj = cls.get_or_create(user_id)
        memcache.set(cache_key, obj.settings)
        return obj.param(key)

    def param(self, key):
        """Returns settings param specified by key."""
        settings = self.to_dict()
        return settings.get(key)

    def to_dict(self):
        """Returns settings dictionary."""
        return api_utils.json_to_dict(self.settings)


class Token(db.Model):

    """Bearer token for Facebook or Eucaby."""
    __tablename__ = 'token'
    id = db.Column(db.Integer, primary_key=True)
    service = db.Column(choice.ChoiceType(SERVICE_TYPES), nullable=False)
    user_id = db.Column(
        db.Integer, db.ForeignKey('auth_user.id'), nullable=False)
    user = db.relationship('User')
    access_token = db.Column(db.String(255), unique=True, nullable=False)
    refresh_token = db.Column(db.String(255), unique=True)
    created_date = db.Column(
        db.DateTime, nullable=False, default=datetime.datetime.now)
    updated_date = db.Column(
        db.DateTime, nullable=False, default=datetime.datetime.now,
        onupdate=datetime.datetime.now)
    expires = db.Column(db.DateTime, nullable=False)
    scope = db.Column(db.Text)

    @classmethod
    def create_facebook_token(cls, user_id, access_token, expires_seconds):
        """Creates Facebook token."""
        # Note: It doesn't create user
        token = cls(
            service=FACEBOOK, user_id=user_id, access_token=access_token,
            expires=datetime.datetime.now() + datetime.timedelta(
                seconds=expires_seconds))
        db.session.add(token)
        db.session.commit()
        return token

    @classmethod
    def create_eucaby_token(cls, user_id, token):
        """Creates Eucaby token."""
        # Note: It doesn't create user
        token = cls(
            service=EUCABY, user_id=user_id,
            access_token=token['access_token'],
            refresh_token=token['refresh_token'],
            expires=datetime.datetime.now() + datetime.timedelta(
                seconds=token['expires_in']),
            scope=token['scope'])
        db.session.add(token)
        db.session.commit()
        return token

    def update_token(self, token):
        """Refreshes existing token. Doesn't update the refresh_token."""
        # Only Eucaby can be refreshed. Facebook has no way to do that
        self.access_token = token['access_token']
        self.expires = (datetime.datetime.now() +
                        datetime.timedelta(seconds=token['expires_in']))
        db.session.add(self)
        db.session.commit()

    @classmethod
    def get_by(cls, service, **filter_params):
        """Get latest token by filter parameters."""
        assert service in (FACEBOOK, EUCABY)
        filter_params.update(dict(service=service))
        return cls.query.filter_by(**filter_params).order_by('-id').first()

    @property
    def scopes(self):
        if self.scope:
            return self.scope.split()
        return []


user_device = db.Table(
    'user_device',
    db.Column('user_id', db.Integer, db.ForeignKey('auth_user.id')),
    db.Column('device_id', db.Integer, db.ForeignKey('device.id'))
)

class Device(db.Model):

    """Device model."""
    __tablename__ = 'device'
    __table_args__ = (db.UniqueConstraint(
        'device_key', 'platform', name='_device_key__platform'),)
    id = db.Column(db.Integer, primary_key=True)
    device_key = db.Column(db.String(255), nullable=False)
    platform = db.Column(choice.ChoiceType(PLATFORMS), nullable=False)
    users = db.relationship('User', secondary=user_device,
                            backref=db.backref('devices', lazy='dynamic'))
    active = db.Column(db.Boolean, nullable=False, default=True)
    created_date = db.Column(
        db.DateTime, nullable=False, default=datetime.datetime.now)
    updated_date = db.Column(
        db.DateTime, nullable=False, default=datetime.datetime.now,
        onupdate=datetime.datetime.now)

    @classmethod
    def get_or_create(cls, user, device_key, platform):
        """Registers device for user and creates a new one if needed."""
        obj = cls.query.filter_by(
            device_key=device_key, platform=platform).first()
        if obj:
            if user not in obj.users:
                obj.users.append(user)
                db.session.commit()
            return obj
        obj = cls(device_key=device_key, platform=platform)
        obj.users.append(user)
        db.session.add(obj)
        db.session.commit()
        return obj

    @classmethod
    def get_by_username(cls, username, platform=None):
        """List of active device objects by user."""
        kwargs = dict(active=True)
        if platform in api_args.PLATFORM_CHOICES:
            kwargs['platform'] = platform
        return cls.query.filter(
            cls.users.any(username=username)).filter_by(**kwargs).all()

    def deactivate(self, commit=True):
        """Deactivates the device."""
        self.active = False
        db.session.add(self)
        if commit:
            db.session.commit()

    @classmethod
    def deactivate_multiple(cls, device_keys, platform=None):
        """Deactivates multiple active devices.

        Note: The method should only be performed by admin
        """
        if not device_keys:
            return

        if platform not in api_args.PLATFORM_CHOICES:
            platform = None
        objs = cls.query.filter(
            cls.device_key.in_(device_keys), cls.active == True)
        if platform:
            objs = objs.filter(cls.platform == platform)
        objs.update(dict(active=False), synchronize_session=False)
        db.session.commit()


class EmailHistory(db.Model):

    """Email history."""
    __tablename__ = 'email_history'
    __table_args__ = (db.UniqueConstraint(
        'text', 'user_id', name='_text__user_id'),)
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('auth_user.id'), nullable=False)
    user = db.relationship('User')
    text = db.Column(db.Unicode(255), nullable=False, index=True)
    created_date = db.Column(
        db.DateTime, nullable=False, default=datetime.datetime.now)

    @classmethod
    def get_or_create(cls, user_id, text):
        """Returns email history or creates a new one."""
        text = unicode(text.lower())
        obj = cls.query.filter_by(user_id=user_id, text=text).first()
        if obj:
            return obj
        obj = cls(user_id=user_id, text=text)
        db.session.add(obj)
        db.session.commit()
        return obj

    @classmethod
    def get_by_user(cls, user_id, query=None, limit=None):
        """Returns email history by username."""
        if query == '':  # Empty query
            return []
        objs = cls.query.filter_by(user_id=user_id)
        if query:
            query = query.lower().replace('%', '')
            objs = objs.filter(cls.text.startswith(query))
        objs = objs.order_by(cls.text)
        if limit:
            objs = objs[:limit]
        else:
            objs = objs.all()
        return objs
