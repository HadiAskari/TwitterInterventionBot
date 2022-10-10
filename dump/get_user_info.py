from math import ceil
import tweepy as tw
import pandas as pd
from threading import Thread
from tqdm.auto import tqdm
from queue import Queue
import argparse
import os

def get_info(token_dict, userid, q):
    consumer_key = token_dict['consumer_key']
    consumer_secret = token_dict['consumer_secret']
    access_token = token_dict['access_token']
    access_token_secret = token_dict['access_token_secret']

    auth = tw.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tw.API(auth, wait_on_rate_limit=True)

    user_infos = []  # this holds information for all users in this thread

    for user in tqdm(userid):  # loop through users in thread

        try:
            user_object = api.get_user(user_id=user)  # get user info and append dict to user_infos
            user_infos.append(dict(
                user_id=user,
                created_at=user_object.created_at,
                lang=user_object.lang,
                location=user_object.location,
                time_zone=user_object.time_zone,
                verified=user_object.verified,
                listed_count=user_object.listed_count,
                favourites_count=user_object.favourites_count,
                statuses_count=user_object.statuses_count,
                friends_count=user_object.friends_count,
                followers_count=user_object.followers_count))

        except Exception as e:
            print(e)
            print("Problematic keys -> ")
            print(consumer_key, consumer_secret, access_token, access_token_secret)

    q.put(user_infos)


def get_tokens(token_file):
    token_arr = []
    with open(token_file) as f:
        tokens = f.read().strip().split('\n')
        for token in tokens:
            consumer_key, consumer_secret, access_token, access_token_secret = token.split('|')  ## token.split(',')
            token_arr.append(dict(consumer_key=consumer_key, consumer_secret=consumer_secret, access_token=access_token,
                                  access_token_secret=access_token_secret))
    return token_arr


def run_collection(user_file, token_file):
    global df
    tokens = get_tokens(token_file)

    user_df = pd.read_csv(user_file)  # MAKE SURE THAT THIS FILE HAS USER IDS IN THE RIGHT FORMAT
    userid = user_df['user_id'].apply(lambda x: str(x)).to_list()  # REPLACE COLUMN NAME WITH CORRECT NAME

    NUM_THREADS = len(tokens)  # equivalent to num tokens
    userid_per_thread = ceil(len(userid) / len(tokens))

    res_q = Queue()

    threads = []
    for i in range(NUM_THREADS):
        token_dict = tokens[i]
        start = int(i * userid_per_thread)
        thread_userid = userid[start:start + userid_per_thread]
        thread = Thread(target=get_info, args=(token_dict, thread_userid, res_q))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

    while not res_q.empty():
        res = res_q.get()
        df = pd.DataFrame(res)
        if os.path.isfile('user_info.csv'): # REPLACE THIS WITH DESIRED PATH
            loaded_df = pd.read_csv('user_info.csv')
            df = pd.concat([loaded_df, df], ignore_index=True, sort=False)
        df.to_csv('user_info.csv', index=False)

    print(df)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--user_file", help="Path to user file", type=str, required=True)
    parser.add_argument("-t", "--token_file", help="Path to token file", type=str, required=True)

    args = parser.parse_args()
    user_file = args.user_file
    token_file = args.token_file

    run_collection(user_file, token_file)
