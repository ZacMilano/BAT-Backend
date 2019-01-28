from bat import CONFIG
from bat.db import ENGINE

QUERIES = CONFIG['queries']

def add_user(user_name, user_bot_score):
  return ENGINE.execute(QUERIES['add_user'].format(user_name, user_bot_score))
