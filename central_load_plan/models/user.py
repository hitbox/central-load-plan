import uuid

import sqlalchemy as sa

from flask_login import UserMixin
from passlib.hash import argon2

from .clp_base import CLPBase

class User(CLPBase, UserMixin):
    """
    A user of the web app system controlling login.
    """

    __tablename__ = 'user'

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)

    username = sa.Column(sa.String, unique=True, nullable=False)
    _password_hash = sa.Column(sa.String, nullable=False)

    is_active = sa.Column(
        sa.Boolean,
        nullable=False,
        default=True,
        comment = 'User can login.',
    )
    is_admin = sa.Column(
        sa.Boolean,
        nullable=False,
        default=False,
        comment = 'User can access admin pages.',
    )

    @property
    def password(self):
        raise AttributeError('Password hash is write-only.')

    @password.setter
    def password(self, plaintext):
        self._password_hash = argon2.hash(plaintext)

    def verify_password(self, plaintext):
        return self.is_active and argon2.verify(plaintext, self._password_hash)
