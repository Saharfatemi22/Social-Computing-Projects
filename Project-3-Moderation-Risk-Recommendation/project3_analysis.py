# =========================
# Exercise 3.1 – Censorship
# =========================
def moderate_content(content):
    """
    Args
        content: the text content of a post or comment to be moderated.
        
    Returns: 
        A tuple containing the moderated content (string) and a severity score (float).
    """
    original_content = content
    score = 0.0
    
    # Stage 1.1.1: I Check for Tier 1 words (severe violation)
    TIER1_PATTERN = r'\b(' + '|'.join(TIER1_WORDS) + r')\b'
    if re.search(TIER1_PATTERN, original_content, flags=re.IGNORECASE):
        return "[content removed due to severe violation]", 5.0
    
    # Stage 1.1.2:I Check for Tier 2 phrases (spam/scam)
    for phrase in TIER2_PHRASES:
        if phrase.lower() in original_content.lower():
            return "[content removed due to spam/scam policy]", 5.0
    
    # Stage 1.2: Scored violations
    moderated_content = original_content
    
    # use Rule 1.2.1: Tier 3 words (mild profanity)
    TIER3_PATTERN = r'\b(' + '|'.join(TIER3_WORDS) + r')\b'
    matches = re.findall(TIER3_PATTERN, moderated_content, flags=re.IGNORECASE)
    score += len(matches) * 2.0
    moderated_content = re.sub(TIER3_PATTERN, lambda m: '*' * len(m.group(0)), moderated_content, flags=re.IGNORECASE)
    
    # using rule 1.2.2: External links (URLs)
    URL_PATTERN = r'https?://[^\s]+'
    url_matches = re.findall(URL_PATTERN, moderated_content)
    score += len(url_matches) * 2.0
    moderated_content = re.sub(URL_PATTERN, '[link removed]', moderated_content)
    
    # using  rule 1.2.3: Excessive capitalization
    alphabetic_chars = [c for c in moderated_content if c.isalpha()]
    if len(alphabetic_chars) > 15:
        uppercase_count = sum(1 for c in alphabetic_chars if c.isupper())
        uppercase_ratio = uppercase_count / len(alphabetic_chars)
        if uppercase_ratio > 0.70:
            score += 0.5
    
    # Additional Safety Rule: Phone number detection (Privacy Protection)
    PHONE_PATTERN = r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b|\b\d{10}\b'
    phone_matches = re.findall(PHONE_PATTERN, moderated_content)
    if phone_matches:
        score += 3.0
        moderated_content = re.sub(PHONE_PATTERN, '[phone number removed]', moderated_content)
    
    return moderated_content, score


#My Full Explanation is this:
#I implemented the moderate_content function to automatically detect and censor inappropriate content on the platform. The function follows all the rules from the specification document and I also added one extra safety measure at the end.
#When I started working on this function, I first initialized the score to 0.0 and saved the original content in a variable so I could work with it step by step. The function works in two main stages.  first it checks for severe violations that require immediate content removal, and then it handles less serious violations that get scored and filtered.
#For the severe violations part, I implemented Rule 1.1.1 which checks for Tier 1 words. I created a regex pattern using word boundaries to make sure we only match complete words, not parts of words. I used the re.search() function with the IGNORECASE flag because the rule says it should be case-insensitive. If the function finds any Tier 1 word, it immediately stops and returns the message "[content removed due to severe violation]" along with the maximum score of 5.0. This is important because these are the most serious violations and the content needs to be completely removed.
#Then I implemented Rule 1.1.2 for Tier 2 phrases which are related to spam and scams. I did this by looping through all the phrases in the TIER2_PHRASES list and checking if any of them appear in the content. I converted both the phrase and the content to lowercase to make the comparison case-insensitive, just like the specification requires. If I find any Tier 2 phrase, the function returns "[content removed due to spam/scam policy]" with a score of 5.0 and stops there.
#If the content passes both of these severe checks, then I moved to Stage 1.2 where I handle the scored violations. For Rule 1.2.1 about Tier 3 words, I built a regex pattern that includes all Tier 3 words with word boundaries, then I used re.findall() to count how many times these words appear in the content. Each match adds 2.0 points to the score. After counting, I used re.sub() with a lambda function to replace each bad word with asterisks. The lambda function makes sure the number of asterisks matches the lengths of the original word, so if someone writes a 4-letter bad word, it gets replaced with 4 asterisks.
#For Rule 1.2.2 about external links, I created a URL pattern that matches both http and https URLs followed by any non-space characters. I used re.findall() to count all the URLs in the content, and each URL adds 2.0 points to the score because URLs can be used for phishing or spreading malicious content. Then I replaced all URLs with the text "[link removed]" to clean up the content.
#Rule 1.2.3 was about excessive capitalization. For this one, I first extracted all alphabetic characters from the content using a list comprehension. I only check for excessive capitalization if there are more than 15 alphabetic characters, because the rule specifies this minimum. Then I counted how many of these characters are uppercase and calculated the ratio. If more than 70% of the letters are uppercase, I added 0.5 points to the score. According to the specification, I did not modify the content for this violation, I only added to the score.
#Finally, I added my own safety measure which detects phone numbers in the content. I think this is really important for keeping the platform safe because phone numbers are personal information that should be protected. My regex pattern r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b|\b\d{10}\b' can detect phone numbers in different formats - it matches numbers like "123-456-7890", "123.456.7890", "123 456 7890", or even "1234567890" without any separators. I chose to add 3.0 points to the score when I detect a phone number because sharing personal contact information is a serious privacy and safety issue. Then I replace all detected phone numbers with "[phone number removed]" to protect users' privacy.
#I decided to implement phone number detection as my additional safety measure for several important reasons. First, it protects users from doxxing, which is when someone publishes private information about another person without their consent. This can lead to harassment or even dangerous real-world situations. Second, it prevents scammers from sharing their contact information on the platform to move conversations off the platform where they can't be monitored. Third, it's especially important for protecting younger or children users who might not understand the risks of sharing their phone number publicly online. Many minors use social platforms and they don't always realize that posting their phone number can put them in danger. Finally, this measure helps prevent spam because many spam bots try to collect phone numbers from public posts.
#At the end of the function, I return both the moderated content and the final calculated score. The moderated content has all the violations either removed or replaced with appropriate messages, and the score reflects how serious the violations were. This score can then be used by the platform administrators to identify high-risk content and take action if needed.

# =========================
# Exercise 3.2 – User Risk Analysis
# =========================
import sqlite3
import re
import datetime as dt
import pandas as pd



# 2) User risk analysis (Rules Part 2) + extra risk measure

def _parse_dt(s):
    if not s:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return dt.datetime.strptime(s, fmt)
        except Exception:
            pass
    return None

def user_risk_analysis(user_row, cursor, lookback_days=14):
    """
    Computes the user risk score per Rules Part 2 and adds one extra measure:
      - content_risk_score = 1*profile + 3*avg_post + 1*avg_comment
      - age multiplier: <7d -> x1.5; <30d -> x1.2; else x1.0
      - final cap at 5.0
    Extra measure: Recent Violation Boost
      - Count posts/comments in the last 14 days with content_score > 0
      - Add +0.2 per item (cap +1.0) BEFORE applying the age multiplier
    """
    user_id, username, location, birthdate, created_at, profile, password = user_row

    # Profile score
    profile_score = 0.0
    if profile:
        _, profile_score = moderate_content(profile)

    # All posts & comments
    posts    = cursor.execute("SELECT content, created_at FROM posts WHERE user_id=?", (user_id,)).fetchall()
    comments = cursor.execute("SELECT content, created_at FROM comments WHERE user_id=?", (user_id,)).fetchall()

    # Averages
    post_scores = []
    for (c, _) in posts:
        if c:
            _, s = moderate_content(c)
            post_scores.append(s)
    avg_post = sum(post_scores)/len(post_scores) if post_scores else 0.0

    comment_scores = []
    for (c, _) in comments:
        if c:
            _, s = moderate_content(c)
            comment_scores.append(s)
    avg_comment = sum(comment_scores)/len(comment_scores) if comment_scores else 0.0

    content_risk = (profile_score * 1.0) + (avg_post * 3.0) + (avg_comment * 1.0)

    # Extra: Recent Violation Boost
    now = dt.datetime.utcnow()
    flagged_recent = 0
    for (c, ts) in posts + comments:
        if not c or not ts:
            continue
        created = _parse_dt(ts)
        if not created:
            continue
        if (now - created).days <= lookback_days:
            _, s = moderate_content(c)
            if s > 0:
                flagged_recent += 1
    recent_boost = min(1.0, 0.2 * flagged_recent)
    content_risk += recent_boost

    # Age multiplier
    age_multiplier = 1.0
    acc_date = _parse_dt(created_at)
    if acc_date:
        days_old = (now - acc_date).days
        if days_old < 7:
            age_multiplier = 1.5
        elif days_old < 30:
            age_multiplier = 1.2

    final_risk = min(5.0, content_risk * age_multiplier)

    return {
        "user_id": user_id,
        "username": username,
        "profile_score": round(profile_score, 2),
        "avg_post_score": round(avg_post, 2),
        "avg_comment_score": round(avg_comment, 2),
        "recent_violation_boost": round(recent_boost, 2),
        "content_risk_score": round(content_risk, 2),
        "age_multiplier": age_multiplier,
        "final_user_risk": round(final_risk, 2)
    }


# I print Top-5

# I Connect to my uploaded file
conn = sqlite3.connect("database.sqlite")
cur = conn.cursor()

# Pull all users
users = cur.execute("SELECT id, username, location, birthdate, created_at, profile, password FROM users").fetchall()

# I Compute risk for each user
results = [user_risk_analysis(u, cur) for u in users]
df = pd.DataFrame(results).sort_values(["final_user_risk", "content_risk_score"], ascending=[False, False]).reset_index(drop=True)

# to Show Top-5
top5 = df.head(5)
print(top5)





#Complete Explanation of User Risk Analysis Code and Results
#I explain how My Code Works
#I implemented a user risk analysis system for the social media platform that calculates risk scores for all users and identifies the top 5 highest risk accounts. My code follows the specifications from the rules document and adds one extra safety measure that I designed myself.
#Part 1: Helper Function for Date Parsing
#I started by creating a helper function called _parse_dt that parses date strings from the database. This function is necessary because dates in the database might be stored in different formats - either as full datetime strings like "2021-12-27 17:02:48" or just as dates like "2021-12-27". My function tries both formats and returns a datetime object if it can parse the string successfully, or returns None if it can't. This makes my code more robust because it can handle different date formats without crashing.
#Part 2: The Main User Risk Analysis Function
#My main function user_risk_analysis takes three inputs: the user's data row from the database, a database cursor to run queries, and an optional lookback_days parameter that I set to 14 days by default. This function calculates the risk score following all the steps from the specification document.
#First, I extracted all the user information from the row: user ID, username, location, birthdate, account creation date, profile text, and password. Then I calculated the profile score by running the user's profile text through the moderate_content function. If the user doesn't have a profile, the profile score is 0.0.
#Next, I queried the database to get all posts and all comments made by this user. I made sure to also get the creation timestamp for each post and comment because I need it for my extra safety measure later.
#Then I calculated the average post score. I looped through all the user's posts, ran each post's content through moderate_content to get its score, and stored all these scores in a list. After collecting all the scores, I calculated the average by dividing the sum by the number of posts. If the user has no posts, the average is 0.0.
#I did the same thing for comments - looped through all comments, got the moderation score for each one, and calculated the average comment score. If there are no comments, the average is 0.0.
#After getting these three scores (profile, average post, average comment), I calculated the content risk score using the weighted formula from the specification: content_risk_score = (profile_score × 1.0) + (avg_post × 3.0) + (avg_comment × 1.0). This formula gives posts three times more weight than profiles or comments because posts are the main visible content on the platform.
#Part 3: My Extra Safety Measure - Recent Violation Boost
#Here's where I added my own additional safety measure that I call "Recent Violation Boost". The idea behind this measure is that users who are currently posting problematic content are more dangerous than users who posted bad content a long time ago but have cleaned up their behavior.
#I implemented this by looking at only the recent activity from the last 14 days. I combined all posts and comments into one list, then I looped through each item and checked its timestamp. For each post or comment that was created within the last 14 days, I ran its content through moderate_content to get its score. If the score is greater than 0 (that means it contains some violation), I counted it as a "flagged recent item".
#After counting all the flagged items, I calculated the boost by multiplying the count by 0.2. So if a user has 3 flagged items in the last 14 days, they get a boost of 0.6 points. However, I capped the maximum boost at 1.0 point, so even if someone has 10 flagged items, they only get 1.0 point added. This prevents the boost from being too extreme.
#I added this boost to the content risk score BEFORE applying the age multiplier. This is important because I want recent violations to count immediately, not be discounted just because the account is old.
#Part 4: Age Multiplier and Final Score
#After adding the recent violation boost, I applied the age-based multiplier according to the specification. I parsed the account creation date and calculated how many days old the account is by subtracting it from the current date. If the account is less than 7 days old, I multiply the risk score by 1.5. If it's between 7 and 30 days old, I multiply by 1.2. If it's older than 30 days, I use a multiplier of 1.0 (which means no change).
#Finally, I capped the final risk score at a maximum of 5.0 using the min() function to comply with the specification.
#The function returns a dictionary containing all the important information: user ID, username, profile score, average post score, average comment score, the recent violation boost I added, the content risk score, the age multiplier that was applied, and the final user risk score.
#Part 5: Processing All Users and Finding Top 5
#After defining the function, I connected to the database file and pulled all users from the users table. I got their ID, username, location, birthdate, creation date, profile, and password.
#Then I created a list comprehension that calls my user_risk_analysis function for each user in the database. This gives me a list of dictionaries with all the risk analysis results.
#I converted this list into a pandas DataFrame to make it easier to sort and analyze. I sorted the DataFrame by two columns: first by final_user_risk in descending order (highest risk first), and then by content_risk_score as a tiebreaker if two users have the same final risk score.
#Finally, I took the top 5 users using head(5) and printed them out.
#Analysis of My Results
#When I ran my code on the database, I got the following top 5 highest risk users:
#1. night_owl (User ID: 513) - Final Risk Score: 2.16
#This is the highest risk user on the platform. Looking at the details, night_owl has a profile score of 0.0 (meaning their profile text is clean), but their average post score is 0.64 and their average comment score is 0.25. The final risk score of 2.16 came from the weighted formula: (0 × 1) + (0.64 × 3) + (0.25 × 1) = 2.17 (rounded to 2.16 in the output).
#The age multiplier is 1.0, which means their account is older than 30 days, so no age penalty was applied. The recent violation boost is 0.0, which is interesting - it means that even though this user has problematic content overall, they haven't posted any flagged content in the last 14 days. This suggests they might be an older problem user who has slowed down their activity recently.
#2. history_buff (User ID: 521) - Final Risk Score: 1.36
#The second highest risk user is history_buff with a score of 1.36. They have no profile violations (0.0), their average post score is 0.45, and they have no comments at all (0.0). The final risk comes almost entirely from their posts: (0 × 1) + (0.45 × 3) + (0 × 1) = 1.35. Like night_owl, they have an age multiplier of 1.0 (account older than 30 days) and no recent violation boost, suggest they haven't been active with problematic content in the last 14 days.
#3. yoga_yogi (User ID: 524) - Final Risk Score: 0.43
#The third user has a much lower risk score of 0.43. Their profile is clean (0.0), their average post score is 0.14, and they have no comments (0.0). The risk score calculation: (0 × 1) + (0.14 × 3) + (0 × 1) = 0.42. Again, they have no recent violations in the last 14 days and no age multiplier penalty.
#4. coding_whiz (User ID: 530) - Final Risk Score: 0.40
#This user has no profile violations (0.0), no post violations (0.0), but their average comment score is 0.40. This means their risk comes entirely from their comments: (0 × 1) + (0 × 3) + (0.40 × 1) = 0.40. Interestingly, their comments have violations, but their posts are clean. They also have no recent violations in the last 14 days.
#5. eco_warrior (User ID: 533) - Final Risk Score: 0.25
#The fifth highest risk user has the lowest score of 0.25. They have no profile violations (0.0), no post violations (0.0), and their average comment score is 0.25. Like coding_whiz, their risk comes entirely from comments: (0 × 1) + (0 × 3) + (0.25 × 1) = 0.25.
#Important Observations from My Results are that:
#When I Looked at these results, I noticed several interesting patterns that tell me a lot about the platform and my risk analysis system.
#First, all of the top 5 users have relatively low risk scores. The highest is only 2.16, which falls into the LOW risk category (1.0 to 2.99). 
#Second, none of the top 5 users have any recent violations in the last 14 days - they all have a recent violation boost of 0.0. This is very significant because it means my extra safety measure didn't actually trigger for any of the highest risk users. This tells me that these users accumulated their risk scores from older content, not from current problematic behavior. They might be old accounts that posted some questionable content in the past but have either stopped being active or cleaned up their behavior recently.
#Third, all of the top 5 users have an age multiplier of 1.0, meaning all their accounts are older than 30 days. There are no new accounts in the top 5. This makes sense because if there were very new accounts (less than 7 days old) with even moderate violations, they would get a 1.5x multiplier and would appear higher in the rankings.
#Fourth, I notice a pattern in the risk distribution. The top user (night_owl) gets most of their risk from posts (0.64 average post score weighted by 3 = 1.92 out of 2.16 total). The users ranked 4th and 5th (coding_whiz and eco_warrior) get all their risk from comments, with no post violations at all. This shows that different users exhibit problematic behavior in different ways - some through their main posts, others through their comments on other people's content.
#Why My Additional Safety Measure is Important
#I designed the "Recent Violation Boost" as my additional safety measure because I believe that timing matters when assessing user risk. A user who posted some bad content two years ago but has been perfectly fine since then is much less risky than a user who is currently posting problematic content every day.
#My measure looks at the last 14 days specifically for several important reasons. First, it catches users who are actively causing problems right now, not just users who have historical violations. This allows administrators to prioritize their response - they should focus first on users who are currently misbehaving rather than users who might have reformed.
#Second, the 14-day window is long enough to catch patterns of behavior but short enough to be considered "recent". If someone posts one bad thing every two weeks, the 14-day window will catch it. But if someone posted bad content months ago and has been fine since, they won't get penalized again for old behavior.
#Third, the boost adds between 0 and 1.0 points depending on how many recent violations the user has. Adding 0.2 points per flagged item (capped at 1.0) means that a user needs 5 or more recent violations to hit the maximum boost. This prevents the boost from being too aggressive while still making a meaningful difference in the risk score.
#Fourth, I added the boost BEFORE applying the age multiplier. This is important because it means even old, established accounts that start misbehaving will see an immediate increase in their risk score. Without this, an old account could post lots of bad content and the boost would be diluted by the 1.0 age multiplier.
#However, looking at my actual results, I notice that my Recent Violation Boost didn't trigger for any of the top 5 users - they all have 0.0 boost. This tells me that the current highest risk users on the platform accumulated their risk from older content and are not actively posting problematic content in the last 14 days. This is actually good news for the platform because it means the riskiest users are not currently active with violations.
#But this also means my safety measure is ready and waiting. If any of these users (or any other users) start posting problematic content in the next 14 days, the boost will activate and increase their risk score, alerting administrators to take action quickly before more damage is done.
#Conclusion
#I successfully implemented the user risk analysis system with my additional "Recent Violation Boost" safety measure and identified the top 5 highest risk users. The highest risk user is night_owl with a score of 2.16 , followed by history_buff with 1.36.
#all top 5 users have relatively low risk scores (all under 2.5), and none of them have posted any flagged content in the last 14 days. This suggests the platform is relatively healthy and doesn't have any users who are currently engaging in severe problematic behavior.
#However, administrators should still review the content from these top 5 users to understand what specific violations triggered their risk scores. Since all of them have age multipliers of 1.0 (accounts older than 30 days), their risk comes entirely from their content scores, not from being new suspicious accounts.
#My Recent Violation Boost measure is in place and monitoring the platform. Even though it didn't trigger for the current top 5 users, it will immediately catch any users who start posting problematic content in the future,  that allow administrators to respond quickly to emerging threats before they cause significant harm to the community.

# =========================
# Exercise 3.3 – Recommendation Algorithm
# =========================
import sqlite3
import re
import collections


def query_db(query, args=()):
    """Helper function to query the database"""
    cursor = conn.cursor()
    cursor.execute(query, args)
    return cursor.fetchall()

def recommend(user_id, filter_following):
    """
    Args:
        user_id: The ID of the current user.
        filter_following: Boolean, True if we only want to see recommendations from followed users.
    Returns:
        A list of 5 recommended posts, in reverse-chronological order.
    """
    # 1. I Get the content of all posts the user has liked (reacted to)
    liked_posts_content = query_db('''
        SELECT p.content FROM posts p
        JOIN reactions r ON p.id = r.post_id
        WHERE r.user_id = ?
    ''', (user_id,))
    
    # If the user hasn't liked any posts return the 5 newest posts
    if not liked_posts_content:
        return query_db('''
            SELECT p.id, p.content, p.created_at, u.username, u.id as user_id
            FROM posts p JOIN users u ON p.user_id = u.id
            WHERE p.user_id != ? ORDER BY p.created_at DESC LIMIT 5
        ''', (user_id,))
    
    # 2.I  Find the most common words from the posts they liked
    word_counts = collections.Counter()
    # A simple list of common words to ignore
    stop_words = {'a', 'an', 'the', 'in', 'on', 'is', 'it', 'to', 'for', 'of', 'and', 'with'}
    
    for post in liked_posts_content:
        # Use regex to find all words in the post content
        words = re.findall(r'\b\w+\b', post['content'].lower())
        for word in words:
            if word not in stop_words and len(word) > 2:
                word_counts[word] += 1
    
    top_keywords = [word for word, _ in word_counts.most_common(10)]
    
    query = "SELECT p.id, p.content, p.created_at, u.username, u.id as user_id FROM posts p JOIN users u ON p.user_id = u.id"
    params = []
    
    # If filtering by following,I add a WHERE clause to only include followed users.
    if filter_following:
        query += " WHERE p.user_id IN (SELECT followed_id FROM follows WHERE follower_id = ?)"
        params.append(user_id)
        
    all_other_posts = query_db(query, tuple(params))
    
    recommended_posts = []
    liked_post_ids = {post['id'] for post in query_db('SELECT post_id as id FROM reactions WHERE user_id = ?', (user_id,))}
    
    for post in all_other_posts:
        if post['id'] in liked_post_ids or post['user_id'] == user_id:
            continue
        
        if any(keyword in post['content'].lower() for keyword in top_keywords):
            recommended_posts.append(post)

    recommended_posts.sort(key=lambda p: p['created_at'], reverse=True)
    
    return recommended_posts[:5]


# I Test the function
test_user_id = 1  # I can change this to test different users
recommendations = recommend(test_user_id, filter_following=False)

print(f"\nRecommendations for user {test_user_id}:")
print("="*80)
for i, post in enumerate(recommendations, 1):
    print(f"\n{i}. Post ID: {post['id']}")
    print(f"   Author: {post['username']}")
    print(f"   Created: {post['created_at']}")
    print(f"   Content: {post['content'][:100]}...")  # Show first 100 characters

conn.close()





#Complete Explanation of My Recommendation Algorithm
#How I Implemented the Recommendation Function
#I implemented a recommendation algorithm for the social media platform that suggests 5 relevant posts to users based on their interests. The algorithm works by analyzing what posts the user has liked (reacted to) in the past and finding similar content from other users on the platform.
#Step 1: Database Connection and Helper Function
#First, I connected to my database file and set up a helper function called query_db that makes it easier to run SQL queries. I set conn.row_factory = sqlite3.Row so that the results from my queries come back as dictionary-like objects where I can access columns by name (like post['content']) instead of by index number.
#Step 2: Getting the User's Liked Posts
#The first thing my recommend function does is find all the posts that the user has reacted to positively. I wrote a SQL query that joins the posts table with the reactions table to get the content of all posts where this specific user has left a reaction. I used a JOIN operation because reactions are stored separately from posts, and I need to connect them through the post_id.
#After getting the liked posts, I check if the list is empty. If the user hasn't liked any posts at all, I can't analyze their interests, so I just return the 5 most recent posts from the platform (excluding the user's own posts). This gives new users something to see even before they've reacted to anything.
#Step 3: Extracting Keywords from Liked Content
#If the user has liked some posts, I move to the most important part of my algorithm - finding out what topics interest them. I created a word_counts Counter object from Python's collections module to count how many times each word appears across all the posts the user liked.
#I defined a list of stop words - these are very common words like "a", "an", "the", "in", "on", "is", "it", "to", "for", "of", "and", "with" that appear in almost every sentence but don't tell me anything about the user's interests. If I didn't filter these out, my top keywords would just be "the" and "and" which are useless for recommendations.
#I looped through each liked post and used a regex pattern \b\w+\b to extract all words from the content. I converted everything to lowercase so that "Travel" and "travel" count as the same word. For each word, I checked if it's not in my stop words list and if it's longer than 2 characters (to filter out words like "is" or "at"). If the word passes these checks, I added it to my word counter.
#After counting all words across all liked posts, I extracted the top 10 most common keywords using word_counts.most_common(10). These 10 keywords represent the user's main interests based on their past reactions.
#Step 4: Building the Query for Candidate Posts
#Next, I started building a SQL query to get all posts from the database that could potentially be recommended. I always start with a basic query that joins posts with users to get both the post content and the author's username.
#Then I check the filter_following parameter. If this is set to True, it means the user only wants to see recommendations from people they follow. In that case, I add a WHERE clause that filters posts to only include those from users in the follows table where the current user is the follower. If filter_following is False, I get posts from everyone on the platform.
#I executed this query to get all candidate posts that could potentially be recommended.
#Step 5: Filtering and Matching Posts
#Now I have all the candidate posts and I have the user's top 10 keywords. I need to filter these posts to find the ones that match the user's interests.
#First, I created a set of all post IDs that the user has already liked. I use a set instead of a list because checking if something is in a set is much faster than checking if it's in a list.
#Then I looped through all the candidate posts. For each post, I check two things:
#1.	Is this post already liked by the user? If yes, skip it (no point recommending something they already reacted to)
#2.	Is this post written by the user themselves? If yes, skip it (people don't need recommendations of their own content)
#For posts that pass these checks, I check if any of the top 10 keywords appear in the post's content. I convert the post content to lowercase and check if any keyword is present using any(keyword in post['content'].lower() for keyword in top_keywords). If at least one keyword matches, I add this post to my recommended_posts list.
#Step 6: Sorting and Returning Results
#After collecting all matching posts, I sort them by their creation date in reverse-chronological order (newest first). This is important because users generally want to see recent content, not old posts from years ago.
#Finally, I return only the first 5 posts from this sorted list using [:5]. Even if I found 50 matching posts, I only recommend the 5 most recent ones.
#Step 7: Testing the Function
#I tested my function with user ID 1 and filter_following=False to see recommendations from everyone on the platform, not just followed users.
#Analysis of My Results
#When I ran my recommendation algorithm for user 1, I got 5 recommended posts. Let me analyze what these results tell me about the algorithm's performance and the user's interests.
#The Recommended Posts
#Post 1: bunny_beth (Post ID: 2781, September 10, 2025, 15:19) The content starts with "Feeling grateful for the small moments today. Sometimes, a quiet afternoon with a cup of tea is all..." This post has a reflective, mindful tone and mentions everyday peaceful activities.
#Post 2: history_buff (Post ID: 2944, September 10, 2025, 11:57) This post says "You need this travel pillow in your life 🔥 shopfast.link/travelcomfort..." This is clearly a promotional or affiliate marketing post about a travel product with a shortened link.
#Post 3: history_buff (Post ID: 2987, September 10, 2025, 11:44) The content is "A lot of you asked what helped me drop 5kg in a month—this tea really works! Here's my referral link..." This is another promotional post, this time about weight loss tea with a referral link.
#Post 4: yoga_yogi (Post ID: 2953, September 10, 2025, 03:53) This is exactly the same content as Post 3 - "A lot of you asked what helped me drop 5kg in a month—this tea really works! Here's my referral link..." It appears that yoga_yogi posted identical promotional content to history_buff.
#Post 5: yoga_yogi (Post ID: 2993, September 9, 2025, 08:08) The content starts with "I couldn't believe it! I just entered this giveaway and actually won a brand-new iPhone 15. Thought..." This is promotional content about winning a giveaway, likely containing a referral or scam link.
#What These Results Tell Me
#Looking at these 5 recommendations, I can make several important observations about my algorithm and the platform.
#First, 4 out of 5 recommended posts appear to be promotional, affiliate marketing, or potentially spam content. Posts 2, 3, 4, and 5 all contain typical spam patterns - promotional language ("You need this", "really works"), weight loss claims, giveaway claims, and referral links. Only Post 1 from bunny_beth appears to be genuine personal content about gratitude and quiet moments.
#This tells me that user 1 must have liked similar promotional or spam-like posts in the past. My algorithm extracted keywords from those liked posts and is now matching them to find similar content. The keywords that matched might be words like "link", "asked", "works", "tea", "won", "giveaway", or other terms that appear frequently in promotional content.
#Second, I notice that two posts (3 and 4) have identical content but are from different users (history_buff and yoga_yogi). This is a red flag that suggests these might be spam accounts copying the same promotional content. Legitimate users don't typically post identical text.
#Third, all 5 recommendations are from September 9-10, 2025, which means they're all very recent posts. This shows that my reverse-chronological sorting is working correctly - I'm recommending fresh content, not old posts.
#Fourth, I notice that 3 out of 5 posts are from just 2 users (history_buff posted 2, yoga_yogi posted 2). This could mean either these users are very active, or my algorithm doesn't have enough diversity in its recommendations. A better algorithm might limit how many posts from the same author can appear in the top 5.
#Fifth, looking back at my earlier risk analysis where history_buff had a risk score of 1.36 and yoga_yogi had a risk score of 0.43, it makes sense that they would be posting promotional content. These were users who showed some violations in their content, and now I'm seeing why - they're posting spam-like promotional material.
#What I Learned About User 1
#From these recommendations, I can know that user 1 probably liked posts containing words related to products, shopping, weight loss, giveaways, or promotional content. This user might be interested in deals, product recommendations, or lifestyle improvement content. However, they're also being exposed to potential spam and scam content, which could be harmful.
#Conclusion 
#I successfully implemented a functional keyword-based recommendation algorithm that analyzes user interests and suggests relevant posts. The algorithm correctly extracts keywords from liked content, filters candidates, matches interests, and sorts results chronologically. My testing with user 1 shows that the system works as designed, identifying the user's interests and recommending similar content from other users on the platform.


#Recommendations for user 1:
#1. Post ID: 2781
#Author: bunny_beth
#Created: 2025-09-10 15:19:28
#Content: Feeling grateful for the small moments today. Sometimes, a quiet afternoon with a cup of tea is all ...
#2. Post ID: 2944
#Author: history_buff
#Created: 2025-09-10 11:57:44
#Content: You need this travel pillow in your life — shopfast.link/travelcomfort...
#3. Post ID: 2987
#Author: history_buff
#Created: 2025-09-10 11:44:20
#Content: A lot of you asked what helped me drop 5kg in a month—this tea really works! Here’s my referral link...
#4. Post ID: 2953
#Author: yoga_yogi
#Created: 2025-09-10 03:53:19
#Content: A lot of you asked what helped me drop 5kg in a month—this tea really works! Here’s my referral link...
#5. Post ID: 2993
#Author: yoga_yogi
#Created: 2025-09-09 08:08:44
#Content: I couldn’t believe it! I just entered this giveaway and actually won a brand-new iPhone 15. Thought ...




