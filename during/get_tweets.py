from math import ceil
import tweepy as tw
import pandas as pd
from threading import Thread
from tqdm.auto import tqdm
import os
import json
import sqlite3
from collections import defaultdict
import json
from queue import Queue
from datetime import datetime

os.environ['MKL_THREADING_LAYER'] = 'GNU'

def get_tweet_responses(consumer_key, consumer_secret, access_token, access_token_secret, user, num_tweets, since):

    auth = tw.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tw.API(auth, wait_on_rate_limit=True)
    
    tweets = []
    try:
        tweetsReq = tw.Cursor(api.user_timeline,
            user_id=user, count=10,
            exclude_replies=True, include_rts=False,
            since_id = since, ##
            tweet_mode='extended').items(num_tweets)
    
    
        for tweet in tweetsReq:
            tweets.append(dict(
                full_text = tweet.full_text,
                tweet_id=tweet.id_str,
                screen_name=tweet.user.screen_name,
                user_id=tweet.user.id_str,
                created=tweet.created_at,
            ))
    except Exception as e:
        print(e)
        print("Problematic get_tweets keys -> ")
        print(consumer_key, consumer_secret, access_token, access_token_secret)

    return tweets

def get_sinceID(user, db_file):
    conn=sqlite3.connect(db_file) ##
    c=conn.cursor()
    c.execute("SELECT sinceid FROM users WHERE userid=(?)",[user])
    result=c.fetchall()
    conn.commit()
    conn.close()

    return result

def set_sinceID(user, sinceid, db_file):
    conn=sqlite3.connect(db_file) ##
    c=conn.cursor()
    c.execute("UPDATE users SET sinceid = (?) WHERE userid = (?)", (sinceid, user))
    conn.commit()
    conn.close()


def get_tweets(token_dict, userid, GLOBALCOUNT, db_file, q):
    for user in tqdm(userid):

        if GLOBALCOUNT == 1: ##
            since_var = None
        else:
            since_var = get_sinceID(user, db_file)
            since_var = str(int(since_var[0][0]))

        tweets = get_tweet_responses(
            token_dict['consumer_key'],
            token_dict['consumer_secret'],
            token_dict['access_token'],
            token_dict['access_token_secret'],
            user, num_tweets=10, since=since_var
        )

        if len(tweets)==0: #get_tweet_responses can return None
            continue
        else:
            q.put(tweets)


def get_tokens(token_file):
    token_arr = []
    with open(token_file) as f:
        tokens = f.read().strip().split('\n')
        for token in tokens:
            consumer_key,consumer_secret,access_token,access_token_secret = token.split(',') ## token.split('|')
            token_arr.append(dict(consumer_key=consumer_key,consumer_secret=consumer_secret,access_token=access_token,access_token_secret=access_token_secret))

    return token_arr

def get_days_passed(twitter_date): #Only accepts twitter date format (UTC)
    dtime = twitter_date.to_pydatetime().strftime("%Y/%m/%d %H:%M:%S")
    now = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    dtime, now = pd.to_datetime(dtime), pd.to_datetime(now)
    return (now-dtime).days

def run_collection(GLOBALCOUNT, user_file, db_file, token_file):
    df_pkl_file = 'data/' + user_file.split('users/')[1].split('.csv')[0] + '_df.pkl'

    tokens = get_tokens(token_file) ##

    user_df = pd.read_csv(user_file) #
    userid = user_df['UserIDs'].apply(lambda x: str(x)).to_list()

    NUM_THREADS = len(tokens) #equivalent to num tokens
    userid_per_thread = ceil(len(userid) / len(tokens))

    res_q = Queue() #can't write to files in threads-> race condition!. We will use a Queue (thread-safe) to store results instead and write to file later

    threads = []
    for i in range(NUM_THREADS):
        token_dict = tokens[i]
        start = int(i * userid_per_thread)
        thread_userid = userid[start:start + userid_per_thread]
        thread = Thread(target=get_tweets, args=(token_dict, thread_userid, GLOBALCOUNT, db_file, res_q, ))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

    while not res_q.empty():
        res = res_q.get()
        df = pd.DataFrame(res)

        if GLOBALCOUNT == 1: #for first time collection, ensure that the tweets are no older than 7 days
            df = df[df['created'].apply(get_days_passed) <= 1]
            if len(df) == 0: #in case we removed all collected tweets!
                continue

        user = res[0]['user_id'] #all user ids should be same for one thread collection
        tweet_list_str = df['tweet_id'].to_list()
        int_list = list(map(int, tweet_list_str))
        global_count_list = [GLOBALCOUNT] * len(tweet_list_str)
        user_id_list = [user]* len(tweet_list_str)
        df['GLOBALCOUNT'] = global_count_list
        df['user'] = user_id_list
        set_sinceID(user, max(int_list), db_file) ## set since id for future use


        if os.path.isfile(df_pkl_file): ##
            loaded_df = pd.read_pickle(df_pkl_file) ##
            df = pd.concat([loaded_df, df], ignore_index=True, sort=False)

        df.to_pickle(df_pkl_file)
    
