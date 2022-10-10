import sys
import os

if __name__ == "__main__":
    try:
        user_file = sys.argv[2]
        clean_type = sys.argv[1]
        db_file = sys.argv[3]
    except:
        user_file = 'users.csv'
        clean_type = 'partial'
        db_file = 'data/database.db'


    os.system('python cleanup.py ' + str(clean_type))
    if clean_type == 'full':
        os.system('python construct_database.py ' + str(user_file))
    os.system('python main.py ' + str(user_file) + ' ' + str(db_file))
