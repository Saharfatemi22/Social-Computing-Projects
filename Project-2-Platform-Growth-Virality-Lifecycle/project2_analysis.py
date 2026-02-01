# =========================
# Exercise 2.1 – Growth
# =========================

import pandas as pd
import matplotlib.pyplot as plt
import sqlite3

conn = sqlite3.connect("database.sqlite")

q = """
SELECT
  STRFTIME('%Y-%m', created_at) AS month,
  COUNT(*) AS monthly_load
FROM comments
GROUP BY STRFTIME('%Y-%m', created_at)
ORDER BY month;
"""
df = pd.read_sql_query(q, conn)
df["month"] = pd.to_datetime(df["month"] + "-01")

# I am calculating the average monthly growth rate
df["growth"] = df["monthly_load"].pct_change()
avg_growth = df["growth"].mean()
current = df["monthly_load"].iloc[-1]
forecast = current * (1 + avg_growth) ** 36  # 3 years ahead

# Servers: 16 handle current load → scale up for forecast +20%
servers_now = 16
per_server = current / servers_now
needed = int((forecast / per_server) * 1.2)

plt.plot(df["month"], df["monthly_load"], marker="o")
plt.title("Monthly comments trend")
plt.xlabel("Month"); plt.ylabel("Comments")
plt.xticks(rotation=45); plt.grid(True); plt.tight_layout()
plt.show()

print(f"Servers needed (3 years +20% redundancy): {needed}")

#I used the monthly number of comments as a proxy for server load. So, I decided to calculate the average growth rate per month and project it three years ahead. Since 16 servers handle the current load, I scaled the forecast to see how many servers are needed. After that I added 20% redundancy, the result is that the platform will need about 7 servers to stay reliable for the next 3 years.
#when I run the code the chart shows the monthly comments on the platform from early 2023 to late 2025.In the beginning, activity was very low, but it started to grow quickly after mid-2023. In 2024, the number of comments were increasing, though with some ups and downs, and at its peak it  hit 500 in a single month. I can understand from this, that user activity and engagement grew a lot during that time and the platform has experienced strong growth in engagement, even though the activity is not stable every month.

# =========================
# Exercise 2.2 – Virality
# =========================

#A post can become viral if its comments and reactions  are high 

# So I am counting the comments and reactions for every post
Being_viral = """
SELECT
    p.id AS post_id,
    COUNT(DISTINCT c.id) AS comment_count,
    COUNT(DISTINCT r.id) AS reaction_count,
    COUNT(DISTINCT c.id) + COUNT(DISTINCT r.id) AS virality_score
FROM posts p
LEFT JOIN comments c ON p.id = c.post_id
LEFT JOIN reactions r ON p.id = r.post_id
GROUP BY p.id
ORDER BY virality_score DESC
LIMIT 3;
"""
top3 = pd.read_sql_query(Being_viral, conn)
print("\nTop 3 viral posts (by combined comments + reactions):")
print(top3)

#post_id 2351 is the most viral post among posts and it has 62 comments and 139 reactions which is more than other posts.

# =========================
# Exercise 2.3 – Content Lifecycle
# =========================

q = """
SELECT
  p.id                 AS post_id,
  p.created_at         AS post_time,
  MIN(c.created_at)    AS first_engagement_time,
  MAX(c.created_at)    AS last_engagement_time
FROM posts p
LEFT JOIN comments c ON c.post_id = p.id
GROUP BY p.id
ORDER BY p.id;
"""

df = pd.read_sql_query(q, conn)

# I am converting it to the datetime
df["post_time"] = pd.to_datetime(df["post_time"])
df["first_engagement_time"] = pd.to_datetime(df["first_engagement_time"])
df["last_engagement_time"]  = pd.to_datetime(df["last_engagement_time"])

#  I am Keeping those  posts that actually received at least one comment
df = df.dropna(subset=["first_engagement_time"])

# Time deltas (hours)
df["hours_to_first"] = (df["first_engagement_time"] - df["post_time"]).dt.total_seconds() / 3600
df["hours_to_last"]  = (df["last_engagement_time"]  - df["post_time"]).dt.total_seconds() / 3600

avg_first = df["hours_to_first"].mean()
avg_last  = df["hours_to_last"].mean()

print(f"Average time to first engagement: {avg_first:.2f} hours")
print(f"Average time to last engagement:  {avg_last:.2f} hours")
print(f"Posts with engagement counted:    {len(df)}")
#when I run the code actually I see that average time to first engagement is 45.18 hours and the avreage time to last engagement is 138.95 hours and the count of  posts with engagements is 1215.
#The reactions table has no timestamp, so I measured engagement using comments only. For each post, I found the earliest and latest comment times and calculated the hours from the post’s publish time to those events. 

# =========================
# Exercise 2.4 – Connections
# =========================

#Iam  defining the  engagement between two users (A and B) like this:
#number of comments A leaves on B’s posts
#number of reactions A leaves on B’s posts.
#Then I’ll also count the reverse of the same thing (B → A).
#Finally, I am ranking  pairs by the total engagement in both directions that I calculated.

connections_query = """
WITH engagement AS (
    -- Comments as engagement
    SELECT
        c.user_id AS engager,
        p.user_id AS poster,
        COUNT(c.id) AS comment_count,
        0 AS reaction_count
    FROM comments c
    JOIN posts p ON c.post_id = p.id
    WHERE c.user_id != p.user_id
    GROUP BY engager, poster

    UNION ALL

    -- Reactions as engagement
    SELECT
        r.user_id AS engager,
        p.user_id AS poster,
        0 AS comment_count,
        COUNT(r.id) AS reaction_count
    FROM reactions r
    JOIN posts p ON r.post_id = p.id
    WHERE r.user_id != p.user_id
    GROUP BY engager, poster
),

pairwise AS (
    SELECT
        engager,
        poster,
        SUM(comment_count + reaction_count) AS engagement_score
    FROM engagement
    GROUP BY engager, poster
),

combined AS (
    SELECT
        CASE WHEN engager < poster THEN engager ELSE poster END AS user_a,
        CASE WHEN engager < poster THEN poster ELSE engager END AS user_b,
        SUM(engagement_score) AS total_engagement
    FROM pairwise
    GROUP BY
        CASE WHEN engager < poster THEN engager ELSE poster END,
        CASE WHEN engager < poster THEN poster ELSE engager END
)

SELECT user_a, user_b, total_engagement
FROM combined
ORDER BY total_engagement DESC
LIMIT 3;
"""

top3_pairs = pd.read_sql_query(connections_query, conn)
print("\nTop 3 user pairs with strongest mutual engagement:")
print(top3_pairs)
#When I run the code I can see User 38 and User 88 with 16 engagements
#User 9 and User 51 with 13 engagements
#User 13 and User 54 with 13 engagements are at the top.
#I can see that these pairs interacted with each other’s posts more than any other users on the platform.










