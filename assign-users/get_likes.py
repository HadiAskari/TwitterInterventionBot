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

def get_favorites(consumer_key, consumer_secret, access_token, access_token_secret, user, num_tweets ):
    auth = tw.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tw.API(auth, wait_on_rate_limit=True)
    tweetsReq = tw.Cursor(api.get_favorites,
            user_id=user, count=num_tweets,
            tweet_mode='extended').items(num_tweets)
    tweets = []
    try:
        for tweet in tweetsReq:
            tweets.append(dict(
                full_text = tweet.full_text,
                tweet_id=tweet.id_str,
                created_at=tweet.created_at,
                screen_name=tweet.user.screen_name,
                liked_user_id=tweet.user.id_str,
                original_user_id=user,
                collected_at=datetime.datetime.today(),
                ))
    except Exception as e:
        print(e)

    return tweets




def get_likes(token_dict, users_list, num_tweets, q):
    for user in tqdm(users_list):
        tweets = get_favorites(
            token_dict['consumer_key'],
            token_dict['consumer_secret'],
            token_dict['access_token'],
            token_dict['access_token_secret'],
            user, num_tweets=num_tweets
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


def get_likes_main(user_file, token_file, num_tweets):
    user_df = pd.read_csv(user_file)
    users_list = user_df['UserIDs'].apply(lambda x: str(x)).to_list()
    tokens = get_tokens(token_file)

    res_q = Queue()

    NUM_THREADS = len(tokens) #equivalent to num tokens
    KEYWORDS_PER_THREAD = ceil(len(users_list) / len(tokens))

    threads = []
    for i in range(NUM_THREADS):
        token_dict = tokens[i]
        start = int(i * KEYWORDS_PER_THREAD)
        thread_users = users_list[start: start + KEYWORDS_PER_THREAD]
        thread = Thread(target=get_likes, args=(token_dict, thread_users, num_tweets, res_q ))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

    save_df_path = 'data/' + user_file.split('users/')[1].split('.csv')[0] + '_likes_df.csv'

    while not res_q.empty():
        res = res_q.get()
        res_df = pd.DataFrame(res)
        if os.path.isfile(save_df_path):
            loaded_df = pd.read_csv(save_df_path)
            res_df = pd.concat([loaded_df, res_df], ignore_index=True, sort=False)
        res_df.to_csv(save_df_path, index=False)

    print(res_df)
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

    get_likes_main(user_file, token_file, num_tweets)
