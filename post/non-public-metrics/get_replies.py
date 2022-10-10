from requests_oauthlib import OAuth1
import requests
from time import sleep
from math import ceil
import tweepy as tw
import pandas as pd
from threading import Thread
from tqdm.auto import tqdm
import os
import json
from queue import Queue
import argparse
from datetime import datetime
from collections import defaultdict


def get_tokens(token_file):
    token_arr = []
    with open(token_file) as f:
        tokens = f.read().strip().split('\n')
        for token in tokens:
            consumer_key,consumer_secret,access_token,access_token_secret = token.split(',')
            token_arr.append(dict(consumer_key=consumer_key,consumer_secret=consumer_secret,access_token=access_token,access_token_secret=access_token_secret))
    return token_arr


def get_replies_helper(consumer_key, consumer_secret, access_token, access_token_secret, tweetid, num_tweets, date, botusername):
    auth = tw.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tw.API(auth, wait_on_rate_limit=True)

    name = botusername
    tweet_id=tweetid

    tweetsReq = tw.Cursor(api.search_tweets,
                q='to: '+name + " -filter:retweets",
                lang="en", until=date,
                result_type='recent', tweet_mode='extended').items(num_tweets)

    tweets = []
    try:
        for tweet in tweetsReq:
            if hasattr(tweet, 'in_reply_to_status_id_str') == False:
                continue
            if (tweet.in_reply_to_status_id_str==tweet_id):
                tweets.append(dict(
                        full_text = tweet.full_text,
                        BotTweetID=tweet_id,
                        tweet_id=tweet.id_str,
                        screen_name=tweet.user.screen_name,
                        user_id=tweet.user.id_str
                        ))
    except Exception as e:
        print(e)

    return tweets


def get_replies(tweet_ids_file, token_file, bot_username):
    tokens = get_tokens(token_file)[0]

    tweet_ids_df = pd.read_csv(tweet_ids_file)
    tweet_ids = tweet_ids_df[tweet_ids_df.columns[0]].to_list()

    appended_data = []
    for tweet in tweet_ids:
            tweets = get_replies_helper(
                tokens['consumer_key'],
                tokens['consumer_secret'],
                tokens['access_token'],
                tokens['access_token_secret'],
                tweetid=tweet, num_tweets=20000, date=datetime.now().strftime("%Y-%m-%d"), botusername=bot_username
            )
            if len(tweets)==0:
                continue
            else:
                appended_data.append(pd.DataFrame(tweets))
                
    try:
        appended_data = pd.concat(appended_data)
    except:
        appended_data = pd.DataFrame()

    save_df_path = 'data/' + tweet_ids_file.split('tweet_ids/')[1].split('.csv')[0] + '_replies_df.csv'
    appended_data.to_csv(save_df_path)
    print(appended_data)
    return save_df_path

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-tw", "--tweet_ids_file", help="Path to tweet ids file", type=str, required=True)
    parser.add_argument("-bu", "--bot_username", help="Bot user name without the @", type=str, required=True)
    parser.add_argument("-t", "--token_file", help="Path to token file", type=str, required=True)
    
    args = parser.parse_args()

    tweet_ids_file = args.tweet_ids_file
    token_file = args.token_file
    bot_username = args.bot_username

    get_replies(tweet_ids_file, token_file, bot_username)
    
