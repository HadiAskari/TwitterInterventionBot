## How to run (test)

## Testing individual files:

- Tweets/Retweets: ```python get_re_tweets.py -u users/test.csv -t tokens/tokens.txt -n 100```
- Followees: ```python get_followees.py -u users/test.csv -t tokens/tokens.txt```
- Likes: ```python get_likes.py -u users/test.csv -t tokens/tokens.txt -n 100```

## Testing the user assignment
- Preferred approach is to run everything in one go and not require code files to be run individually: ```python assign_treatments.py -u users/test.csv -m utils/media_political_twitter.csv -d 100 -t tokens/tokens.txt -n 100```

- However, if metric files were run individually, the user assignment can also be run as follows: ```python assign_treatments.py -u users/test.csv -m utils/media_political_twitter.csv -f data/test_followees_df.csv -l data/test_likes_df.csv -r data/test_tweets_df.csv -d 100 -t tokens/token_file.txt -n 100```
