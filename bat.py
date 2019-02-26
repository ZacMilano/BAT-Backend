import datetime
import json
import sys

import psycopg2
import tweepy

from BotometerLite.core import BotometerLiteDetector
from __init__ import CONFIG

# sys.path.append("/home/ubuntu/bat/src/BotometerLite")

twitter_creds = CONFIG['twitter']

consumer_key = twitter_creds['consumer_key']
consumer_secret = twitter_creds['consumer_secret']
access_token = twitter_creds['access_token']
access_secret = twitter_creds['access_token_secret']

authorization = tweepy.OAuthHandler(consumer_key, consumer_secret)
authorization.set_access_token(access_token, access_secret)

api = tweepy.API(authorization)

DB_CONFIG = CONFIG['database']
QUERIES = DB_CONFIG['queries']
CONNECT_ARGS = DB_CONFIG['connect_args']

add_user = QUERIES['add_user'] # 3 args
add_topic = QUERIES['add_topic'] # 1 args
add_topic_mention = QUERIES['add_topic_mention'] # 2 args
get_trends_with_bot_scores_query = QUERIES['get_trends_with_bot_scores'] # 1 args

def get_trends_with_bot_scores(location=1, trend_count=10,
    count_per_topic=500,
    fetch_new_tweets=True, save=False):
  if not fetch_new_tweets:
    with open('/home/ubuntu/bat/trend_dict.json', 'r') as fp:
      trend_dict = json.load(fp)
  else:
    trends = get_trends(location=location, count=trend_count)
    trend_dict = {trend: get_tweets_by_topic(trend, limit=count_per_topic)
        for trend in trends}

    trends_to_remove = []
    for trend, tweets in trend_dict.items():
      if tweets == []:
        trends_to_remove.append(trend)
    for trend in trends_to_remove:
      trend_dict.pop(trend, None)

    # print(trend_dict)
    trend_dict = {trend: (transform_tweets(tweets)) for trend, tweets in
        trend_dict.items()}
    if save:
      with open('/home/ubuntu/bat/trend_dict.json', 'w') as fp:
        json.dump(trend_dict, fp)
  with get_db_connection() as conn:
    with conn.cursor() as curs:
      for trend, tweets in trend_dict.items():
        try:
          add_topic_to_db(curs, trend)
        except psycopg2.IntegrityError:
          print('Ignoring duplicate trend {}'.format(trend))
        for tweet in tweets:
          tweet_id_str, user_id_str, bot_score = tweet
          try:
            add_user_to_db(curs, user_id_str, bot_score)
          except psycopg2.IntegrityError:
            print('Ignoring duplicate user {}'.format(user_id_str))
          try:
            add_topic_mention_to_db(curs, tweet_id_str, trend, user_id_str)
          except psycopg2.IntegrityError:
            print('Ignoring duplicate tweet {}'.format(tweet_id_str))

      curs.execute(get_trends_with_bot_scores_query.format(str(trend_count)))
      trends_list = curs.fetchall()
  trends_list = [(trend, float(str(score))) for trend, score in trends_list]
  write_out_trends_with_bot_scores(trends_list)
  return trends_list

def get_db_connection():
  return psycopg2.connect(
      host=CONNECT_ARGS['host'],
      port=CONNECT_ARGS['port'],
      dbname=CONNECT_ARGS['dbname'],
      user=CONNECT_ARGS['username'],
      password=CONNECT_ARGS['password']
      )

def write_out_trends_with_bot_scores(data,
    file_path="/home/ubuntu/bat-frontend/src/data.json"):
  '''Given list of (trend, average bot score), write out json file to be used
  in frontend'''
  data_dict_list = [{"topic": trend, "botscore": bot_score}
      for trend, bot_score in data]
  with open(file_path, 'w') as fp:
    json.dump(data_dict_list, fp)

def get_trends(location=1, count=10):
  '''Get last {count} trending topics near given location. Default is global'''
  trends = api.trends_place(location)
  trends_list = trends[0]['trends'][:count]
  trends_list = [trend['name'] for trend in trends_list]
  return trends_list

def get_tweets_by_topic(trending_topic, limit=1):
  '''Search for tweets mentioning given topic with Twitter's streaming API'''
  tweet_jsons = []
  today = datetime.datetime.today().strftime('%Y-%m-%d')
  yesterday = datetime.datetime.today() - datetime.timedelta(1)
  yesterday = yesterday.strftime('%Y-%m-%d')
  for tweet in tweepy.Cursor(api.search, q=(trending_topic), since=yesterday,
      until=today).items(limit):
    tweet_jsons.append(tweet._json)
    # tweet_jsons.append(json.dumps(tweet._json))
    # print(type(tweet._json))
  return tweet_jsons

def transform_tweets(tweet_objs):
  '''Use BotometerLite to get bot score for a user based on the tweet
  object. Input is list of tweet objects.'''
  scorer = BotometerLiteDetector()
  df_result = scorer.detect_on_tweet_objects(tweet_objs)
  transformed_tweets = []
  for index, twt in df_result.iterrows():
    bot_score = twt['blt_score']
    raw_tweet = tweet_objs[index]
    transformed_tweets.append((
      raw_tweet['id_str'],
      raw_tweet['user']['id_str'],
      bot_score
      ))
  return transformed_tweets

def add_user_to_db(curs, user_id_str, bot_score):
  '''Add user to database with curs as the cursor'''
  curs.execute(add_user.format(user_id_str, bot_score))

def add_topic_to_db(curs, topic_name):
  '''Add topic/trend to database with curs as the cursor'''
  curs.execute(add_topic.format(topic_name.replace("'", "''")))

def add_topic_mention_to_db(curs, tweet_id_str, topic, user_id_str):
  '''Add a mention of a topic in a tweet to database with curs as the cursor'''
  curs.execute(add_topic_mention.format(tweet_id_str,
    topic.replace("'", "''"), user_id_str))

# BotometerLite.BotometerLiteDetector()
if __name__ == "__main__":
  print(get_trends_with_bot_scores(fetch_new_tweets=True, save=True))
