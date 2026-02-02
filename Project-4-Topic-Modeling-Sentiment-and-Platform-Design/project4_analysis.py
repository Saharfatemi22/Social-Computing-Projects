# =========================
# 4.1 – Topic Modeling (LDA)
# =========================

!pip -q install "gensim>=4.4.0" nltk

import re
import pandas as pd
import numpy as np
from pathlib import Path

import nltk
nltk.download("punkt")
nltk.download("punkt_tab")
nltk.download("stopwords")
nltk.download("wordnet")

from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize

from gensim.corpora import Dictionary
from gensim.models.ldamodel import LdaModel
from gensim.models.coherencemodel import CoherenceModel

CANDIDATE_PATHS = [
    Path("posts.csv"),
    Path("/content/posts.csv"),
    Path("/mnt/data/posts.csv"),  
]
for p in CANDIDATE_PATHS:
    if p.exists():
        POSTS_PATH = p
        break
else:
    raise FileNotFoundError("posts.csv not found. Upload it to Colab workspace or set the correct path.")

posts = pd.read_csv(POSTS_PATH)

#  Basic text cleaning 
URL_RE = re.compile(r"https?://\S+|www\.\S+")
HTML_RE = re.compile(r"<.*?>")
USER_RE = re.compile(r"@\w+")
HASH_RE = re.compile(r"#\w+")
NON_ALPHA_RE = re.compile(r"[^a-z]+")

stop_words = set(stopwords.words("english"))
stop_words.update([
    "would","best","always","amazing","bought","quick","people","new","fun","think","know","believe",
    "many","thing","need","small","even","make","love","mean","fact","question","time","reason","also",
    "could","true","well","life","said","year","going","good","really","much","want","back","look",
    "article","host","university","reply","thanks","mail","post","please",
    "like","one","get","got","u","us","im","amp"  # common fillers
])

lemmatizer = WordNetLemmatizer()

def normalize_text(text: str) -> str:
    text = str(text)
    text = text.lower()
    text = URL_RE.sub(" ", text)
    text = HTML_RE.sub(" ", text)
    text = USER_RE.sub(" ", text)
    text = HASH_RE.sub(" ", text)
    return text

def tokenize_lemmatize(text: str):
    text = normalize_text(text)
    tokens = word_tokenize(text)
    # it keeps alphabetic tokens only
    tokens = [NON_ALPHA_RE.sub("", t) for t in tokens]
    tokens = [t for t in tokens if t.isalpha()]
    # lemmatize
    tokens = [lemmatizer.lemmatize(t) for t in tokens]
    # remove short tokens and stopwords
    tokens = [t for t in tokens if len(t) >= 3 and t not in stop_words]
    return tokens

# 3) Build tokenized corpus (skip empty rows)
texts = []
row_index = []
for i, row in posts.iterrows():
    toks = tokenize_lemmatize(row.get("content", ""))
    if toks:
        texts.append(toks)
        row_index.append(i)

if len(texts) == 0:
    raise ValueError("After preprocessing, no tokens left. Loosen filters or inspect data.")

# 4) Dictionary + BoW corpus
dictionary = Dictionary(texts)
# Filter rare and overly common tokens (tune as needed)
dictionary.filter_extremes(no_below=5, no_above=0.4)  # appears in >=5 docs, in <=40% of docs
corpus = [dictionary.doc2bow(t) for t in texts]

# ensure vocab/corpus not empty
if dictionary.num_nnz == 0 or all(len(bow) == 0 for bow in corpus):
    raise ValueError("Filtered dictionary/corpus is empty. Relax filter_extremes or preprocessing.")

# 5) Train LDA with exactly 10 topics (alpha/eta learned from data for stability)
NUM_TOPICS = 10
lda = LdaModel(
    corpus=corpus,
    id2word=dictionary,
    num_topics=NUM_TOPICS,
    random_state=42,
    chunksize=2000,
    passes=10,
    iterations=200,
    alpha="auto",
    eta="auto",
    eval_every=None
)

coh_model = CoherenceModel(model=lda, texts=texts, dictionary=dictionary, coherence="c_v")
coherence_cv = coh_model.get_coherence()

print(f"Trained LDA with {NUM_TOPICS} topics. Coherence (c_v): {coherence_cv:.3f}\n")

# 6) Show top words per topic
TOPN_WORDS = 10
topic_terms = lda.show_topics(num_topics=NUM_TOPICS, num_words=TOPN_WORDS, formatted=False)
print("Top words per topic:")
for tid, words in topic_terms:
    word_list = ", ".join([w for (w, prob) in words])
    print(f"Topic {tid:02d}: {word_list}")

# 7) Assign a dominant topic to each post and measure "popularity"
def dominant_topic_for_bow(bow):
    dist = lda.get_document_topics(bow, minimum_probability=0.0)
    # dist: list[(topic_id, prob)]
    if not dist:
        return None, 0.0
    tid, prob = max(dist, key=lambda x: x[1])
    return tid, prob

dominants = [dominant_topic_for_bow(bow) for bow in corpus]
dom_ids = [d[0] for d in dominants]
dom_probs = [d[1] for d in dominants]

summary_df = pd.DataFrame({
    "row_id": row_index,
    "dominant_topic": dom_ids,
    "dominant_prob": dom_probs,
})

# Aggregate popularity = how many posts (and share) are dominated by each topic
popularity = summary_df.groupby("dominant_topic").size().rename("posts").reset_index()
popularity["share"] = popularity["posts"] / popularity["posts"].sum()
popularity = popularity.sort_values("posts", ascending=False).reset_index(drop=True)

# Attach top words preview for each topic to the popularity table
topic_labels = {
    tid: ", ".join([w for (w, p) in words])
    for tid, words in topic_terms
}
popularity["top_words"] = popularity["dominant_topic"].map(topic_labels)

print("\n=== 10 Most Popular Topics (by dominant-post count) ===")
print(popularity.to_string(index=False))

popular_topics_table = popularity[["dominant_topic", "posts", "share", "top_words"]]
popular_topics_table



#My explanation:
#I prepared the text. I lowercased the post content, removed links, HTML, @mentions and hashtags, tokenized, lemmatized words (so “walking” → “walk”), removed short tokens, and filtered standard + custom stopwords.
#I built a dictionary and bag-of-words corpus, then removed very rare terms (appearing in fewer than 5 posts) and very common terms (in more than 40% of posts).
#I trained an LDA model with 10 topics in gensim, using alpha='auto' and eta='auto' for stability, 10 passes and 200 iterations.
#I computed coherence c_v to sanity-check quality and then, for each post, I took the dominant topic (the one with the highest probability) and counted how many posts each topic “owns”. That is my definition of “most popular.”
#Model quality
#The coherence score is 0.397. For short, casual social posts, this is reasonable. It tells me the topics are somewhat consistent but still noisy—which makes sense given many posts include generic words like “today.”
#Top words and my short labels
#Below are the 10 topics ordered by popularity (post count and share), with my quick human label based on the top words the model showed.
#Topic 8 — 183 posts (14.09%): day, feel, anyone, book, every, else, another, world, finished
#Label: daily thoughts and reading
#Topic 9 — 159 posts (12.24%): health, mental, today, session, feeling, break, grateful
#Label: mental health and wellbeing
#Topic 3 — 148 posts (11.39%): today, tried, recipe, attended, change, local, inspiring
#Label: trying recipes and local events
#Topic 2 — 135 posts (10.39%): today, perfect, incredible, day, finally, saw, art, nature, fresh, made
#Label: outings, art, nature
#Topic 0 — 132 posts (10.16%): today, first, feeling, tried, parenting, friend, coffee, little, finally
#Label: everyday life, parenting, coffee
#Topic 5 — 123 posts (9.47%): night, last, kid, see, hard, today, caught, latest, damn, friend
#Label: late-night life, kids, tough days
#Topic 4 — 123 posts (9.47%): wait, friend, trip, spent, weekend, meme, little, tech, day, moment
#Label: trips, weekends, memes, tech
#Topic 1 — 110 posts (8.47%): spent, finally, change, finished, afternoon, nature, documentary, project, climate
#Label: climate/nature documentaries and projects
#Topic 6 — 99 posts (7.62%): kindness, reflecting, volunteering, simple, local, exploring, shelter, importance
#Label: volunteering and kindness
#Topic 7 — 87 posts (6.70%): today, everyone, keep, garden, community, beautiful, visited, better, local
#Label: community and gardening
#How I calculated “most popular”
#For each post, I asked the model for its topic distribution and picked the topic with the highest probability as the post’s dominant topic. Then I counted how many posts fell under each dominant topic. I also calculated each topic’s share by dividing its post count by the total number of modeled posts. That produced the ranking above.
#Notes 
#The word “today” appears in several top-word lists. If I remove “today” as a custom stopword and re-run, topics will likely sharpen.
#If I add bigrams (e.g., “mental_health”, “climate_change”), coherence may improve and labels become clearer.
#To validate, I would sample a few posts with the highest probability for each topic and check if the label matches the content.
#This satisfies Exercise 4.1: I identified 10 topics with gensim LDA and reported which ones are most popular by number of posts, including brief explanations of what each topic is about.

# =========================
# 4.2 – Sentiment Analysis (VADER)
# =========================

#  Setup part
!pip -q install "gensim>=4.4.0" nltk

import re
import pandas as pd
import numpy as np
from pathlib import Path

import nltk
nltk.download("punkt")
nltk.download("punkt_tab")   # needed by newest NLTK tokenizers
nltk.download("stopwords")
nltk.download("wordnet")
nltk.download("vader_lexicon")

from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from nltk.sentiment import SentimentIntensityAnalyzer

from gensim.corpora import Dictionary
from gensim.models.ldamodel import LdaModel

# 1) Load data
def find_path(fname):
    for p in [Path(fname), Path("/content")/fname, Path("/mnt/data")/fname]:
        if p.exists():
            return p
    raise FileNotFoundError(f"{fname} not found. Upload it to Colab or set path.")

posts_path = find_path("posts.csv")
comments_path = find_path("comments.csv")

posts = pd.read_csv(posts_path)
comments = pd.read_csv(comments_path)

# 2) Text cleaning & tokenization
URL_RE = re.compile(r"https?://\S+|www\.\S+")
HTML_RE = re.compile(r"<.*?>")
USER_RE = re.compile(r"@\w+")
HASH_RE = re.compile(r"#\w+")
NON_ALPHA_RE = re.compile(r"[^a-z]+")

stop_words = set(stopwords.words("english"))
stop_words.update([
    # tutorial extras + a few fillers common in short posts
    "would","best","always","amazing","bought","quick","people","new","fun","think","know","believe",
    "many","thing","need","small","even","make","love","mean","fact","question","time","reason","also",
    "could","true","well","life","said","year","going","good","really","much","want","back","look",
    "article","host","university","reply","thanks","mail","post","please",
    "like","one","get","got","u","us","im","amp","today"  # drop "today" to reduce topic bleed
])

lemmatizer = WordNetLemmatizer()

def normalize_text(text: str) -> str:
    text = str(text).lower()
    text = URL_RE.sub(" ", text)
    text = HTML_RE.sub(" ", text)
    text = USER_RE.sub(" ", text)
    text = HASH_RE.sub(" ", text)
    return text

def tokenize_lemmatize(text: str):
    text = normalize_text(text)
    tokens = word_tokenize(text)
    tokens = [NON_ALPHA_RE.sub("", t) for t in tokens]
    tokens = [t for t in tokens if t.isalpha()]
    tokens = [lemmatizer.lemmatize(t) for t in tokens]
    tokens = [t for t in tokens if len(t) >= 3 and t not in stop_words]
    return tokens

# 3) VADER sentiment on posts and comments
sia = SentimentIntensityAnalyzer()

def vader_compound(s: str) -> float:
    return sia.polarity_scores(str(s))["compound"]

posts["post_text"] = posts["content"].fillna("").astype(str)
comments["comment_text"] = comments["content"].fillna("").astype(str)

posts["sent_compound"] = posts["post_text"].apply(vader_compound)
comments["sent_compound"] = comments["comment_text"].apply(vader_compound)

# Label per VADER thresholds
def label_from_compound(c):
    if c >= 0.05: return "positive"
    if c <= -0.05: return "negative"
    return "neutral"

posts["sent_label"] = posts["sent_compound"].apply(label_from_compound)
comments["sent_label"] = comments["sent_compound"].apply(label_from_compound)

# 4) Overall tone (posts, comments, combined)
def sentiment_summary(df, value_col="sent_compound", label_col="sent_label"):
    out = {}
    out["n"] = len(df)
    out["mean"] = df[value_col].mean()
    out["median"] = df[value_col].median()
    counts = df[label_col].value_counts(dropna=False)
    total = counts.sum() if counts.sum() else 1
    for k in ["positive","neutral","negative"]:
        out[f"pct_{k}"] = float(counts.get(k, 0)) / total
    return out

overall_posts = sentiment_summary(posts)
overall_comments = sentiment_summary(comments)
combined = pd.concat([
    posts[["sent_compound","sent_label"]],
    comments[["sent_compound","sent_label"]]
], ignore_index=True)
overall_combined = sentiment_summary(combined)

print("=== Overall Tone ===")
print("Posts:", overall_posts)
print("Comments:", overall_comments)
print("Combined:", overall_combined)

# 5) Topics on posts (re-derive 10 topics like Ex. 3/4.1)
#   I  Build tokenized corpus for posts only, then LDA -> dominant topic.
tokenized_posts = []
keep_index = []
for i, row in posts.iterrows():
    toks = tokenize_lemmatize(row["post_text"])
    if toks:
        tokenized_posts.append(toks)
        keep_index.append(i)

if len(tokenized_posts) == 0:
    raise ValueError("No tokens left for posts after preprocessing. Loosen filters.")

from gensim.corpora import Dictionary
dictionary = Dictionary(tokenized_posts)
dictionary.filter_extremes(no_below=5, no_above=0.4)
corpus = [dictionary.doc2bow(t) for t in tokenized_posts]

if dictionary.num_nnz == 0 or all(len(bow)==0 for bow in corpus):
    raise ValueError("Dictionary/corpus empty after filtering. Adjust no_below/no_above.")

NUM_TOPICS = 10
lda = LdaModel(
    corpus=corpus,
    id2word=dictionary,
    num_topics=NUM_TOPICS,
    random_state=42,
    chunksize=2000,
    passes=10,
    iterations=200,
    alpha="auto",
    eta="auto",
    eval_every=None
)

def dominant_topic(bow):
    dist = lda.get_document_topics(bow, minimum_probability=0.0)
    if not dist: return None, 0.0
    tid, prob = max(dist, key=lambda x: x[1])
    return tid, prob

dom = [dominant_topic(bow) for bow in corpus]
dom_ids = [d[0] for d in dom]
dom_probs = [d[1] for d in dom]

topic_map = pd.DataFrame({
    "row_ix": keep_index,
    "topic_id": dom_ids,
    "topic_conf": dom_probs
})

# Attach topic to posts
posts_with_topic = posts.copy()
posts_with_topic["topic_id"] = np.nan
posts_with_topic.loc[topic_map["row_ix"], "topic_id"] = topic_map["topic_id"].values
posts_with_topic.loc[topic_map["row_ix"], "topic_conf"] = topic_map["topic_conf"].values
posts_with_topic["topic_id"] = posts_with_topic["topic_id"].astype("Int64")

# 6) Sentiment variation across topics (for posts)
topic_sent_posts = (
    posts_with_topic.dropna(subset=["topic_id"])
    .groupby("topic_id")["sent_compound"]
    .agg(["count","mean","median"])
    .reset_index()
    .sort_values("mean", ascending=False)
)

topic_words = {
    tid: ", ".join([w for (w, p) in words])
    for tid, words in lda.show_topics(num_topics=NUM_TOPICS, num_words=8, formatted=False)
}
topic_sent_posts["top_words"] = topic_sent_posts["topic_id"].map(topic_words)

print("\n=== Sentiment by Topic (Posts) ===")
print(topic_sent_posts.to_string(index=False))

# 7) Comment sentiment by the topic of their parent post (join on post_id)
#    (comments.csv has post_id; posts.csv has id)
comments_join = comments.merge(
    posts_with_topic[["id","topic_id"]],
    left_on="post_id", right_on="id", how="left"
)
topic_sent_comments = (
    comments_join.dropna(subset=["topic_id"])
    .groupby("topic_id")["sent_compound"]
    .agg(["count","mean","median"])
    .reset_index()
    .sort_values("mean", ascending=False)
)
topic_sent_comments["top_words"] = topic_sent_posts.set_index("topic_id")["top_words"].to_dict()
print("\n=== Sentiment by Topic (Comments, topic from parent post) ===")
print(topic_sent_comments.to_string(index=False))

def pct_fmt(x): return f"{100*x:.1f}%"
print("\n=== Compact Takeaways ===")
print(f"Overall posts mean compound: {overall_posts['mean']:.3f} "
      f"(pos {pct_fmt(overall_posts['pct_positive'])}, "
      f"neu {pct_fmt(overall_posts['pct_neutral'])}, "
      f"neg {pct_fmt(overall_posts['pct_negative'])})")
print(f"Overall comments mean compound: {overall_comments['mean']:.3f} "
      f"(pos {pct_fmt(overall_comments['pct_positive'])}, "
      f"neu {pct_fmt(overall_comments['pct_neutral'])}, "
      f"neg {pct_fmt(overall_comments['pct_negative'])})")

topic_sent_posts.to_csv("sentiment_by_topic_posts.csv", index=False)
topic_sent_comments.to_csv("sentiment_by_topic_comments.csv", index=False)




#my explanation of what I did and what the results mean.
#What I measured
#I used VADER to score sentiment for every post and every comment. For each item, VADER returns a compound score between −1 (very negative) and +1 (very positive). I also labeled each item as positive (≥ 0.05), neutral (between −0.05 and 0.05), or negative (≤ −0.05). Then I re-used the 10-topic LDA mapping from Exercise 4.1 to see how sentiment changes by topic. For comments, I grouped them by the topic of their parent post.
#Overall tone of the platform
#Across the entire platform (posts + comments), the average compound score is 0.409, with 74.6% positive, 7.5% neutral, and 17.9% negative. This tells me the general tone is clearly positive.
#Comparing posts vs comments
#Posts: mean 0.305, median 0.440. About 65.8% of posts are positive, 14.7% neutral, and 19.6% negative.
#Comments: mean 0.432, median 0.598. About 76.6% of comments are positive, only 5.8% neutral, and 17.6% negative.
#So comments are noticeably more positive than posts. I read this as users reacting more supportively or appreciatively in replies, while original posts include more mixed or reflective content.
#How sentiment varies by topic (posts)
#I ranked topics by their mean compound score on posts:
#Most positive post topics:
#Topic 6 (feeling, kid, day, coffee, grateful, friend): mean 0.464. Everyday life and gratitude come through as upbeat.
#Topic 4 (book, health, mental, kindness, reflecting): mean 0.429. Self-care, kindness, and reading lean positive.
#Topic 0 (nature, spent, morning, garden, weekend): mean 0.384. Nature and weekend activities are also positive.
#Topic 1 (project, finally, latest, diy, finished): mean 0.364. Finishing projects and DIY is positive, but a bit less than the top two.
#Least positive post topics:
#Topic 7 (else, feel, anyone, parenting, hard): mean 0.108. This looks like asking for help or talking about hard days.
#Topic 2 (meme, attended, favorite, mental health, tried): mean 0.188. Mixed playful content and mental health may balance out.
#Topic 5 (finished, session, night, gaming, film): mean 0.233. Entertainment is positive but more neutral overall.
#Topic 8 and Topic 3 sit in the middle around 0.256–0.256, including local/giveaways and climate/change/documentary themes.
#How sentiment varies by topic (comments)
#When I look at comments grouped by their parent post’s topic, the pattern is similar but shifted more positive:
#Most positive comment topics:
#Topic 0 (nature/weekend): mean 0.497.
#Topic 1 (projects/DIY): mean 0.492.
#Topic 6 (everyday life/gratitude): mean 0.492.
#Least positive comment topics:
#Topic 7 (parenting/hard days): mean 0.327.
#Topic 2 (memes/favorites/mental health): mean 0.347.
#Topic 3 (climate/change/documentaries): mean 0.364.

#The platform’s overall tone is positive. Both posts and comments skew positive, and comments are even more positive than posts.
#Topics about daily gratitude, books/mental health/acts of kindness, nature, weekends, and finishing projects show the highest positivity.
#Topics about harder personal experiences (parenting, tough days), mixed meme/mental-health chats, and heavy societal themes (climate/change) show the lowest positivity, though comments still tend to be supportive.

