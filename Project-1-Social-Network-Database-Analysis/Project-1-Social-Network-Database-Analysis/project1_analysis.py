# Project 1 – Social Network Database Analysis
# Social Computing – University of Oulu
# =========================
# 1.1 Database Exploration
# =========================
### First  I am importing SQLite library for python for reading database and also pandas provides support for importing data from SQLite database file.
###I am using os for clearing the terminal

import sqlite3
import pandas as pd
import os
os.system('clear')

###I am saving the database.sqlite in a variable and then connecting the database to python using sqlite3.connect()

MY_FILE = "database.sqlite"
try:
    conn = sqlite3.connect(MY_FILE)
    print("SQLite Database connection successful")
except Exception as e:
    print(f"not working'{e}'")

###Now I want to see the names of the tables so I write SELECT name
tablenames_df = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'", conn)
print(tablenames_df)

###Now I want to see all the information and data about each table. I useSELECT* to see all columns and rows
for table in ["follows", 'users', 'reactions', 'comments', 'posts']:
    print(f'\n\nThis is the information of {table}')
    table= pd.read_sql_query(f"SELECT * FROM {table}", conn)
    print(table)
    print(f"this is the column names of this table:{table.columns}")
### Information of (follows) table: I can see 2 columns named follower_id , followed_id
#The table has 7225 rows
### Information of (users) table: I can see 7 columns named 'id', 'username', 'location', 'birthdate', 'created_at', 'profile','password'
#This table is about users’ information. The table has 210 rows
### Information of (reactions)table: I can see 4 columns named 'id', 'post_id', 'user_id', 'reaction_type'
#The table has 8276 rows. All columns are integer except reaction_type which is a string.
#Id is a Unique identifier for each reaction and post_id shows which post this reaction belongs to.

###Information of (comments)table: I can see 5 columns named ‘id', 'post_id', 'user_id', 'content', 'created_at' and 5804 rows. The content column stores the  text of the post for example the message, status update, or caption written by the user.

###Infromation of (posts) table: I can see 4 columns named 'id', 'user_id', 'content', 'created_at' and 1303 rows. id column means which post is this? And the user_id column means who wrote this post.

# =========================
# 1.2 Lurkers
# =========================
###In the question I see that I should find the users that did not posted, interacted with posts. So, 4 tables I need to write my code. Those are users, posts, comments, reactions. I do not need the follows table.
#First I use error handling block(try) then I use read_sql_query function to run an SQL query.
#After that, COUNT(*) counts all rows that I need. I put the column name lurkers with As lurkers.
#FROM users takes the data from users table where users.id is not in posts, comments, and reactions tables. I use DISTINCT  because I want to remove duplicates if a user has many posts, comments or reactions. Only users who are missing from all three tables remain. I ran the code and the number of lurkers are 55.

try:
    lurkers_df = pd.read_sql_query("""
    SELECT
        COUNT(*) AS lurkers
    FROM
        users u
    WHERE
        u.id NOT IN (SELECT DISTINCT user_id FROM posts)
        AND u.id NOT IN (SELECT DISTINCT user_id FROM comments)
        AND u.id NOT IN (SELECT DISTINCT user_id FROM reactions);
    """, conn)
    
    print(f'\n\nNumber of lurkers on the platform')
    print(lurkers_df)
except Exception as e:
    print(f"not working: {e}")

# =========================
# 1.3 Influencers
# =========================
###I am using comments and reactions tables as they are engagement related tables. I am selecting all user IDs from the comments and reactions tables and combining them with union all. I use union all because I want to keep the duplicates and get one combined list of all user activity. I use order by desc because I want to see the biggest numbers first and limit5 to see top 5. The user_id 88 with total engagement 165 has the most engagement.

try:
    influencers_df = pd.read_sql_query("""
    SELECT
        user_id,
        (COUNT(*) ) AS total_engagement
    FROM (
        SELECT user_id FROM comments
        UNION ALL
        SELECT user_id FROM reactions
    )
    GROUP BY user_id
    ORDER BY total_engagement DESC
    LIMIT 5;
    """, conn)

    print(f'\n\nTop 5 influencers')
    print(influencers_df)
except Exception as e:
    print(f"not working: {e}")

# =========================
# 1.4 Spammers
# =========================
###I should check comments and posts tables  for this exercise. First I check posts table then comments table. I use repeat_count that will calculate how many times that user posted that exact text(COUNT(*) AS repeat_count). I am using 2 froms. The inner  from is for pulling raw data and the outer one is for making the grouped results as a new table to filter on. I use where repeat_count>=3 because it keeps only rows where the number of repeats is 3 or more. In the results I can see that the number of scammers in posts are higher than the ones in the comments. The person with user_id 521 has the highest number of repeat counts. She or he has 22 repeated spam posts overall. Only one person with user_id 530 is the spammer in the comments table who has more than 3 spams.


spam_posts_df = pd.read_sql_query("""
SELECT
    user_id,
    content,
    repeat_count
FROM (
    SELECT
        user_id,
        content,
        COUNT(*) AS repeat_count
    FROM
        posts
    GROUP BY
        user_id, content
)
WHERE repeat_count >= 3;
""", conn)

if spam_posts_df.empty:
    print("No spammers in posts.")
else:
    print("Spammers are found in posts")
    print(spam_posts_df)

spam_comments_df = pd.read_sql_query("""
SELECT
    user_id,
    content,
    repeat_count
FROM (
    SELECT
        user_id,
        content,
        COUNT(*) AS repeat_count
    FROM
        comments
    GROUP BY
        user_id, content
)
WHERE repeat_count >= 3;
""", conn)

if spam_comments_df.empty:
    print("No spammers in comments.")
else:
    print("Spammers found in comments")
    print(spam_comments_df)

