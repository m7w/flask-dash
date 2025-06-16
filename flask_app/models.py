from flask_security.models import sqla as sqla
from sqlalchemy import select

from .database import Base, db_session


class Role(Base, sqla.FsRoleMixin):
    __tablename__ = "role"


class User(Base, sqla.FsUserMixin):
    __tablename__ = "user"

    def get_permissions(self):
        roles = db_session.execute(
            select(Role).join(User.roles).filter(User.id == self.id)
        ).scalars()
        permissions = set()
        for role in roles:
            permissions.update(role.get_permissions())
        return list(permissions)
