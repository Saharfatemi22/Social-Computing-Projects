# Project 3 – Moderation, Risk Analysis, and Recommendation Systems

This project is part of the **Social Computing** course at the **University of Oulu**.

The goal of this project is to design and implement core platform safety and personalization mechanisms, including automated content moderation, user risk scoring, and a simple recommendation algorithm, using **Python**, **SQL**, and an SQLite database.

---

## Tasks

### 3.1 – Censorship

Implement an automated content moderation function that detects and censors inappropriate content in posts, comments, and user profile introductions.

The moderation system:
- Detects severe violations and removes content immediately
- Censors mild violations and assigns a severity score
- Produces a final risk score based on the number and weight of violations

An additional moderation measure was implemented to improve platform safety and protect user privacy.

---

### 3.2 – User Risk Analysis

Implement a user risk analysis function that assigns a risk score to each user based on their behavior and content history.

The risk score is computed using:
- Moderation score of the user profile
- Average moderation score of posts
- Average moderation score of comments
- Account age–based multipliers

An additional safety measure was implemented to detect **recent violations**, increasing the risk score for users who have posted problematic content in the last 14 days.

The top five highest-risk users on the platform are identified and analyzed.

---

### 3.3 – Recommendation Algorithm

Implement a simple recommendation function that suggests five relevant posts for a user on the “Recommended” tab.

The recommendation logic is based on:
- Posts the user has reacted to positively
- Keyword extraction from previously liked content
- Optional filtering to recommend posts only from followed users
- Reverse chronological ordering to prioritize recent posts

---

## Files

- `project3_analysis.py` – Python code for Tasks 3.1–3.3  
- `database.sqlite` – SQLite database used for moderation, risk analysis, and recommendations
