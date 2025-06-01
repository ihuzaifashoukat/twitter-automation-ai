import os
import sys
import time
import re
import random
from typing import List, Optional, Tuple
from datetime import datetime, timezone

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.action_chains import ActionChains


# Adjust import paths
try:
    from ..core.browser_manager import BrowserManager
    from ..core.config_loader import ConfigLoader
    from ..utils.logger import setup_logger
    from ..data_models import ScrapedTweet
    from ..utils.scroller import Scroller
    from ..utils.progress import Progress
except ImportError:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..')) # Add root src to path
    from src.core.browser_manager import BrowserManager
    from src.core.config_loader import ConfigLoader
    from src.utils.logger import setup_logger
    from src.data_models import ScrapedTweet
    from src.utils.scroller import Scroller
    from src.utils.progress import Progress


config = ConfigLoader()
logger = setup_logger(config)

class TweetScraper:
    def __init__(self, browser_manager: BrowserManager, account_id: Optional[str] = None):
        self.browser_manager = browser_manager
        self.driver = self.browser_manager.get_driver() # Ensure driver is initialized
        self.actions = ActionChains(self.driver)
        self.config_loader = browser_manager.config_loader # Reuse config loader
        self.scroller = Scroller(self.driver) # Initialize scroller
        self.account_id = account_id # For logging or account-specific actions

        # Scraper settings from global config
        self.scrape_settings = self.config_loader.get_twitter_automation_setting("scraper_config", {})
        self.default_max_tweets = self.config_loader.get_twitter_automation_setting("max_tweets_per_scrape", 50)
        self.scroll_delay_min = self.scrape_settings.get("scroll_delay_min_seconds", 1.5)
        self.scroll_delay_max = self.scrape_settings.get("scroll_delay_max_seconds", 3.5)
        self.no_new_tweets_scroll_limit = self.scrape_settings.get("no_new_tweets_scroll_limit", 5) # Stop after 5 scrolls with no new tweets

    def _parse_tweet_card(self, card_element: WebElement) -> Optional[ScrapedTweet]:
        """Parses a single tweet card WebElement into a ScrapedTweet model."""
        try:
            # Extract user name
            user_name_element = card_element.find_element(By.XPATH, './/div[@data-testid="User-Name"]//span[1]//span')
            user_name = user_name_element.text if user_name_element else None

            # Extract user handle
            user_handle_element = card_element.find_element(By.XPATH, './/div[@data-testid="User-Name"]//span[contains(text(), "@")]')
            user_handle = user_handle_element.text if user_handle_element else None
            
            # Extract tweet text
            tweet_text_parts = []
            text_elements = card_element.find_elements(By.XPATH, './/div[@data-testid="tweetText"]//span | .//div[@data-testid="tweetText"]//a')
            for el in text_elements:
                try:
                    tweet_text_parts.append(el.text)
                except StaleElementReferenceException: # Element might go stale during iteration
                    logger.warning("Stale element reference when extracting tweet text part.")
                    continue 
            text_content = "".join(tweet_text_parts).strip()
            if not text_content: # Skip if no text content, might be a poll or other non-text tweet
                return None

            # Extract tweet ID and URL from the timestamp link (most reliable)
            tweet_id = None
            tweet_url = None
            try:
                # Link containing '/status/' and a timestamp
                link_element = card_element.find_element(By.XPATH, './/a[contains(@href, "/status/") and .//time]')
                href = link_element.get_attribute("href")
                if href and "/status/" in href:
                    tweet_url = href
                    tweet_id = href.split("/status/")[-1].split("?")[0] # Get ID part
            except NoSuchElementException:
                logger.warning("Could not find tweet link/ID element for a card.")
                return None # Essential info missing

            # Extract timestamp
            created_at_dt = None
            try:
                time_element = card_element.find_element(By.XPATH, ".//time")
                datetime_str = time_element.get_attribute("datetime")
                if datetime_str:
                    created_at_dt = datetime.fromisoformat(datetime_str.replace("Z", "+00:00"))
            except NoSuchElementException:
                logger.debug(f"Timestamp not found for tweet ID {tweet_id}")


            # Extract engagement counts (handle cases where they might be empty or missing)
            def get_count(testid: str) -> int:
                try:
                    element = card_element.find_element(By.XPATH, f'.//button[@data-testid="{testid}"]//span[@data-testid="app-text-transition-container"]//span')
                    text = element.text.strip()
                    if not text: return 0
                    if 'K' in text: return int(float(text.replace('K', '')) * 1000)
                    if 'M' in text: return int(float(text.replace('M', '')) * 1000000)
                    return int(text)
                except (NoSuchElementException, ValueError):
                    return 0

            reply_count = get_count("reply")
            retweet_count = get_count("retweet")
            like_count = get_count("like")
            
            # Views (analytics) count - selector might differ
            view_count = 0
            try: # Example selector, adjust based on actual X.com structure
                view_element = card_element.find_element(By.XPATH, './/a[contains(@href, "/analytics")]//span[@data-testid="app-text-transition-container"]//span')
                text = view_element.text.strip()
                if text:
                    if 'K' in text: view_count = int(float(text.replace('K', '')) * 1000)
                    elif 'M' in text: view_count = int(float(text.replace('M', '')) * 1000000)
                    else: view_count = int(text)
            except (NoSuchElementException, ValueError):
                pass # Views might not always be present or selector changes

            # Tags
            tags = [tag.text for tag in card_element.find_elements(By.XPATH, './/a[contains(@href, "src=hashtag_click")]')]
            
            # Mentions
            mentions = [mention.text for mention in card_element.find_elements(By.XPATH, './/div[@data-testid="tweetText"]//a[contains(text(), "@")]')]

            # Profile image URL
            profile_image_url = None
            try:
                img_element = card_element.find_element(By.XPATH, './/div[@data-testid="Tweet-User-Avatar"]//img')
                profile_image_url = img_element.get_attribute("src")
            except NoSuchElementException:
                pass
            
            # Embedded media URLs
            embedded_media_urls = []
            media_elements = card_element.find_elements(By.XPATH, './/div[@data-testid="tweetPhoto"]//img | .//div[contains(@data-testid, "videoPlayer")]//video')
            for media_el in media_elements:
                src = media_el.get_attribute("src") or media_el.get_attribute("poster") # poster for videos
                if src:
                    embedded_media_urls.append(src)
            
            is_verified = False
            try:
                card_element.find_element(By.XPATH, './/*[local-name()="svg" and @data-testid="icon-verified"]')
                is_verified = True
            except NoSuchElementException:
                pass

            # Heuristic for thread candidate
            is_thread_candidate = False
            thread_indicators = [r'\(\d+/\d+\)', r'\d+/\d+', 'thread', '🧵', r'1\.', r'a\.', r'i\.'] # Common thread indicators
            for indicator in thread_indicators:
                if re.search(indicator, text_content, re.IGNORECASE):
                    is_thread_candidate = True
                    break
            if user_handle and f"@{user_handle.lstrip('@')}" in text_content and reply_count == 0 : # Replying to self often indicates a thread start
                 # This is a weaker heuristic, could be a self-quote.
                 # More advanced logic would check if the reply is to their *own previous tweet*.
                 pass


            return ScrapedTweet(
                tweet_id=tweet_id,
                user_name=user_name,
                user_handle=user_handle,
                user_is_verified=is_verified,
                created_at=created_at_dt,
                text_content=text_content,
                reply_count=reply_count,
                retweet_count=retweet_count,
                like_count=like_count,
                view_count=view_count,
                tags=tags,
                mentions=mentions,
                tweet_url=tweet_url,
                profile_image_url=profile_image_url,
                embedded_media_urls=list(set(embedded_media_urls)), # Remove duplicates
                is_thread_candidate=is_thread_candidate
            )

        except Exception as e:
            logger.error(f"Error parsing tweet card: {e}", exc_info=True)
            return None

    def _get_tweet_cards_from_page(self) -> List[WebElement]:
        """Finds all tweet card WebElements on the current page."""
        try:
            # This selector targets the article elements that represent tweets
            return self.driver.find_elements(By.XPATH, '//article[@data-testid="tweet"]')
        except Exception as e:
            logger.error(f"Error finding tweet cards: {e}")
            return []

    def scrape_tweets_from_url(
        self,
        url: str,
        search_type: str, # e.g., "keyword", "profile", "hashtag"
        max_tweets: Optional[int] = None,
        stop_if_no_new_tweets_count: Optional[int] = None # How many scrolls with no new tweets before stopping
    ) -> List[ScrapedTweet]:
        
        if max_tweets is None:
            max_tweets = self.default_max_tweets
        if stop_if_no_new_tweets_count is None:
            stop_if_no_new_tweets_count = self.no_new_tweets_scroll_limit

        logger.info(f"Navigating to {url} for scraping ({search_type}). Max tweets: {max_tweets}")
        self.browser_manager.navigate_to(url)
        time.sleep(5) # Wait for initial page load, adjust as needed

        scraped_tweets: List[ScrapedTweet] = []
        seen_tweet_ids = set()
        scroll_attempts_with_no_new_tweets = 0
        
        # Progress tracking
        progress = Progress(0, max_tweets)
        progress.print_progress(0, False, 0, no_tweets_limit=(max_tweets == float('inf')))


        while len(scraped_tweets) < max_tweets:
            try:
                tweet_card_elements = self._get_tweet_cards_from_page()
                if not tweet_card_elements:
                    logger.info("No tweet card elements found on the page.")
                    scroll_attempts_with_no_new_tweets +=1 # Count as no new tweets
                    if scroll_attempts_with_no_new_tweets >= stop_if_no_new_tweets_count:
                        logger.info(f"No new tweets found after {stop_if_no_new_tweets_count} scrolls. Stopping.")
                        break
                    # Try scrolling once more if nothing found initially
                    if not self.scroller.scroll_page(): break # End of page or error
                    time.sleep(random.uniform(self.scroll_delay_min, self.scroll_delay_max))
                    continue

                new_tweets_found_this_scroll = 0
                for card_el in tweet_card_elements:
                    if len(scraped_tweets) >= max_tweets: break
                    
                    # Scroll element into view (helps with lazy loading and interaction)
                    try:
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", card_el)
                        time.sleep(0.2) # Brief pause after scroll
                    except Exception as scroll_err:
                        logger.debug(f"Could not scroll tweet card into view: {scroll_err}")

                    parsed_tweet = self._parse_tweet_card(card_el)
                    if parsed_tweet and parsed_tweet.tweet_id not in seen_tweet_ids:
                        scraped_tweets.append(parsed_tweet)
                        seen_tweet_ids.add(parsed_tweet.tweet_id)
                        new_tweets_found_this_scroll += 1
                        progress.print_progress(len(scraped_tweets), False, 0, no_tweets_limit=(max_tweets == float('inf')))


                if new_tweets_found_this_scroll == 0:
                    scroll_attempts_with_no_new_tweets += 1
                    logger.info(f"No new tweets found in this scroll. Attempt {scroll_attempts_with_no_new_tweets}/{stop_if_no_new_tweets_count}")
                else:
                    scroll_attempts_with_no_new_tweets = 0 # Reset counter

                if scroll_attempts_with_no_new_tweets >= stop_if_no_new_tweets_count:
                    logger.info(f"Stopping scrape for {url}: No new tweets after {stop_if_no_new_tweets_count} consecutive empty scrolls.")
                    break
                
                if len(scraped_tweets) >= max_tweets:
                    logger.info(f"Reached max_tweets ({max_tweets}) for {url}.")
                    break

                # Scroll for more tweets
                if not self.scroller.scroll_page(): # scroll_page returns False if end of page or error
                    logger.info(f"End of page or scroll error for {url}.")
                    break
                
                time.sleep(random.uniform(self.scroll_delay_min, self.scroll_delay_max))

            except TimeoutException:
                logger.warning(f"Timeout during tweet scraping for {url}. May proceed with fewer tweets.")
                break
            except StaleElementReferenceException:
                logger.warning("Encountered stale element reference, attempting to re-fetch cards.")
                time.sleep(1) # Brief pause before retrying
                continue # Retry the loop
            except Exception as e:
                logger.error(f"Unhandled exception during scraping {url}: {e}", exc_info=True)
                break
        
        logger.info(f"Finished scraping for {url}. Found {len(scraped_tweets)} tweets.")
        return scraped_tweets

    def scrape_tweets_by_keyword(self, keyword: str, max_tweets: Optional[int] = None) -> List[ScrapedTweet]:
        # Twitter search URL for keywords: https://x.com/search?q=KEYWORD&src=typed_query&f=live (for latest)
        # The 'f=live' parameter shows latest tweets. Remove for 'Top' tweets.
        # Consider adding a parameter for 'latest' vs 'top' based on config.
        search_url = f"https://x.com/search?q={keyword.replace(' ', '%20')}&f=live" # Default to latest
        return self.scrape_tweets_from_url(search_url, "keyword", max_tweets)

    def scrape_tweets_from_profile(self, profile_url: str, max_tweets: Optional[int] = None) -> List[ScrapedTweet]:
        # Profile URL is typically https://x.com/USERNAME
        return self.scrape_tweets_from_url(profile_url, "profile", max_tweets)

    def scrape_tweets_by_hashtag(self, hashtag: str, max_tweets: Optional[int] = None) -> List[ScrapedTweet]:
        # Hashtag URL: https://x.com/hashtag/HASHTAG?f=live
        clean_hashtag = hashtag.lstrip('#')
        hashtag_url = f"https://x.com/hashtag/{clean_hashtag}?f=live"
        return self.scrape_tweets_from_url(hashtag_url, "hashtag", max_tweets)


if __name__ == '__main__':
    # Example Usage:
    # Ensure config/settings.json is set up, and webdriver (e.g., geckodriver) is in PATH or managed.
    # You might need to log in manually first or provide cookies via accounts.json and BrowserManager config.
    
    # Dummy account config for BrowserManager (if your settings.json doesn't specify cookies for default)
    # Or, ensure your accounts.json has an account with a valid cookie_file_path
    # and pass that account_config to BrowserManager.
    
    # Example: Create a dummy cookie file for testing BrowserManager's cookie loading
    dummy_cookie_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'config')
    dummy_cookie_file = os.path.join(dummy_cookie_dir, "dummy_scraper_cookies.json")

    if not os.path.exists(dummy_cookie_dir):
        os.makedirs(dummy_cookie_dir)

    # Create a dummy cookie file if it doesn't exist, to test cookie loading path in BrowserManager
    if not os.path.exists(dummy_cookie_file):
        with open(dummy_cookie_file, 'w') as f:
            import json
            json.dump([{"name": "test_cookie", "value": "test_value", "domain": ".x.com"}], f)
    
    # Example account config in accounts.json:
    # [
    #   {
    #     "account_id": "test_scraper_user",
    #     "is_active": true,
    #     "cookie_file_path": "dummy_scraper_cookies.json" 
    #   }
    # ]
    # Make sure accounts.json exists and has such an entry, or BrowserManager won't load cookies.

    cfg_loader = ConfigLoader()
    accounts = cfg_loader.get_accounts_config()
    
    # Select an account for the test, or use None for default browser session
    test_account_cfg = None
    if accounts: # Try to use the first account if available
        test_account_cfg = accounts[0]
        logger.info(f"Using account config for: {test_account_cfg.get('account_id')}")
    else: # Fallback if no accounts are configured in accounts.json
        logger.info("No accounts configured in accounts.json, running scraper without specific account cookies.")


    bm = BrowserManager(account_config=test_account_cfg) 
    scraper = TweetScraper(browser_manager=bm, account_id=test_account_cfg.get('account_id') if test_account_cfg else "default_session")

    try:
        logger.info("Starting scraper test...")
        
        # Test 1: Scrape by keyword
        keyword_to_scrape = "AI ethics" # Choose a relevant keyword
        logger.info(f"\n--- Scraping for keyword: {keyword_to_scrape} ---")
        keyword_tweets = scraper.scrape_tweets_by_keyword(keyword_to_scrape, max_tweets=5)
        for i, tweet in enumerate(keyword_tweets):
            logger.info(f"Keyword Tweet {i+1}: ID={tweet.tweet_id}, User={tweet.user_handle}, Text='{tweet.text_content[:50]}...'")
        
        # Test 2: Scrape from a profile (use a known active profile)
        profile_to_scrape = "https://x.com/elonmusk" # Example profile
        logger.info(f"\n--- Scraping profile: {profile_to_scrape} ---")
        profile_tweets = scraper.scrape_tweets_from_profile(profile_to_scrape, max_tweets=5)
        for i, tweet in enumerate(profile_tweets):
            logger.info(f"Profile Tweet {i+1}: ID={tweet.tweet_id}, User={tweet.user_handle}, Text='{tweet.text_content[:50]}...'")

        # Test 3: Scrape by hashtag
        hashtag_to_scrape = "#OpenAI"
        logger.info(f"\n--- Scraping for hashtag: {hashtag_to_scrape} ---")
        hashtag_tweets = scraper.scrape_tweets_by_hashtag(hashtag_to_scrape, max_tweets=5)
        for i, tweet in enumerate(hashtag_tweets):
            logger.info(f"Hashtag Tweet {i+1}: ID={tweet.tweet_id}, User={tweet.user_handle}, Text='{tweet.text_content[:50]}...'")

    except Exception as e:
        logger.error(f"Error during scraper test: {e}", exc_info=True)
    finally:
        logger.info("Closing browser manager...")
        scraper.browser_manager.close_driver()
        # Clean up dummy cookie file if it was created by this test script
        # if os.path.exists(dummy_cookie_file) and "dummy_scraper_cookies.json" in dummy_cookie_file:
        #     os.remove(dummy_cookie_file)
        logger.info("Scraper test finished.")
