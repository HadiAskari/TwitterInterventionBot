import pandas as pd
from datetime import timedelta
import argparse
import numpy as np
from get_followees import get_followees_main
from get_likes import get_likes_main
from get_re_tweets import get_tweets_main
import random

# this is for testing
# media_file = 'pre-metrics/utils/media_political_twitter.csv'
# followees_file = 'pre-metrics/data/test_followees_df.csv'
# likes_file = 'pre-metrics/data/test_likes_df.csv'
#  tweets_file = 'pre-metrics/data/test_tweets_df.csv'
#  user_file = 'pre-metrics/users/test.csv'
#  days_to_summarize = 100

def filter_summary_days(df, number_of_days):
    number_of_days = int(number_of_days)
    df[['created_at', 'collected_at']] = df[['created_at', 'collected_at']].apply(pd.to_datetime)
    df[['first_summary_day']] = df[['collected_at']] - timedelta(days=number_of_days)
    df['first_summary_day'] = pd.to_datetime(df['first_summary_day'], utc=True)
    df = df[df['created_at'] >= df['first_summary_day']]
    return df


def summarize_users(users, media_accounts, followees, likes, tweets, days):
    media_accounts_df = pd.read_csv(media_accounts, dtype=str)
    media_accounts_df = media_accounts_df.drop(['index', 'name', 'origin_list'], axis=1)
    followees_df = pd.read_csv(followees, dtype=str)
    likes_df = pd.read_csv(likes, dtype=str)
    tweets_df = pd.read_csv(tweets, dtype=str)
    user_df = pd.read_csv(users, dtype=str)
    # TO DO: adapt the following line depending on user csv looks like
    user_df.rename(columns={'UserIDs': 'original_user_id'}, inplace=True)
    user_df = user_df.drop(user_df.columns[1], axis=1)

    # Summarize followees
    followees_df = followees_df.merge(media_accounts_df, left_on='followees', right_on='media_user_id', how='left')
    followees_summ = followees_df.groupby('original_user_id')['followees', 'media_user_id'].agg('count')
    followees_summ.rename(columns={'followees': 'n_followees',
                                   'media_user_id': 'n_media_followees'}, inplace=True)
    followees_summ.reset_index(inplace=True)
    followees_summ['prop_media_followees'] = followees_summ['n_media_followees'] / followees_summ['n_followees']

    # Summarize tweets
    tweets_df_filtered = filter_summary_days(df=tweets_df, number_of_days=days)
    tweets_df_filtered = tweets_df_filtered.merge(media_accounts_df, left_on='retweeted_user_ID',
                                                  right_on='media_user_id', how='left')
    tweets_summ = tweets_df_filtered.groupby('original_user_id')[
        'tweet_id', 'retweeted_user_ID', 'media_user_id'].agg('count')
    tweets_summ.rename(columns={'tweet_id': 'n_retweets_tweets',
                                'retweeted_user_ID': 'n_retweets',
                                'media_user_id': 'n_media_retweets'}, inplace=True)
    tweets_summ.reset_index(inplace=True)
    tweets_summ['prop_media_retweets'] = tweets_summ['n_media_retweets'] / tweets_summ['n_retweets']

    # Summarize likes
    likes_df_filtered = filter_summary_days(likes_df, days)
    likes_df_filtered = likes_df_filtered.merge(media_accounts_df, left_on='liked_user_id', right_on='media_user_id',
                                                how='left')
    likes_summ = likes_df_filtered.groupby('original_user_id')['tweet_id', 'media_user_id'].agg('count')
    likes_summ.rename(columns={'tweet_id': 'n_likes',
                               'media_user_id': 'n_media_likes'}, inplace=True)
    likes_summ.reset_index(inplace=True)
    likes_summ['prop_media_likes'] = likes_summ['n_media_likes'] / likes_summ['n_likes']

    # Merge all three summary dfs to user df
    users_summ = user_df.merge(followees_summ, on='original_user_id', how='left')
    users_summ = users_summ.merge(tweets_summ, on='original_user_id', how='left')
    users_summ = users_summ.merge(likes_summ, on='original_user_id', how='left')

    return users_summ

def assign_treatment_per_block(user_df):
    uniq_blocks = np.unique(user_df['block'].to_list())
    final_treatments = [-1]*len(user_df)
    for block_type in uniq_blocks:
        sub_user_df = user_df[user_df['block'] == block_type]
        block_len = len(sub_user_df)
        possible_treatments = [0,1,2]
        treatments = []
        np.random.shuffle(possible_treatments)
        selector = 0
        for i in range(block_len):
            treatments.append(possible_treatments[selector])
            selector += 1
            if selector == 3:
                selector = 0

        for idx in sub_user_df.index:
            final_treatments[idx] = treatments.pop()
    return final_treatments

def block_assign(user_data):
    # this assigns users to "blocks" for a variable
    # here, I use the three proportions, and put into one block if 0 or another if 1
    # TO DO: Update with the final set of variables/cutoffs
    user_data['prop_media_followees_block'] = user_data['prop_media_followees'].apply(
        lambda x: '1' if x == 0 else '0')
    user_data['prop_media_likes_block'] = user_data['prop_media_likes'].apply(lambda x: '1' if x == 0 else '0')
    user_data['prop_media_retweets_block'] = user_data['prop_media_retweets'].apply(lambda x: '1' if x == 0 else '0')
    cols = ['prop_media_followees_block', 'prop_media_likes_block', 'prop_media_retweets_block']
    user_data['block'] = user_data[cols].apply(lambda row: '_'.join(row.values.astype(str)), axis=1)

    #user_data['condition'] = user_data.groupby('block', sort=False).ngroup() ### Anshuman
    ret_conds = assign_treatment_per_block(user_data)
    user_data['condition'] = ret_conds

    users_assigned = user_data[['original_user_id', 'block', 'condition']] ### Anshuman
    return users_assigned


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--user_file", help="Path to user file", type=str, required=True)
    parser.add_argument("-m", "--media_file", help="Path to media accounts file", type=str, required=True)
    parser.add_argument("-f", "--followees_file", help="Path to followees csv", type=str, required=False) ### Anshuman
    parser.add_argument("-l", "--likes_file", help="Path to likes csv", type=str, required=False) ### Anshuman
    parser.add_argument("-r", "--tweets_file", help="Path to (re)tweets csv", type=str, required=False) ### Anshuman
    parser.add_argument("-d", "--days_to_summarize", help="How many days prior to summarize", type=str, required=True)
    parser.add_argument("-t", "--token_file", help="Path to token file", type=str, required=True) ### Anshuman
    parser.add_argument("-n", "--num_tweets", help="Number of tweets to search-- should be less than 200", type=int, required=True) ### Anshuman

    args = parser.parse_args()
    user_file = args.user_file
    media_file = args.media_file
    followees_file = args.followees_file
    likes_file = args.likes_file
    tweets_file = args.tweets_file
    days_to_summarize = args.days_to_summarize
    token_file = args.token_file ### Anshuman
    num_tweets = int(args.num_tweets) ### Anshuman

    if likes_file is None or tweets_file is None or followees_file is None: ### Anshuman
        followees_file = get_followees_main(user_file, token_file)
        likes_file = get_likes_main(user_file, token_file, num_tweets)
        tweets_file = get_tweets_main(user_file, token_file, num_tweets)

    
    users_summary = summarize_users(users=user_file,
                                    media_accounts=media_file,
                                    followees=followees_file,
                                    likes=likes_file,
                                    tweets=tweets_file,
                                    days=days_to_summarize)
    users_conditions = block_assign(users_summary)

    users_control = users_conditions[users_conditions['condition'] == 0] ### Anshuman
    users_treatment_1 = users_conditions[users_conditions['condition'] == 1] ### Anshuman
    users_treatment_2 = users_conditions[users_conditions['condition'] == 2] ### Anshuman

    save_df_path = 'data/' + user_file.split('users/')[1].split('.csv')[0] + '_users_assigned.csv'
    users_conditions.to_csv(save_df_path, index=False)

    users_control.to_csv('data/users_control.csv', index=False)
    users_treatment_1.to_csv('data/users_treatment_1.csv', index=False)
    users_treatment_2.to_csv('data/users_treatment_2.csv', index=False)

    print(users_conditions)
    
