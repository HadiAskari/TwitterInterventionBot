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

def get_user_timeline(consumer_key, consumer_secret, access_token, access_token_secret, user, num_tweets, since_id_dict ):
    auth = tw.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tw.API(auth, wait_on_rate_limit=True)
    tweetsReq = tw.Cursor(api.user_timeline,
            user_id=user, count=num_tweets,
            exclude_replies=False, include_rts=True,
            tweet_mode='extended', since_id=since_id_dict[user]).items(num_tweets)
    tweets = []
    try:
        for tweet in tweetsReq:
            try:
                full_text=tweet.retweeted_status.full_text
                retweeted_user = tweet.retweeted_status.id_str
            except AttributeError:  # Not a Retweet
                full_text=tweet.full_text
                retweeted_user = ''  # if not a re-tweet, there is no id to assign here
            tweets.append(dict(
                full_text = full_text,
                tweet_id=tweet.id_str,
                created_at=tweet.created_at,
                screen_name=tweet.user.screen_name,
                original_user_id=user,
                retweeted_user_ID=retweeted_user,
                collected_at=datetime.datetime.today()
                ))
    except Exception as e:
        print(e)


    return tweets



def get_tweets(token_dict, users_list, num_tweets, since_id_dict, q):
    for user in tqdm(users_list):
        tweets = get_user_timeline(
            token_dict['consumer_key'],
            token_dict['consumer_secret'],
            token_dict['access_token'],
            token_dict['access_token_secret'],
            user, num_tweets=num_tweets, since_id_dict=since_id_dict
        )
        if len(tweets)==0:
            continue
        else:
            q.put(tweets)


def get_tokens(token_file):
    token_arr = []
    with open(token_file) as f:
        tokens = f.read().strip().split('\n')
        for token in tokens:
            consumer_key,consumer_secret,access_token,access_token_secret = token.split(',')
            token_arr.append(dict(consumer_key=consumer_key,consumer_secret=consumer_secret,access_token=access_token,access_token_secret=access_token_secret))
    return token_arr


def get_since_id_dict(user_file):
    save_df_path = 'data/' + user_file.split('users/')[1].split('.csv')[0] + '_tweets_df.csv'
    user_df = pd.read_csv(user_file)
    users_list = user_df['UserIDs'].apply(lambda x: str(x)).to_list()

    since_id_dict = defaultdict(lambda: None)

    if os.path.isfile(save_df_path):
        prev_df = pd.read_csv(save_df_path)
        for user_id in users_list:
            all_ids = prev_df[prev_df['original_user_id'] == int(user_id)]['tweet_id'].to_list()
            if len(all_ids) == 0:
                continue
            since_id_dict[user_id] = max(all_ids)

    return since_id_dict


def get_tweets_main(user_file, token_file, num_tweets):
    user_df = pd.read_csv(user_file)
    users_list = user_df['UserIDs'].apply(lambda x: str(x)).to_list()
    tokens = get_tokens(token_file)

    since_id_dict = get_since_id_dict(user_file)

    res_q = Queue()

    NUM_THREADS = len(tokens) #equivalent to num tokens
    KEYWORDS_PER_THREAD = ceil(len(users_list) / len(tokens))

    threads = []
    for i in range(NUM_THREADS):
        token_dict = tokens[i]
        start = int(i * KEYWORDS_PER_THREAD)
        thread_users = users_list[start: start + KEYWORDS_PER_THREAD]
        thread = Thread(target=get_tweets, args=(token_dict, thread_users, num_tweets,since_id_dict, res_q ))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

    save_df_path = 'data/' + user_file.split('users/')[1].split('.csv')[0] + '_tweets_df.csv'

    while not res_q.empty():
        res = res_q.get()
        res_df = pd.DataFrame(res)
        if os.path.isfile(save_df_path):
            loaded_df = pd.read_csv(save_df_path)
            res_df = pd.concat([loaded_df, res_df], ignore_index=True, sort=False)
        res_df.to_csv(save_df_path, index=False)


    try:
        print(res_df)
    except Exception:
        print("Nothing new to add..")

    return save_df_path



if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--user_file", help="Path to user file", type=str, required=True)
    parser.add_argument("-t", "--token_file", help="Path to token file", type=str, required=True)
    parser.add_argument("-n", "--num_tweets", help="Number of tweets to search-- should be less than 200", type=int, required=True)

    args = parser.parse_args()
    user_file = args.user_file
    token_file = args.token_file
    num_tweets = int(args.num_tweets)

    get_tweets_main(user_file, token_file, num_tweets)
