import praw
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config.reddit_config as reddit_config
reddit = praw.Reddit(client_id=reddit_config.CLIENT_ID,
                     client_secret=reddit_config.CLIENT_SECRET,
                     user_agent=reddit_config.USER_AGENT,
                     username=reddit_config.REDDIT_USERNAME,
                     password=reddit_config.REDDIT_PASSWORD)

subreddit = reddit.subreddit('UIUC')
cnt = 0

for post in subreddit.hot(limit=None):
    cnt += 1
    # print(post.title)

print(f"Get {cnt} posts")