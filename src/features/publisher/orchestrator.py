import os
import logging
from typing import Optional

from core.browser_manager import BrowserManager
from core.config_loader import ConfigLoader
from core.llm_service import LLMService
from utils.logger import setup_logger
from data_models import TweetContent, ScrapedTweet, AccountConfig, LLMSettings

from .content_generator import generate_post_text_if_needed, maybe_generate_quote_text
from .media_manager import prepare_media_paths
from .composer import post_new_tweet as compose_and_post
from .reply_handler import reply_to_tweet as do_reply
from .retweet_handler import retweet_or_quote as do_retweet_or_quote


# Configure logging once at import-time for this package
_config_loader_instance = ConfigLoader()
setup_logger(_config_loader_instance)
logger = logging.getLogger(__name__)


class TweetPublisher:
    """High-level facade that orchestrates tweet posting, replying, and retweeting.

    Internally delegates to focused modules for content generation, media handling,
    audience selection, and Selenium UI operations. Public API remains compatible
    with the previous monolithic implementation.
    """

    def __init__(self, browser_manager: BrowserManager, llm_service: LLMService, account_config: AccountConfig):
        self.browser_manager = browser_manager
        self.llm_service = llm_service
        self.account_config = account_config
        self.config_loader = browser_manager.config_loader

        twitter_automation_settings = self.config_loader.get_settings().get("twitter_automation", {})
        self.media_dir = twitter_automation_settings.get("media_directory", "media_files")
        os.makedirs(self.media_dir, exist_ok=True)

    async def post_new_tweet(self, content: TweetContent, llm_settings: Optional[LLMSettings] = None) -> bool:
        # 1) Generate text if needed
        tweet_text = await generate_post_text_if_needed(
            content.text, llm_settings, self.llm_service
        ) if content and content.text else (content.text if content else "")

        # 2) Prepare media (download URLs, merge with local paths). Pass BrowserManager for authenticated downloads.
        final_media_paths = await prepare_media_paths(content, self.media_dir, self.browser_manager)

        # 3) Compose and post
        return compose_and_post(
            self.browser_manager,
            self.account_config,
            tweet_text,
            final_media_paths,
        )

    async def reply_to_tweet(self, original_tweet: ScrapedTweet, reply_text: str) -> bool:
        return do_reply(self.browser_manager, original_tweet, reply_text)

    async def retweet_tweet(
        self,
        original_tweet: ScrapedTweet,
        quote_text_prompt_or_direct: Optional[str] = None,
        llm_settings_for_quote: Optional[LLMSettings] = None,
    ) -> bool:
        final_quote_text = await maybe_generate_quote_text(
            quote_text_prompt_or_direct, llm_settings_for_quote, self.llm_service
        )
        return do_retweet_or_quote(self.browser_manager, original_tweet, final_quote_text)
