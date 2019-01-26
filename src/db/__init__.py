from bat import CONFIG
from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker

try:
  ENGINE = create_engine(URL(**CONFIG["database"]["connect_args"]))
  SESSION = scoped_session(sessionmaker(bind=ENGINE))
