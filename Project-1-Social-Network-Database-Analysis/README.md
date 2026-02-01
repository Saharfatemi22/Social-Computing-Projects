# Project 1 – Social Network Database Analysis

This project is part of the **Social Computing** course at the **University of Oulu**.

The goal of this project is to analyze a social network database using **SQL** and **Python** and to answer analytical questions related to user behavior and interactions.

---

## Questions

### 1.1 – Database Exploration
Load the database and inspect all available tables. For each table, describe the columns, their purpose, data types, and provide examples of the contents.

### 1.2 – Lurkers
Identify users who have not posted any content and have not interacted with posts through comments or reactions, but may have followed other users. Explain how the number of lurkers is calculated.

### 1.3 – Influencers
Identify the five users with the highest engagement on the platform. Describe how engagement is defined and measured, and explain how the results are obtained.

### 1.4 – Spammers
Identify users who have shared the same text in posts or comments at least three times over their entire activity history. Explain the criteria and method used to detect spammers.

---

## Approach

The analysis is performed using **Python** with the **SQLite** and **Pandas** libraries.  
SQL queries are used to explore the database, filter users based on activity, calculate engagement metrics, and detect repeated content.

---

## Files

- `project1_analysis.py` – Python script containing all queries and analysis  
- `database.sqlite` – SQLite database used for this project
