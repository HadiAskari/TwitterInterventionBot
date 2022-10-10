# filename: match-tweet.py
# purpose: receives a tweet and decides whether bot should interact with that tweet, and on what topic

import pandas as pd
from collections import Counter
import random
import re

# examples
# input1 = 'Another player I’d like for the Knicks to take a hard look at if they’re picking in that real end-of-lotto range… RJ, Grimes, Reddish, Sochan would be a very cool core of young wings for NYK - defensively versatile and able to move the rock sharply https://t.co/jeZkws6wZ7'
# input2 = '"#DearRobManfred The players make the game, not you. Sincerely, All Baseball Fans'
# input3 = "Travis d'arnaud already got his World Series ring, so he's going after an Oscar's Trophy this time"
# input4 = "Travis d'arnaud already got his World Series ring, so he's going after an Oscars Trophy this time"
# input5 = "Travis d'arnaud already got his wedding ring, so he's going after an Oscars Trophy this time"
# matchKeywords(input1)

def check_word_in(phrase, text):
    try:
        return re.search(r"\b{}\b".format(phrase), text, re.IGNORECASE) is not None
    except:
        return None

def match_keywords(text):

    # get keywords
    keyword_df = pd.read_csv("utils/latest_keywords.csv")
    keywords = list(keyword_df['keyword'])

    # pre-processing
    text = text.lower() # what else? stemming? getting rid of ', like in Oscar's?

    matches = []

    # get all matches
    #matches = [word for word in keywords if (word in text)]
    for word in keywords:
        if check_word_in(word, text):
            matches.append(word)

    # get topics of all matches
    topics = []
    for match in matches:
        topic = keyword_df['topic'].loc[keyword_df['keyword'] == match].item()
        topics.append(topic)

    # determine topic and whether to interact
    if len(matches) == 0:
        interact = False
        topic = None
    else:
        interact = True
        if len(matches) == 1:
            topic = topics[0]
        else:
            most_frequent = Counter(topics).most_common()
            if len(most_frequent) == 1:
                topic = most_frequent[0][0]
            if len(most_frequent) > 1:
                topic = random.sample(most_frequent, 1)[0][0]

    return(interact, topic)


