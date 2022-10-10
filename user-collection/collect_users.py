from queue import Queue
import argparse
from math import ceil
import tweepy as tw
import pandas as pd
from threading import Thread
from tqdm.auto import tqdm
import os
import json
from datetime import datetime
import geostring as geo
import spacy
from spacy_langdetect import LanguageDetector
from spacy.language import Language
from time import sleep

def check_location(loc):
    loc = geo.resolve(loc)
    country = list(loc.items())[2][1]

    if '?' in country:
        country = country.split('?')[1]

    if country == 'united states':
        return True

    return False


@Language.factory('language_detector')
def language_detector(nlp, name):
    return LanguageDetector()

def check_lang(text):
    nlp = spacy.load('en_core_web_sm')
    nlp.add_pipe('language_detector', last=True)
    doc = nlp(text)
    detect_language = doc._.language
    if detect_language['language'] != 'en':
        return False
    else:
        return True



def search_tweets(consumer_key, consumer_secret, access_token, access_token_secret, search_words, num_tweets, date):
    auth = tw.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tw.API(auth, wait_on_rate_limit=True)
    #tweetsReq = tw.Cursor(api.search_tweets,
    tweetsReq = tw.Cursor(api.search,
            q=search_words + " -filter:retweets",
            lang="en", until=date,
            result_type='recent', tweet_mode='extended').items(num_tweets)

    tweets = []

    try:
        for tweet in tweetsReq:
            user_object = tweet.user

            if tweet.in_reply_to_status_id is not None:
                continue
            if tweet.user.verified == True:
                continue

            if not check_location(user_object.location):
                continue
            if not check_lang(tweet.full_text):
                continue

            user=tweet.user.screen_name
            user=user.lower()
            if (user.find('bot') != -1):
                continue
        
        
            tweets.append(dict(
                full_text = tweet.full_text,
                tweet_id=tweet.id_str,
                screen_name=tweet.user.screen_name,
                user_id=tweet.user.id_str,
                created_at=user_object.created_at,
                lang=user_object.lang,
                location=user_object.location,
                time_zone=user_object.time_zone,
                verified=user_object.verified,
                listed_count=user_object.listed_count,
                favourites_count=user_object.favourites_count,
                statuses_count=user_object.statuses_count,
                friends_count=user_object.friends_count,
                followers_count=user_object.followers_count
                ))
    except Exception as e:
        print(e, consumer_key, consumer_secret, access_token, access_token_secret)


    return tweets

def get_tweets(token_dict, keywords, q, num_tweets, date):
    for keyword in tqdm(keywords):
        tweets = search_tweets(
            token_dict['consumer_key'],
            token_dict['consumer_secret'],
            token_dict['access_token'],
            token_dict['access_token_secret'],
            keyword, num_tweets=num_tweets, date=date #20000
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


def get_keywords(keyword_file):
    with open(keyword_file) as f:
        keywords = f.read().strip().split('\n')

    return keywords



def collect_tweets_main(token_file, keyword_file, num_tweets, date):
    tokens = get_tokens(token_file)
    keywords = get_keywords(keyword_file)

    res_q = Queue()

    NUM_THREADS = len(tokens) #equivalent to num tokens
    KEYWORDS_PER_THREAD = ceil(len(keywords) / len(tokens))

    threads = []
    for i in range(NUM_THREADS):
        token_dict = tokens[i]
        start = int(i * KEYWORDS_PER_THREAD)
        thread_keywords = keywords[start: start + KEYWORDS_PER_THREAD]
        thread = Thread(target=get_tweets, args=(token_dict, thread_keywords, res_q, num_tweets, date, ))
        thread.start()
        threads.append(thread)

    #for thread in threads:
    #    thread.join()

    save_df_path = './data/users.csv'

    num_threads_collected = 0

    #while not res_q.empty():
    while True:
        try:
            res = res_q.get()
        except:
            if num_threads_collected == NUM_THREADS:
                break
            else:
                #sleep(600) #10 minutes sleep before checking if any new threads completed again
                continue

        res_df = pd.DataFrame(res)

        if os.path.isfile(save_df_path):
            loaded_df = pd.read_csv(save_df_path)
            res_df = pd.concat([loaded_df, res_df], ignore_index=True, sort=False)
        res_df.to_csv(save_df_path, index=False)
        num_threads_collected += 1

    print(res_df)
    return save_df_path



if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-k", "--keyword_file", help="Path to keyword file", type=str, required=True)
    parser.add_argument("-t", "--token_file", help="Path to token file", type=str, required=True)
    parser.add_argument("-d", "--date", help="Date [YYYY-MM-DD] before which we search", type=str, required=False, default=datetime.today().strftime('%Y-%m-%d'))
    parser.add_argument("-n", "--num_tweets", help="Number of tweets to collect", type=int, required=False, default=20000)

    args = parser.parse_args()
    keyword_file = args.keyword_file
    token_file = args.token_file
    num_tweets = int(args.num_tweets)
    date = args.date

    collect_tweets_main(token_file, keyword_file, num_tweets, date)
