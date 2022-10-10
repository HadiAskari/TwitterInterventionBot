import pandas as pd
import botometer
from queue import Queue
from math import ceil
import tweepy as tw
from threading import Thread
from tqdm.auto import tqdm
import os
import json
from shutil import get_terminal_size 
import argparse
from tqdm.auto import tqdm

def frequency_follower_filter(df):
    df2 = df.drop_duplicates(subset=["tweet_id"], keep="first")
    df_count = df2.groupby(['user_id'])['user_id'].count().reset_index(name="count")
    df_count_trim = df_count[(df_count['count'] > 1) & (df_count['count'] < 21)]
    #df3 = df2.drop_duplicates(subset=["user_id"], keep="last").loc[:, ["user_id", "followers_count"]]
    df3 = df2.drop_duplicates(subset=["user_id"], keep="last").loc[:,]
    df_count_trim_follower = pd.merge(df_count_trim, df3, on="user_id", how="left")
    df_count_trim_follower = df_count_trim_follower[(df_count_trim_follower['followers_count'] > 78) & (df_count_trim_follower['followers_count'] < 16538 )]
    df_count_trim_follower = df_count_trim_follower[(df_count_trim_follower['friends_count'] > 126) & (df_count_trim_follower['friends_count'] < 4589 )]
    return df_count_trim_follower


def get_tokens(token_file):
    token_arr = []
    with open(token_file) as f:
        tokens = f.read().strip().split('\n')
        for token in tokens:
            consumer_key,consumer_secret,access_token,access_token_secret = token.split(',')
            token_arr.append(dict(consumer_key=consumer_key,consumer_secret=consumer_secret,access_token=access_token,access_token_secret=access_token_secret))
    return token_arr

def get_botometer_tokens(token_file):
    with open(token_file) as f:
        tokens = f.read().strip().split('\n')

    return tokens

# bot check
def bot_check(token_dict, rapidapi_key, twitter_userid, q):
    #twitter_userid = list(df.loc[:, "user_id"])
    twitter_app_auth = {
        'consumer_key': token_dict['consumer_key'],
        'consumer_secret': token_dict['consumer_secret'],
        'access_token': token_dict['access_token'],
        'access_token_secret': token_dict['access_token_secret'],
    }
    bom = botometer.Botometer(wait_on_ratelimit=True,
                            rapidapi_key=rapidapi_key,
                            **twitter_app_auth)

    bot_analy = {}
    for i in range(0, len(twitter_userid)):
        try:
            response = bom.check_account(twitter_userid[i])
            bot_analy[i] = response
        except Exception:
            continue

    bot_analy_extr = {}
    for i in tqdm(bot_analy.keys()):
        bot_analy_extr[i] = {}

        bot_analy_extr[i]['cap_english'] = bot_analy[i]['cap']['english']
        bot_analy_extr[i]['cap_universal'] = bot_analy[i]['cap']['universal']

        bot_analy_extr[i]['user_id_str'] = bot_analy[i]['user']['user_data']['id_str']
        bot_analy_extr[i]['user_screen_name'] = bot_analy[i]['user']['user_data']['screen_name']
        bot_analy_extr[i]['user_language'] = bot_analy[i]['user']['majority_lang']

        bot_analy_extr[i]['display_eng_astroturf'] = bot_analy[i]['display_scores']['english']['astroturf']
        bot_analy_extr[i]['display_eng_fake_follower'] = bot_analy[i]['display_scores']['english']['fake_follower']
        bot_analy_extr[i]['display_eng_financial'] = bot_analy[i]['display_scores']['english']['financial']
        bot_analy_extr[i]['display_eng_other'] = bot_analy[i]['display_scores']['english']['other']
        bot_analy_extr[i]['display_eng_overall'] = bot_analy[i]['display_scores']['english']['overall']
        bot_analy_extr[i]['display_eng_self_declared'] = bot_analy[i]['display_scores']['english']['self_declared']
        bot_analy_extr[i]['display_eng_spammer'] = bot_analy[i]['display_scores']['english']['spammer']

        bot_analy_extr[i]['display_uni_astroturf'] = bot_analy[i]['display_scores']['universal']['astroturf']
        bot_analy_extr[i]['display_uni_fake_follower'] = bot_analy[i]['display_scores']['universal']['fake_follower']
        bot_analy_extr[i]['display_uni_financial'] = bot_analy[i]['display_scores']['universal']['financial']
        bot_analy_extr[i]['display_uni_other'] = bot_analy[i]['display_scores']['universal']['other']
        bot_analy_extr[i]['display_uni_overall'] = bot_analy[i]['display_scores']['universal']['overall']
        bot_analy_extr[i]['display_uni_self_declared'] = bot_analy[i]['display_scores']['universal']['self_declared']
        bot_analy_extr[i]['display_uni_spammer'] = bot_analy[i]['display_scores']['universal']['spammer']

        bot_analy_extr[i]['raw_eng_astroturf'] = bot_analy[i]['raw_scores']['english']['astroturf']
        bot_analy_extr[i]['raw_eng_fake_follower'] = bot_analy[i]['raw_scores']['english']['fake_follower']
        bot_analy_extr[i]['raw_eng_financial'] = bot_analy[i]['raw_scores']['english']['financial']
        bot_analy_extr[i]['raw_eng_other'] = bot_analy[i]['raw_scores']['english']['other']
        bot_analy_extr[i]['raw_eng_overall'] = bot_analy[i]['raw_scores']['english']['overall']
        bot_analy_extr[i]['raw_eng_self_declared'] = bot_analy[i]['raw_scores']['english']['self_declared']
        bot_analy_extr[i]['raw_eng_spammer'] = bot_analy[i]['raw_scores']['english']['spammer']

        bot_analy_extr[i]['raw_uni_astroturf'] = bot_analy[i]['raw_scores']['universal']['astroturf']
        bot_analy_extr[i]['raw_uni_fake_follower'] = bot_analy[i]['raw_scores']['universal']['fake_follower']
        bot_analy_extr[i]['raw_uni_financial'] = bot_analy[i]['raw_scores']['universal']['financial']
        bot_analy_extr[i]['raw_uni_other'] = bot_analy[i]['raw_scores']['universal']['other']
        bot_analy_extr[i]['raw_uni_overall'] = bot_analy[i]['raw_scores']['universal']['overall']
        bot_analy_extr[i]['raw_uni_self_declared'] = bot_analy[i]['raw_scores']['universal']['self_declared']
        bot_analy_extr[i]['raw_uni_spammer'] = bot_analy[i]['raw_scores']['universal']['spammer']

    df_bot_score = pd.DataFrame.from_dict(bot_analy_extr, orient='index')
    df_bot_final = df_bot_score[df_bot_score['cap_english'] < .6]
    
    q.put(df_bot_final)


def botometer_filter_main(user_file, token_file, botometer_token_file):
    user_df = pd.read_csv(user_file)
    tokens = get_tokens(token_file)
    botometer_tokens = get_botometer_tokens(botometer_token_file)

    user_df = frequency_follower_filter(user_df)
    print(user_df)

    users_list = user_df['user_id'].apply(lambda x: str(x)).to_list()

    # run botometer function with threading
    res_q = Queue()

    NUM_THREADS = len(tokens) #equivalent to num tokens
    KEYWORDS_PER_THREAD = ceil(len(users_list) / len(tokens))

    threads = []
    for i in range(NUM_THREADS):
        token_dict = tokens[i]
        botometer_token = botometer_tokens[i]
        start = int(i * KEYWORDS_PER_THREAD)
        thread_users = users_list[start: start + KEYWORDS_PER_THREAD]
        thread = Thread(target=bot_check, args=(token_dict, botometer_token, thread_users, res_q ))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

    save_df_path = './data/users_FILTERED.csv'

    while not res_q.empty():
        res = res_q.get()
        res_df = res
        if os.path.isfile(save_df_path):
            loaded_df = pd.read_csv(save_df_path)
            res_df = pd.concat([loaded_df, res_df], ignore_index=True, sort=False)
        res_df.to_csv(save_df_path, index=False)

    print(res_df)
    return save_df_path



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--user_file", help="Path to user file", type=str, required=True)
    parser.add_argument("-t", "--token_file", help="Path to token file", type=str, required=True)
    parser.add_argument("-b", "--botometer_token_file", help="Path to botometer token file", type=str, required=True)

    args = parser.parse_args()
    user_file = args.user_file
    token_file = args.token_file
    botometer_token_file = args.botometer_token_file

    botometer_filter_main(user_file, token_file, botometer_token_file)
