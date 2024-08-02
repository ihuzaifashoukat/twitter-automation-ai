import asyncio
import time
import random
import re  # For regular expression-based keyword matching

from twscrape import API, gather 
from twitter.account import Account
from openai import AsyncOpenAI

# --- Configurations ---
openai_api_key = "apikey"  
twitter_cookie_data = '{"ct0": "cto", "auth_token": "authtoken"}'
target_keywords = ["Linkedin", "Content", "Marketing", "Copywriting", "Ghostwriting"]
response_interval = 300  # Base interval (5 minutes)
max_tweets_per_keyword = 15  # Fetch more tweets to prioritize top accounts
replied_tweet_ids = set()

# --- Initialize Clients ---
client = AsyncOpenAI(api_key=openai_api_key)
twitter_client = Account(cookies={"ct0": "cto", "auth_token": "authtoken"})  # Pass cookie data directly
twscrape_api = API()

# --- OpenAI Reply Generation ---
async def get_openai_reply(tweet_text):
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": f"Given this tweet:\n\n{tweet_text}\n\nWrite an insightful and engaging reply. keep it simple:"}],
        max_tokens=100,
    )
    return response.choices[0].message.content.strip()

# --- Tweet Filtering and Sorting (Improved) ---
def filter_and_sort_tweets(tweets, keyword):
    filtered_tweets = []
    for tweet in tweets:
        if tweet.id in replied_tweet_ids:
            continue

        text = tweet.rawContent.lower()

        # Regular expression for whole-word keyword matching (case-insensitive)
        if re.search(rf"\b{keyword.lower()}\b", text):  
            filtered_tweets.append(tweet)

    # Sort by engagement (could be refined further)
    return sorted(filtered_tweets, key=lambda t: t.likeCount + t.retweetCount + t.replyCount, reverse=True)

# --- Tweet Retrieval, Filtering, and Response ---
async def main():
    await twscrape_api.pool.add_account("cookie_user", "", "", "", cookies=twitter_cookie_data)

    while True:
        try:
            for keyword in target_keywords:
                tweets = await gather(twscrape_api.search(keyword, limit=max_tweets_per_keyword))
                filtered_tweets = filter_and_sort_tweets(tweets, keyword) 

                for tweet in filtered_tweets[:3]:  # Reply to top 3 engaging tweets for each keyword
                    reply_text = await get_openai_reply(tweet.rawContent)
                    twitter_client.reply(reply_text, tweet.id)
                    replied_tweet_ids.add(tweet.id)

                    print(f"Replied to tweet (keyword '{keyword}'): https://twitter.com/{tweet.user.username}/status/{tweet.id}")

                    delay = random.randint(60, 180)
                    await asyncio.sleep(delay)

        except Exception as e:
            print(f"Error: {e}")  
            if "Rate limit exceeded" in str(e):  
                await asyncio.sleep(900)  # Wait 15 minutes for rate limits 
            else:
                await asyncio.sleep(response_interval) 



if __name__ == "__main__":
    asyncio.run(main())
