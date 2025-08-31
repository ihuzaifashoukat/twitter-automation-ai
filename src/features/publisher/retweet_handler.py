import logging
import time
import random
from typing import Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from core.browser_manager import BrowserManager
from data_models import ScrapedTweet

logger = logging.getLogger(__name__)


def retweet_or_quote(
    browser_manager: BrowserManager,
    original_tweet: ScrapedTweet,
    final_quote_text: Optional[str],
) -> bool:
    driver = browser_manager.get_driver()
    if not original_tweet.tweet_url:
        logger.error(f"Cannot retweet tweet {original_tweet.tweet_id}: Missing tweet URL.")
        return False

    is_quote_tweet = bool(final_quote_text)
    action_type_log = "Quote Tweet" if is_quote_tweet else "Retweet"
    logger.info(f"Attempting {action_type_log} for tweet ID: {original_tweet.tweet_id}")
    if final_quote_text:
        logger.info(f"Quote text: '{final_quote_text[:50]}...'")

    try:
        browser_manager.navigate_to(str(original_tweet.tweet_url))
        time.sleep(random.uniform(2.0, 3.8))

        main_tweet_article_xpath = (
            f"//article[.//a[contains(@href, '/status/{original_tweet.tweet_id}')]]"
        )
        main_tweet_element = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, main_tweet_article_xpath))
        )

        retweet_icon_button = WebDriverWait(main_tweet_element, 10).until(
            EC.element_to_be_clickable((By.XPATH, ".//button[@data-testid='retweet']"))
        )
        retweet_icon_button.click()
        logger.info(f"Clicked retweet icon for tweet {original_tweet.tweet_id}.")
        time.sleep(1)

        if is_quote_tweet:
            # Generic, resilient selection for quote option
            try:
                quote_option = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//div[@role='menuitem' and contains(., 'Quote')]"))
                )
            except TimeoutException:
                quote_option = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//div[@data-testid='Dropdown']//a[contains(@href,'/compose/tweet')]"))
                )
            quote_option.click()
            logger.info("Clicked 'Quote' option.")
            time.sleep(2)

            quote_text_area_xpath = "//div[@data-testid='tweetTextarea_0' and @role='textbox']"
            quote_text_area = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, quote_text_area_xpath))
            )
            try:
                quote_text_area.click()
                from selenium.webdriver.common.keys import Keys
                quote_text_area.send_keys(Keys.CONTROL, "a")
                quote_text_area.send_keys(Keys.BACKSPACE)
            except Exception:
                pass
            # Enforce platform cap for quote text as safety
            safe_quote = (final_quote_text or "")[:270]
            quote_text_area.send_keys(safe_quote)
            logger.info("Typed quote text.")

            post_button = WebDriverWait(driver, 12).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@data-testid='tweetButton']"))
            )
            post_button.click()
            logger.info("Clicked 'Post' for quote tweet.")
        else:
            try:
                confirm_retweet_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[@data-testid='retweetConfirm']"))
                )
            except TimeoutException:
                confirm_retweet_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//div[@role='menuitem' and contains(., 'Repost')]//div[1]"))
                )
            confirm_retweet_button.click()
            logger.info("Clicked 'Repost' (confirm retweet) option.")

        # Light backoff after action to avoid rapid-fire sequences
        time.sleep(random.uniform(2.0, 4.5))
        logger.info(f"{action_type_log} for tweet {original_tweet.tweet_id} successful.")
        return True
    except TimeoutException as e:
        logger.error(f"Timeout during {action_type_log.lower()} for tweet {original_tweet.tweet_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to {action_type_log.lower()} tweet {original_tweet.tweet_id}: {e}", exc_info=True)
        return False
