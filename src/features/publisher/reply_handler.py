import logging
import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException

from core.browser_manager import BrowserManager
from data_models import ScrapedTweet

logger = logging.getLogger(__name__)


def reply_to_tweet(browser_manager: BrowserManager, original_tweet: ScrapedTweet, reply_text: str) -> bool:
    driver = browser_manager.get_driver()
    # Small human-like jitter to reduce rate/automation detection
    time.sleep(random.uniform(0.8, 2.2))
    if not original_tweet.tweet_url:
        logger.error(f"Cannot reply to tweet {original_tweet.tweet_id}: Missing tweet URL.")
        return False
    if not reply_text:
        logger.error(f"Cannot reply to tweet {original_tweet.tweet_id}: Reply text is empty.")
        return False

    logger.info(
        f"Attempting to reply to tweet {original_tweet.tweet_id} with text: '{reply_text[:50]}...'"
    )

    try:
        browser_manager.navigate_to(str(original_tweet.tweet_url))
        time.sleep(3)

        main_tweet_article_xpath = (
            f"//article[.//a[contains(@href, '/status/{original_tweet.tweet_id}')]]"
        )
        main_tweet_element = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, main_tweet_article_xpath))
        )

        reply_icon_button = WebDriverWait(main_tweet_element, 10).until(
            EC.element_to_be_clickable((By.XPATH, ".//button[@data-testid='reply']"))
        )
        reply_icon_button.click()
        logger.info(f"Clicked reply icon for tweet {original_tweet.tweet_id}.")
        time.sleep(2)

        # Target the active reply modal/dialog
        try:
            dialog = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[@role='dialog' and @aria-modal='true']"))
            )
        except TimeoutException:
            dialog = driver  # fallback to global scope if modal not detected

        # Locate and type into the reply textarea strictly within the dialog
        reply_text_area_xpath = ".//div[@data-testid='tweetTextarea_0' and @role='textbox']"
        reply_text_area = WebDriverWait(dialog, 15).until(
            EC.presence_of_element_located((By.XPATH, reply_text_area_xpath))
        )
        try:
            reply_text_area.click()
            reply_text_area.send_keys(Keys.CONTROL, "a")
            reply_text_area.send_keys(Keys.BACKSPACE)
        except Exception:
            pass
        # Enforce platform cap for replies
        safe_reply = (reply_text or "")[:270]
        reply_text_area.send_keys(safe_reply)
        logger.info("Typed reply text into textarea.")

        # Wait for overlay/mask to disappear
        try:
            WebDriverWait(driver, 5).until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, "[data-testid='twc-cc-mask']"))
            )
        except Exception:
            pass

        # Wait for the Reply button to become enabled within the dialog
        def find_enabled_reply_button():
            try:
                return dialog.find_element(
                    By.XPATH,
                    ".//button[@data-testid='tweetButton' and not(@disabled) and not(@aria-disabled='true')]",
                )
            except Exception:
                return None

        reply_post_button = None
        for attempt in range(3):
            reply_post_button = find_enabled_reply_button()
            if reply_post_button:
                break
            # Nudge the editor to trigger enablement
            try:
                reply_text_area.send_keys(" ")
                reply_text_area.send_keys(Keys.BACKSPACE)
            except Exception:
                pass
            time.sleep(0.5)

        if not reply_post_button:
            # As a fallback, attempt Ctrl+Enter to submit
            logger.warning("Reply button still disabled; attempting Ctrl+Enter fallback.")
            try:
                reply_text_area.send_keys(Keys.CONTROL, Keys.ENTER)
                # Confirm by waiting for dialog to close
                if dialog is not driver:
                    WebDriverWait(driver, 10).until(EC.staleness_of(dialog))
                time.sleep(1)
                return True
            except Exception as e:
                logger.error(f"Failed to submit reply via keyboard fallback: {e}")
                return False

        # Click the enabled Reply button with fallbacks
        try:
            try:
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", reply_post_button)
            except Exception:
                pass
            reply_post_button.click()
        except ElementClickInterceptedException:
            logger.warning("Reply button click intercepted, trying JS click.")
            try:
                driver.execute_script("arguments[0].click();", reply_post_button)
            except Exception:
                logger.warning("JS click failed; sending Ctrl+Enter as fallback for reply.")
                try:
                    reply_text_area.send_keys(Keys.CONTROL, Keys.ENTER)
                except Exception as e:
                    logger.error(f"Failed to submit reply via keyboard fallback: {e}")
                    return False

        logger.info("Clicked 'Reply' button in composer.")

        # Basic error/toast detection for rate limits or failures
        try:
            error_candidate = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(., 'Try again') or contains(., 'rate limit') or contains(., 'over the limit') or contains(., 'went wrong')]"))
            )
            logger.warning(f"Reply may have failed due to platform limits or errors: {(error_candidate.text or '').strip()}")
        except Exception:
            pass

        # Wait for dialog to close as a confirmation
        try:
            if dialog is not driver:
                WebDriverWait(driver, 10).until(EC.staleness_of(dialog))
        except Exception:
            # Fallback tiny delay if staleness check is inconclusive
            time.sleep(2)

        time.sleep(random.uniform(1.2, 2.6))
        return True
    except TimeoutException as e:
        logger.error(
            f"Timeout while trying to reply to tweet {original_tweet.tweet_id}: {e}"
        )
        return False
    except Exception as e:
        logger.error(
            f"Failed to reply to tweet {original_tweet.tweet_id}: {e}", exc_info=True
        )
        return False
