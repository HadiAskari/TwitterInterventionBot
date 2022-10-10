import random
import pandas as pd
import numpy as np
#from assign_treatments import assign_treatment_per_block

def assign_treatment_per_block(user_df):
    uniq_blocks = np.unique(user_df['block'].to_list())
    user_df['condition'] = [-1]*len(user_df)
    for block_type in uniq_blocks:
        sub_user_df = user_df[user_df['block'] == block_type]
        block_len = len(sub_user_df)
        possible_treatments = [0,1,2]
        treatments = []
        random.shuffle(possible_treatments)
        print(possible_treatments)
        selector = 0
        for i in range(block_len):
            treatments.append(possible_treatments[selector])
            selector += 1
            if selector == 3:
                selector = 0

        for idx in sub_user_df.index:
            user_df.iloc[idx]['condition'] = treatments.pop()
    return user_df



df = pd.DataFrame({'block': [100,111,110,101,111,100,110,111,111]})
print(df)

x = assign_treatment_per_block(df)
print(x)
