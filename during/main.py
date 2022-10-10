
import csv
import pandas as pd
from datetime import datetime, timedelta
from time import time, sleep
import json
from collections import defaultdict
import response
import random
from get_tweets import run_collection
from match_tweet import match_keywords
import os
from tqdm.auto import tqdm
import math
import sqlite3
from post_response import run_posting
import torch
import sys
import numpy as np
import argparse


def get_previous_time(useridname, db_file):
    conn=sqlite3.connect(db_file)
    c=conn.cursor()
    c.execute("SELECT last_replied FROM users WHERE userid = (?)", [useridname])
    result=c.fetchone()

    return result[0]

def get_hours(useridname, db_file):
        #if user was replied to in the past 24 hours then continue
        previous_time=get_previous_time(useridname, db_file)
        datetime_object = datetime.strptime(previous_time, '%Y/%m/%d %H:%M:%S')

        a = datetime(now.year, now.month, now.day, now.hour, now.minute, now.second)
        b=datetime(datetime_object.year,datetime_object.month, datetime_object.day, datetime_object.hour, datetime_object.minute, datetime_object.second)

        c = a-b

        hours = math.floor(c.total_seconds() / 3600)

        return hours


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--user_file", help="Path to user file", type=str, required=True)
    parser.add_argument("-db", "--db_file", help="Path to database file", type=str, required=True)
    parser.add_argument("-t", "--token_file", help="Path to token file", type=str, required=True)
    parser.add_argument("-c", "--control_bool", help="Boolean indicating whether this is a control group experiment", type=str, required=True)
    parser.add_argument("-p", "--post_bool", help="Boolean indicating whether we should post generated responses", type=str, required=True)

    args = parser.parse_args()
    user_file = args.user_file
    db_file = args.db_file
    token_file = args.token_file
    control_bool = args.control_bool.lower()
    post_bool = args.post_bool.lower()

    if control_bool == "true":
        control_bool = True
    else:
        control_bool = False
    if post_bool == "true":
        post_bool = True
    else:
        post_bool = False

    #print(user_file, db_file, token_file, post_bool, control_bool)

    #Prepare response generator model/files
    response_templates, news_templates, sports_df, entertainment_df, lifestyle_df = response.load_all_files()
    tokenizer, model = response.load_model()

    # Initialize variable indicating global iteration of the code
    GLOBALCOUNT = 0
    last_posted_gc = 0


    while True:

        GLOBALCOUNT += 1
   

        now = datetime.now()
        dt_string = now.strftime("%Y-%m-%d")

        run_collection(GLOBALCOUNT, user_file, db_file, token_file) 

        post_tweets_dump=[]
        userid=[]
        originalTweet=[]
        tweetid=[]
        timestamp=[]
        gc = []
        sname = []

        df_pkl_file = 'data/' + user_file.split('users/')[1].split('.csv')[0] + '_df.pkl'
        data_df = pd.read_pickle(df_pkl_file)
        print(data_df)

        #sub_df = data_df[data_df['GLOBALCOUNT'] == GLOBALCOUNT]
        sub_df = data_df[data_df['GLOBALCOUNT'] > last_posted_gc]
        users_list = sub_df['user'].to_list()

        done_check = defaultdict(lambda: False)

        for idx in tqdm(range(len(sub_df))):
            useridname = sub_df.iloc[idx]['user']
            tweet = sub_df.iloc[idx]['full_text']
            ids = sub_df.iloc[idx]['tweet_id']

            #if user in treatment group then continue with the rest
            if control_bool:
                continue

            hours=get_hours(useridname, db_file)
            #if user was replied to in the past 24 hours then continue

            if GLOBALCOUNT != 1:
                if hours < 24: ###### Change to 24
                    continue

            if done_check[useridname]:
               continue

            #match tweet
            interact, topic = match_keywords(tweet)

            if interact:
                generated_responses = response.run_model([tweet], tokenizer, model, response_templates)
                generated_output=response.append_url(topic, generated_responses, news_templates, sports_df, entertainment_df, lifestyle_df)
                post_tweets_dump.append(generated_output)
                originalTweet.append(tweet)
                tweetid.append(ids)
                userid.append(useridname)
                now = datetime.now()
                dt_string = now.strftime("%Y/%m/%d %H:%M:%S")
                timestamp.append(dt_string)
                gc.append(GLOBALCOUNT)
                sname.append(sub_df.iloc[idx]['screen_name'])
                done_check[useridname] = True
                last_posted_gc = GLOBALCOUNT
            else:
                continue
        
        replydict={'UserID': userid, 'Screen_Name': sname, 'TweetID': tweetid, 'Original_Tweet': originalTweet, 'Reply': post_tweets_dump, 'GLOBALCOUNT': gc, 'TimeStamp': timestamp}
        reply_df=pd.DataFrame(replydict)

        print(reply_df)

        if post_bool:
            run_posting(reply_df, dt_string, user_file, db_file, token_file)
        else:
            rdf_pkl_file = 'data/' + user_file.split('users/')[1].split('.csv')[0] + '_replies_df.pkl'
            if os.path.isfile(rdf_pkl_file): ##
                loaded_df = pd.read_pickle(rdf_pkl_file) ##
                reply_df = pd.concat([loaded_df, reply_df], ignore_index=True, sort=False)

            reply_df.to_pickle(rdf_pkl_file) ##


        sleep(28800 - time() % 28800) #8 hours previously
        #sleep(86400 - time() % 86400) #This is 24 hours
        #sleep(3600 - time() % 3600) #### 1 hour

        ### Implement better exit mechanism with if and break ###
        if GLOBALCOUNT > 100:
            break


