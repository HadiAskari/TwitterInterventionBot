import csv
import pandas as pd
from datetime import datetime
import json
from collections import defaultdict
import sqlite3
from tqdm.auto import tqdm
import sys

def CreateTable(db_filename):
    conn=sqlite3.connect(db_filename) ##
    c=conn.cursor()
    c.execute("""CREATE TABLE users (
    userid TEXT,
    Treatment TEXT,
    last_replied TEXT,
    sinceid TEXT
    );
    """)

    print("Table Created Successfully")
    conn.commit()
    conn.close()

def PopulateTableforTest(user_file, db_file):

    now = datetime.now()
    dt_string = now.strftime("%Y/%m/%d %H:%M:%S")
 
    print("now =", dt_string)


    df=pd.read_csv(user_file)

    names=df.iloc[:,0].to_list()

    corrected_names=[]
    treatment_group=[]
    last_replied=[]
    sinceid=[]
    

    for name in names:
        name=str(name)
        name=name.split('.csv')[0]
        corrected_names.append(name)
        treatment_group.append('True')
        last_replied.append(dt_string)
        sinceid.append('12345')

    for i in tqdm(range(len(corrected_names))):
        conn=sqlite3.connect(db_file) ##
        c=conn.cursor()

        mytuple=(corrected_names[i], treatment_group[i], last_replied[i], sinceid[i])

        sqlite_insert_with_param = """INSERT INTO users
                          VALUES (?, ?, ?, ?)"""

        c.execute(sqlite_insert_with_param, mytuple)

        print("Table Updated Successfully")

        conn.commit()
        conn.close()


def ViewTable(db_file):
    conn=sqlite3.connect(db_file)
    c=conn.cursor()
    c.execute("SELECT * FROM users")
    print(c.fetchmany(5))
    conn.commit()
    conn.close()




if __name__ == "__main__":
    try:
        user_filename = sys.argv[1]
        db_filename = sys.argv[2]
    except:
        print("Please add userfile and db file")

    CreateTable(db_filename)
    PopulateTableforTest(user_filename, db_filename)
    ViewTable(db_filename)
 
