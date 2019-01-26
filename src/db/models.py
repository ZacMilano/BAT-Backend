from datetime import datetime
from sqlalchemy import Column, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.types import BigInteger, Enum, NUMERIC, String, TIMESTAMP, VARCHAR
import re

Base = declarative_base()

class BaseTable:
  @declared_attr
  def __tablename__(cls):
    return re.sub('(?!^)([A-Z]+)', r'_\1', cls.__name__).lower()

class Topic(BaseTable, Base):
  topic_id = Column(BigInteger, primary_key=True)
  topic_name = Column(Text, nullable=False)
  topicTypes = ["hashtag", "url", "user_mention", "symbol"]
  topic_type = Column(Enum(*topicTypes, name="topicType"), default="hashtag")

class TwitterUser(BaseTable, Base):
  user_id = Column(BigInteger, primary_key=True)
  user_name = Column(VARCHAR(length=15))
  user_bot_score = Column(NUMERIC(precision=5, scale=3), nullable=False)

class TopicMention(BaseTable, Base):
  topic_id = Column(BigInteger, primarykey=True, ForeignKey("topic.topic_id"))
  user_id = Column(BigInteger, primarykey=True, ForeignKey("user.user_id"))
  time_of_mention = Column(TIMESTAMP, primarykey=True)
