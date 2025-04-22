import os

from dotenv import load_dotenv
from flask_security.models import sqla
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, scoped_session, sessionmaker

load_dotenv()

engine = create_engine(
    "postgresql+psycopg2://{DATABASE_USER}:{DATABASE_PASS}@localhost/{DATABASE}".format(
        **os.environ
    )
)
db_session = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
)


class Base(DeclarativeBase):
    pass


sqla.FsModels.set_db_info(base_model=Base)


def init_db():
    Base.metadata.create_all(bind=engine)
