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
import datetime
from collections import defaultdict


def get_tokens(token_file):
    token_arr = []
    with open(token_file) as f:
        tokens = f.read().strip().split('\n')
        for token in tokens:
            consumer_key,consumer_secret,access_token,access_token_secret = token.split(',')
            token_arr.append(dict(consumer_key=consumer_key,consumer_secret=consumer_secret,access_token=access_token,access_token_secret=access_token_secret))
    return token_arr


def get_url_clicks(tweet_ids_file, token_file):
    tokens = get_tokens(token_file)[0]

    tweet_ids_df = pd.read_csv(tweet_ids_file)
    tweet_ids = tweet_ids_df[tweet_ids_df.columns[0]].to_list()

    url_clicks, tweet_text, reply_id, tweet_likes = [], [], [], []

    for tweet_id in tweet_ids:
        url = 'https://api.twitter.com/2/tweets/{}?tweet.fields=public_metrics,non_public_metrics'.format(tweet_id)

        headeroauth = OAuth1(tokens['consumer_key'], tokens['consumer_secret'], tokens['access_token'], tokens['access_token_secret'], signature_type='auth_header')
        r = requests.get(url, auth=headeroauth)

        #print(r.json())
        data = r.json()
        tweet_text.append(data['data']['text'])
        reply_id.append(data['data']['id'])
        url_clicks.append(data['data']['non_public_metrics']['url_link_clicks'])
        tweet_likes.append(data['data']['public_metrics']['like_count'])


    df = pd.DataFrame({ 'tweet_text':tweet_text, 'url_clicks': url_clicks, 'response_id': reply_id, 'response_likes': tweet_likes})
    save_df_path = 'data/' + tweet_ids_file.split('tweet_ids/')[1].split('.csv')[0] + '_link_clicks_df.csv'
    df.to_csv(save_df_path)
    print(df)
    return save_df_path

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-tw", "--tweet_ids_file", help="Path to tweet ids file", type=str, required=True)
    parser.add_argument("-t", "--token_file", help="Path to token file", type=str, required=True)
    
    args = parser.parse_args()

    tweet_ids_file = args.tweet_ids_file
    token_file = args.token_file

    get_url_clicks(tweet_ids_file, token_file)
    
