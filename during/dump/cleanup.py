import sys
import os

try:
    opt = sys.argv[1]
except:
    opt = 'partial'

if opt == 'full':
    os.system('rm -rf data')
    os.system('mkdir data')
elif opt == 'partial':
    os.system('rm -rf data/df.pkl data/replies_df.pkl')

