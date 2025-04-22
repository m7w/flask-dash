from flask_security.models import sqla as sqla

from .database import Base


class Role(Base, sqla.FsRoleMixin):
    __tablename__ = 'role'

class User(Base, sqla.FsUserMixin):
    __tablename__ = 'user'
