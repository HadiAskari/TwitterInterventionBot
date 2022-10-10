import argparse
import pandas as pd
import numpy as np
from filter_bots import botometer_filter_main
from collect_users import collect_tweets_main
from datetime import datetime

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-k", "--keyword_file", help="Path to keyword file", type=str, required=True)
    parser.add_argument("-t", "--token_file", help="Path to token file", type=str, required=True)
    parser.add_argument("-d", "--date", help="Date [YYYY-MM-DD] before which we search", type=str, required=False, default=datetime.today().strftime('%Y-%m-%d'))
    parser.add_argument("-n", "--num_tweets", help="Number of tweets to collect", type=int, required=False, default=20000)
    parser.add_argument("-b", "--botometer_token_file", help="Path to botometer token file", type=str, required=True)

    args = parser.parse_args()
    keyword_file = args.keyword_file
    token_file = args.token_file
    num_tweets = int(args.num_tweets)
    date = args.date
    botometer_token_file = args.botometer_token_file

    user_file = collect_tweets_main(token_file, keyword_file, num_tweets, date)
    
    filtered_user_file = botometer_filter_main(user_file, token_file, botometer_token_file)

    df = pd.read_csv(filtered_user_file)
    final_df = pd.DataFrame({'UserIDs': df['user_id_str'].to_list()})
    print(final_df)
    final_df.to_csv('data/users_FINAL.csv', index=False)
