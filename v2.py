import asyncio
import time
import random
import re

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from twitter.account import Account
import os
from openai import AsyncOpenAI

# --- Configurations ---
openai_api_key = "apikey"  
twitter_cookie_data = {
    "ct0": "Autho", 
    "auth_token": "auth_token"
}
target_keywords = [   
    "Content Creation", 
    "Startup", 
    "Enterprenuer",
    "Automation"
    ]
response_interval = 300  # Base interval (5 minutes)
max_tweets_per_keyword = 15  # Fetch more tweets to prioritize top accounts
replied_tweet_ids = set()

# --- Initialize Clients ---
client = AsyncOpenAI(api_key=openai_api_key)
twitter_client = Account(cookies=twitter_cookie_data) 

# --- Initialize Selenium with Cookie Authentication ---
def initialize_driver_with_cookies(cookie_data):
    # Configure Chrome Options
    options = Options()
    # options.add_argument("--headless")  # Run Chrome in headless mode
    options.add_argument("--window-size=1920,1080")

    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage") 


    # Initialize the WebDriver
    driver = webdriver.Chrome(options=options)
    
    driver.get("https://x.com/")  # Navigate to Twitter to set cookies

    for key, value in cookie_data.items():
        driver.add_cookie({"name": key, "value": value, "domain": "x.com"})  # Use "x.com" as the domain

    return driver

driver = initialize_driver_with_cookies(twitter_cookie_data)

# --- OpenAI Reply Generation ---
async def get_openai_reply(tweet_text):
    def sync_completion():
        return client.chat.completions.create(
            model="gpt-4o", 
            messages=[{"role": "user", "content": f"Given this tweet:\n\n{tweet_text}\n\nWrite an insightful and engaging reply. Keep it simple:"}],
            max_tokens=100,
        )
    
    response = await asyncio.to_thread(sync_completion)
    return response.choices[0].message.content.strip()

# --- Tweet Scraping with Selenium ---
async def scrape_tweets(keyword):
    url = f"https://x.com/search?q={keyword}&src=spelling_expansion_revert_click"
    
    # Introduce a delay before navigating to the search URL
    print(f"Waiting 5 minutes before searching for '{keyword}'...")
    await asyncio.sleep(300)  # Wait for 5 minutes

    driver.get(url)

    # Wait for tweets to load (adjust as needed)
    await asyncio.sleep(5)  

    tweets = []
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        try:
            # Extract tweet elements (adjust the selector if Twitter's HTML changes)
            tweet_elements = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, '[data-testid="tweetText"]'))
            )
            
            for element in tweet_elements:
                # Extract tweet ID from the link element
                link_element = element.find_element(By.XPATH, "./ancestor::article//a[contains(@href, '/status/')]")
                tweet_id = link_element.get_attribute("href").split('/')[-1]  
                tweet_text = element.text
                if tweet_id not in replied_tweet_ids and re.search(rf"\b{keyword.lower()}\b", tweet_text.lower()):
                    tweets.append({"id": tweet_id, "text": tweet_text})

            # Scroll down to load more tweets
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # Introduce a variable delay to mimic human-like scrolling behavior
            scroll_delay = random.uniform(1.5, 3.5)  # Delay between 1.5 and 3.5 seconds
            await asyncio.sleep(scroll_delay)

            # Calculate new scroll height and compare with last scroll height
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break  # No more tweets to load
            last_height = new_height

        except Exception as e:
            print(f"Error during scraping: {e}")
            break

    # Sort by engagement metrics (likes, retweets, replies) - Placeholder logic
    # You'll need to implement actual extraction of these metrics using Selenium
    tweets.sort(key=lambda t: t.get('likes', 0) + t.get('retweets', 0) + t.get('replies', 0), reverse=True)  
    return tweets

# --- Tweet Retrieval, Filtering, and Response ---
async def main():
    while True:
        try:
            for keyword in target_keywords:
                scraped_tweets = await scrape_tweets(keyword)

                for tweet in scraped_tweets[:3]:  # Reply to top 3 engaging tweets
                    reply_text = await get_openai_reply(tweet["text"])
                    twitter_client.reply(reply_text, tweet["id"])
                    replied_tweet_ids.add(tweet["id"])

                    print(f"Replied to tweet (keyword '{keyword}'): https://x.com/i/web/status/{tweet['id']}")

                    # Introduce a variable delay between replies
                    reply_delay = random.randint(60, 180)  # Delay between 60 and 180 seconds
                    await asyncio.sleep(reply_delay)

        except Exception as e:
            print(f"Error: {e}") 
            if "Rate limit exceeded" in str(e):
                await asyncio.sleep(900)  # Wait 15 minutes for rate limits
            else:
                await asyncio.sleep(response_interval)

if __name__ == "__main__":
    asyncio.run(main())