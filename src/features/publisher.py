import os
import sys
import time
import requests
import mimetypes
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Adjust import paths
try:
    from ..core.browser_manager import BrowserManager
    from ..core.config_loader import ConfigLoader
    from ..core.llm_service import LLMService
    from ..utils.logger import setup_logger
    from ..data_models import TweetContent, ScrapedTweet, AccountConfig, LLMSettings
except ImportError:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..')) # Add root src to path
    from src.core.browser_manager import BrowserManager
    from src.core.config_loader import ConfigLoader
    from src.core.llm_service import LLMService
    from src.utils.logger import setup_logger
    from src.data_models import TweetContent, ScrapedTweet, AccountConfig, LLMSettings

config_loader_instance = ConfigLoader()
logger = setup_logger(config_loader_instance)

class TweetPublisher:
    def __init__(self, browser_manager: BrowserManager, llm_service: LLMService, account_config: AccountConfig):
        self.browser_manager = browser_manager
        self.driver = self.browser_manager.get_driver()
        self.llm_service = llm_service
        self.account_config = account_config # Specific account performing actions
        self.config_loader = browser_manager.config_loader # Reuse config loader
        
        self.twitter_automation_settings = self.config_loader.get_settings().get('twitter_automation', {})
        self.media_dir = self.twitter_automation_settings.get('media_directory', 'media_files')
        if not os.path.exists(self.media_dir):
            os.makedirs(self.media_dir, exist_ok=True)

    async def _download_media(self, media_url: str) -> Optional[str]:
        """Downloads media from a URL and saves it locally."""
        if not media_url:
            return None
        try:
            logger.info(f"Downloading media from: {media_url}")
            response = requests.get(media_url, stream=True, timeout=30)
            response.raise_for_status()

            # Try to get a meaningful filename and extension
            parsed_url = urlparse(media_url)
            base_name = os.path.basename(parsed_url.path)
            if not base_name or '.' not in base_name: # Fallback if no filename in URL
                content_type = response.headers.get('content-type')
                ext = mimetypes.guess_extension(content_type) if content_type else '.jpg'
                base_name = f"media_{int(time.time())}{ext or '.unknown'}"
            
            file_path = os.path.join(self.media_dir, base_name)
            
            # Ensure unique filename
            counter = 1
            original_file_path = file_path
            while os.path.exists(file_path):
                name, ext = os.path.splitext(original_file_path)
                file_path = f"{name}_{counter}{ext}"
                counter += 1

            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            logger.info(f"Media downloaded successfully to: {file_path}")
            return file_path
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download media from {media_url}: {e}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred during media download from {media_url}: {e}")
            return None

    async def post_new_tweet(self, content: TweetContent, llm_settings: Optional[LLMSettings] = None) -> bool:
        """
        Posts a new tweet. If content.text is a prompt, it generates text first.
        Downloads media from URLs if provided.
        """
        tweet_text = content.text
        
        # Check if text needs generation (e.g. if it's a prompt)
        # This logic can be more sophisticated, e.g. checking a flag in TweetContent
        if llm_settings and ("generate tweet about" in tweet_text.lower() or "write a post on" in tweet_text.lower()): # Simple check
            logger.info(f"Generating tweet text for prompt: {tweet_text}")
            generated_text = await self.llm_service.generate_text(
                prompt=tweet_text,
                service_preference=llm_settings.service_preference,
                model_name=llm_settings.model_name_override,
                max_tokens=llm_settings.max_tokens,
                temperature=llm_settings.temperature
            )
            if not generated_text:
                logger.error("Failed to generate tweet text. Aborting post.")
                return False
            tweet_text = generated_text
            logger.info(f"Generated tweet text: {tweet_text}")

        # Prepare media
        final_media_paths: List[str] = content.local_media_paths or []
        if content.media_urls:
            for url in content.media_urls:
                downloaded_path = await self._download_media(str(url))
                if downloaded_path:
                    final_media_paths.append(downloaded_path)
        
        # Ensure all media paths are absolute for Selenium
        final_media_paths = [os.path.abspath(p) for p in final_media_paths if os.path.exists(p)]

        logger.info(f"Attempting to post tweet: '{tweet_text[:50]}...' with {len(final_media_paths)} media file(s).")

        try:
            # Navigate to Twitter home or composer, ensure logged in state
            self.driver.get("https://x.com/home") # Or specific composer URL if available: https://x.com/compose/tweet
            time.sleep(3) # Wait for page load

            # Click the main tweet button to open composer (if not already on compose page)
            # This selector might need adjustment based on X.com's current UI
            try:
                main_tweet_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, '//a[@data-testid="SideNav_NewTweet_Button"]'))
                )
                main_tweet_button.click()
                logger.info("Clicked main tweet button to open composer.")
                time.sleep(2) # Wait for composer to open
            except TimeoutException:
                logger.info("Main tweet button not found or not clickable, assuming composer might be open or navigating to compose URL.")
                self.driver.get("https://x.com/compose/tweet")
                time.sleep(3)


            # Find the tweet text area
            text_area = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.XPATH, '//div[@data-testid="tweetTextarea_0"]'))
            )
            # text_area.click() # Sometimes needed
            text_area.clear()
            text_area.send_keys(tweet_text)
            logger.info("Typed tweet text into textarea.")

            # Upload media if any
            if final_media_paths:
                # Twitter typically allows up to 4 images, 1 GIF, or 1 video.
                # This uploader handles one file at a time if multiple inputs are not present.
                # For multiple files, X.com might have one input that accepts multiple files,
                # or you might need to click an "add media" button for subsequent files.
                
                # The input element is often hidden. It might be easier to find the button that triggers it.
                # For simplicity, assuming a single file input `input[type="file"]` that can handle multiple files.
                # Join paths with '\n' if the input field accepts it for multiple files.
                
                # Locate the file input element. It's often visually hidden.
                # The actual button to click might be different.
                file_input_xpath = '//input[@data-testid="fileInput" and @type="file"]'
                
                # Click the "Add media" button first if it's separate
                try:
                    add_media_button = self.driver.find_element(By.XPATH, '//button[@data-testid="mediaButton"]')
                    add_media_button.click()
                    time.sleep(1) # Wait for file dialog to be ready (conceptually)
                except NoSuchElementException:
                    logger.debug("Did not find a separate 'Add Media' button, proceeding to file input.")

                file_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, file_input_xpath))
                )
                
                # For multiple files, send them as a newline-separated string to the input element
                # This works if the <input type="file" multiple> is used.
                files_to_upload_str = "\n".join(final_media_paths)
                file_input.send_keys(files_to_upload_str)
                logger.info(f"Sent {len(final_media_paths)} media file(s) to input: {files_to_upload_str}")
                time.sleep(5) # Wait for media to upload and preview

            # Click the "Post" button
            post_button = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, '//button[@data-testid="tweetButton"]'))
            )
            post_button.click()
            logger.info("Clicked 'Post' button.")

            # Wait for confirmation (e.g., "Your post was sent.") or URL change, or specific element indicating success
            # This is highly dependent on X.com's UI.
            time.sleep(5) # Simple wait for now
            # Add more robust success check here, e.g., looking for "Your post was sent." notification

            logger.info(f"Tweet posted successfully: '{tweet_text[:50]}...'")
            return True

        except TimeoutException as e:
            logger.error(f"Timeout while trying to post tweet: {e}")
            # self.browser_manager.save_screenshot("post_tweet_timeout") # Optional: for debugging
            return False
        except Exception as e:
            logger.error(f"Failed to post tweet: {e}", exc_info=True)
            # self.browser_manager.save_screenshot("post_tweet_error") # Optional
            return False

    async def reply_to_tweet(self, original_tweet: ScrapedTweet, reply_text: str) -> bool:
        """
        Replies to a given tweet.
        :param original_tweet: The ScrapedTweet object of the tweet to reply to.
        :param reply_text: The text content of the reply (should be pre-generated).
        """
        if not original_tweet.tweet_url:
            logger.error(f"Cannot reply to tweet {original_tweet.tweet_id}: Missing tweet URL.")
            return False
        if not reply_text:
            logger.error(f"Cannot reply to tweet {original_tweet.tweet_id}: Reply text is empty.")
            return False

        logger.info(f"Attempting to reply to tweet {original_tweet.tweet_id} with text: '{reply_text[:50]}...'")

        try:
            self.browser_manager.navigate_to(str(original_tweet.tweet_url))
            time.sleep(3) # Wait for tweet page to load

            # Click the reply button on the main tweet to open the reply composer
            # This selector targets the reply icon/button for the specific tweet.
            # It might be within an article tag corresponding to the tweet.
            # First, try to find the main tweet article to scope the search for reply button
            main_tweet_article_xpath = f"//article[.//a[contains(@href, '/status/{original_tweet.tweet_id}')]]"
            main_tweet_element = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.XPATH, main_tweet_article_xpath))
            )
            
            reply_icon_button = WebDriverWait(main_tweet_element, 10).until(
                EC.element_to_be_clickable((By.XPATH, './/button[@data-testid="reply"]')) # Relative to the tweet article
            )
            reply_icon_button.click()
            logger.info(f"Clicked reply icon for tweet {original_tweet.tweet_id}.")
            time.sleep(2) # Wait for reply composer to appear

            # The reply composer's text area and post button might be similar to the main tweet composer
            reply_text_area_xpath = '//div[@data-testid="tweetTextarea_0" and @role="textbox"]' # More specific
            reply_text_area = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.XPATH, reply_text_area_xpath))
            )
            
            # reply_text_area.click() # Sometimes helpful
            reply_text_area.clear()
            reply_text_area.send_keys(reply_text)
            logger.info("Typed reply text into textarea.")

            # Click the "Reply" button in the composer
            # This is often also data-testid="tweetButton" but it's specific to the composer context
            reply_post_button_xpath = '//button[@data-testid="tweetButton"]' 
            # Ensure it's the one in the modal/composer, might need a more specific parent selector if ambiguous
            # For example, if the composer is in a modal: //div[@data-testid="layers"]//button[@data-testid="tweetButton"]
            
            # Let's try to find it within a modal layer if possible, as that's common for reply composers
            try:
                layers_xpath = '//div[@data-testid="layers"]'
                modal_layer = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, layers_xpath))
                )
                reply_post_button = WebDriverWait(modal_layer, 10).until(
                    EC.element_to_be_clickable((By.XPATH, './/button[@data-testid="tweetButton"]'))
                )
            except TimeoutException: # Fallback if not in a typical modal layer structure
                logger.debug("Reply composer not found in standard modal layer, trying general tweetButton.")
                reply_post_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, reply_post_button_xpath))
                )

            reply_post_button.click()
            logger.info("Clicked 'Reply' button in composer.")

            # Wait for confirmation (e.g., "Your reply was sent.")
            # This is highly UI-dependent. A simple delay for now.
            time.sleep(5) 
            # TODO: Add a more robust check for reply success, e.g., looking for the reply to appear on the page or a success notification.
            
            logger.info(f"Reply to tweet {original_tweet.tweet_id} posted successfully.")
            return True

        except TimeoutException as e:
            logger.error(f"Timeout while trying to reply to tweet {original_tweet.tweet_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to reply to tweet {original_tweet.tweet_id}: {e}", exc_info=True)
            return False

    async def retweet_tweet(self, original_tweet: ScrapedTweet, quote_text_prompt_or_direct: Optional[str] = None, llm_settings_for_quote: Optional[LLMSettings] = None) -> bool:
        """
        Retweets a given tweet. Can be a simple retweet or a quote tweet if quote_text is provided.
        If quote_text_prompt_or_direct is a prompt, it will be generated by LLM.
        """
        if not original_tweet.tweet_url: # Need URL to navigate to the tweet
            logger.error(f"Cannot retweet tweet {original_tweet.tweet_id}: Missing tweet URL.")
            return False

        final_quote_text: Optional[str] = None
        is_quote_tweet = bool(quote_text_prompt_or_direct)

        if is_quote_tweet and llm_settings_for_quote and \
           ("generate quote for" in quote_text_prompt_or_direct.lower() or "write a quote about" in quote_text_prompt_or_direct.lower()):
            logger.info(f"Generating quote text for tweet {original_tweet.tweet_id} using prompt: {quote_text_prompt_or_direct}")
            generated_quote = await self.llm_service.generate_text(
                prompt=quote_text_prompt_or_direct,
                service_preference=llm_settings_for_quote.service_preference,
                model_name=llm_settings_for_quote.model_name_override,
                max_tokens=llm_settings_for_quote.max_tokens,
                temperature=llm_settings_for_quote.temperature
            )
            if not generated_quote:
                logger.error(f"Failed to generate quote text for tweet {original_tweet.tweet_id}. Aborting retweet.")
                return False
            final_quote_text = generated_quote
            logger.info(f"Generated quote text: {final_quote_text}")
        elif is_quote_tweet:
            final_quote_text = quote_text_prompt_or_direct # Use as direct text

        action_type_log = "Quote Tweet" if is_quote_tweet else "Retweet"
        logger.info(f"Attempting {action_type_log} for tweet ID: {original_tweet.tweet_id}")
        if final_quote_text:
            logger.info(f"Quote text: '{final_quote_text[:50]}...'")

        try:
            self.browser_manager.navigate_to(str(original_tweet.tweet_url))
            time.sleep(3) # Wait for tweet page to load

            main_tweet_article_xpath = f"//article[.//a[contains(@href, '/status/{original_tweet.tweet_id}')]]"
            main_tweet_element = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.XPATH, main_tweet_article_xpath))
            )
            
            retweet_button_xpath = './/button[@data-testid="retweet"]' # Relative to tweet article
            retweet_icon_button = WebDriverWait(main_tweet_element, 10).until(
                EC.element_to_be_clickable((By.XPATH, retweet_button_xpath))
            )
            
            # Check if already retweeted (aria-label might change to "Undo Retweet" or similar)
            # Or the icon color might change. This is complex to check reliably via DOM alone for retweets.
            # For now, we'll proceed. Twitter usually handles duplicate retweets gracefully (e.g., by un-retweeting).
            
            retweet_icon_button.click()
            logger.info(f"Clicked retweet icon for tweet {original_tweet.tweet_id}.")
            time.sleep(1) # Wait for retweet menu to appear

            if is_quote_tweet:
                # Click "Quote" option in the menu
                quote_option_xpath = '//a[@data-testid="tweet opción Quote"]' # This selector is an example, needs verification
                # A more reliable way might be to find menu item by role and text "Quote" or "Quote Tweet"
                # Example: //div[@role="menuitem"]//span[text()="Quote"] or similar
                # For now, using a placeholder data-testid which is unlikely to be correct.
                # Let's try a more generic approach: find a menu item containing "Quote"
                try:
                    quote_option = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, '//div[@role="menuitem" and contains(., "Quote")]'))
                    )
                except TimeoutException: # Fallback for older UIs or different text
                     quote_option = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, '//div[@data-testid="Dropdown"]//a[contains(@href,"/compose/tweet")]'))) # Common pattern for quote tweet link
                
                quote_option.click()
                logger.info("Clicked 'Quote' option.")
                time.sleep(2) # Wait for quote tweet composer to appear

                # Composer text area for quote
                quote_text_area_xpath = '//div[@data-testid="tweetTextarea_0" and @role="textbox"]'
                quote_text_area = WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.XPATH, quote_text_area_xpath))
                )
                quote_text_area.clear()
                quote_text_area.send_keys(final_quote_text)
                logger.info("Typed quote text.")

                # Click "Post" button for the quote tweet
                post_button_xpath = '//button[@data-testid="tweetButton"]' # Usually the same for all posts
                post_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, post_button_xpath))
                )
                post_button.click()
                logger.info("Clicked 'Post' for quote tweet.")

            else: # Simple Retweet
                # Click "Repost" (or "Retweet") confirmation in the menu
                # Example: //div[@role="menuitem"]//span[text()="Repost"]
                # Or data-testid="retweetConfirm"
                try:
                    confirm_retweet_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, '//button[@data-testid="retweetConfirm"]')) # Common testid
                    )
                except TimeoutException:
                     confirm_retweet_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, '//div[@role="menuitem" and contains(., "Repost")]//div[1]')) # Click the div if span is tricky
                    )
                confirm_retweet_button.click()
                logger.info("Clicked 'Repost' (confirm retweet) option.")

            time.sleep(5) # Wait for action to complete
            # TODO: Add robust check for retweet/quote tweet success.
            
            logger.info(f"{action_type_log} for tweet {original_tweet.tweet_id} successful.")
            return True

        except TimeoutException as e:
            logger.error(f"Timeout during {action_type_log.lower()} for tweet {original_tweet.tweet_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to {action_type_log.lower()} tweet {original_tweet.tweet_id}: {e}", exc_info=True)
            return False


if __name__ == '__main__':
    import asyncio
    # Example Usage:
    # This requires config/settings.json and potentially config/accounts.json to be set up
    # with valid API keys for LLM and cookie info for Twitter.

    async def test_publisher():
        cfg_loader = ConfigLoader()
        accounts = cfg_loader.get_accounts_config()
        
        if not accounts:
            logger.error("No accounts configured in config/accounts.json. Cannot run publisher test.")
            return

        # Use the first active account for testing
        active_account_config_dict = None
        for acc_dict in accounts:
            if acc_dict.get("is_active", True): # Default to active if not specified
                # Convert dict to AccountConfig Pydantic model if needed by BrowserManager/Publisher
                # For now, assuming BrowserManager can handle dict or has its own parsing
                active_account_config_dict = acc_dict 
                break
        
        if not active_account_config_dict:
            logger.error("No active accounts found in config/accounts.json.")
            return
        
        # Create AccountConfig Pydantic model instance
        # This assumes your accounts.json structure matches AccountConfig or is adaptable
        # For simplicity, let's assume direct fields match or BrowserManager handles dict
        try:
            # A more robust way would be to parse active_account_config_dict into AccountConfig model
            # For now, we pass the dict, BrowserManager is designed to handle it for cookies.
            # Publisher's __init__ expects AccountConfig model, so we should ideally parse it.
            # However, for this test, we'll focus on the publisher methods.
            # Let's assume account_config in publisher is mainly for context like account_id.
            # A proper AccountConfig model instance should be created for full functionality.
            
            # Simplified AccountConfig for test context
            mock_account_model = AccountConfig(
                account_id=active_account_config_dict.get("account_id", "test_publisher_user"),
                cookie_file_path=active_account_config_dict.get("cookie_file_path") # BrowserManager uses this
            )

        except Exception as e:
            logger.error(f"Failed to prepare account config for test: {e}")
            return


        bm = BrowserManager(account_config=active_account_config_dict) # BrowserManager takes the dict
        llm = LLMService(config_loader=cfg_loader)
        
        # Pass the Pydantic model to publisher if its __init__ strictly requires it
        # For this test, we'll assume the publisher can work with the account_id from a simplified model
        # or that its __init__ is flexible. The provided code for Publisher takes AccountConfig.
        publisher = TweetPublisher(browser_manager=bm, llm_service=llm, account_config=mock_account_model)

        try:
            logger.info(f"Testing publisher for account: {mock_account_model.account_id}")

            # Test 1: Post a simple text tweet
            simple_content = TweetContent(text="Hello from the automated world! This is a test tweet. #Python #Automation")
            logger.info("\n--- Testing simple text post ---")
            success = await publisher.post_new_tweet(simple_content)
            logger.info(f"Simple text post successful: {success}")
            if not success: time.sleep(2) # Pause if failed

            # Test 2: Post a tweet with text generated by LLM
            llm_prompt = "Generate a short, optimistic tweet about the impact of AI on creativity. Include #AI #Creativity."
            # Define LLMSettings for this generation
            gen_llm_settings = LLMSettings(service_preference="gemini", max_tokens=100, temperature=0.8) # Prefer Gemini
            
            prompt_content = TweetContent(text=llm_prompt) # Text here is the prompt
            logger.info("\n--- Testing LLM-generated post ---")
            success_llm = await publisher.post_new_tweet(prompt_content, llm_settings=gen_llm_settings)
            logger.info(f"LLM-generated post successful: {success_llm}")
            if not success_llm: time.sleep(2)


            # Test 3: Post a tweet with media (requires a valid image/video URL)
            # Replace with a real, accessible image URL for testing
            # media_image_url = "https://www.python.org/static/community_logos/python-logo-master-v3-TM.png"
            # content_with_media = TweetContent(
            #     text="Check out this cool Python logo! #Python #Logo #Test",
            #     media_urls=[media_image_url]
            # )
            # logger.info("\n--- Testing post with media ---")
            # success_media = await publisher.post_new_tweet(content_with_media)
            # logger.info(f"Post with media successful: {success_media}")

        except Exception as e:
            logger.error(f"Error during publisher test: {e}", exc_info=True)
        finally:
            logger.info("Closing browser manager after publisher test...")
            publisher.browser_manager.close_driver()
            logger.info("Publisher test finished.")

    asyncio.run(test_publisher())
