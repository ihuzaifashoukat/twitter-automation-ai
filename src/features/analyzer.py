import os
import sys
import json
from typing import Optional

# Adjust import paths
try:
    from ..core.llm_service import LLMService
    from ..core.config_loader import ConfigLoader
    from ..utils.logger import setup_logger
    from ..data_models import ScrapedTweet, LLMSettings, AccountConfig
except ImportError:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..')) # Add root src to path
    from src.core.llm_service import LLMService
    from src.core.config_loader import ConfigLoader
    from src.utils.logger import setup_logger
    from src.data_models import ScrapedTweet, LLMSettings, AccountConfig

config_loader_instance = ConfigLoader()
logger = setup_logger(config_loader_instance)

class TweetAnalyzer:
    def __init__(self, llm_service: LLMService, account_config: Optional[AccountConfig] = None):
        self.llm_service = llm_service
        self.account_config = account_config # For account-specific LLM settings if needed
        self.config_loader = llm_service.config_loader # Reuse config loader

    async def check_if_thread_with_llm(self, tweet: ScrapedTweet, custom_llm_settings: Optional[LLMSettings] = None) -> bool:
        """
        Uses LLM to analyze tweet content and determine if it's likely part of a thread.
        Returns True if determined to be a thread, False otherwise.
        """
        if not tweet.text_content:
            return False

        # Determine LLM settings to use
        # Priority: custom_llm_settings > account_config.action_config.llm_settings_for_thread_analysis > global_action_config.llm_settings_for_thread_analysis
        llm_settings_to_use = custom_llm_settings
        if not llm_settings_to_use and self.account_config and self.account_config.action_config:
            llm_settings_to_use = self.account_config.action_config.llm_settings_for_thread_analysis
        
        if not llm_settings_to_use:
            # Fallback to global default thread analysis LLM settings
            global_action_config_dict = self.config_loader.get_twitter_automation_setting('action_config', {})
            if global_action_config_dict: # Check if action_config exists in settings
                default_thread_llm_settings_dict = global_action_config_dict.get('llm_settings_for_thread_analysis', {})
                llm_settings_to_use = LLMSettings(**default_thread_llm_settings_dict) if default_thread_llm_settings_dict else LLMSettings() # Default LLMSettings if not configured
            else: # Absolute fallback if no action_config in settings
                llm_settings_to_use = LLMSettings(max_tokens=70, temperature=0.2, service_preference='gemini')


        prompt = f"""Analyze the following tweet text to determine if it is part of a thread or a standalone tweet.
A tweet is part of a thread if it explicitly indicates continuation (e.g., "(1/n)", "thread below", "🧵"), or if its content strongly implies it's one piece of a multi-part discussion.
Consider common thread indicators.

Tweet text:
"{tweet.text_content}"

Based on this text, is this tweet likely part of a thread?
Respond with only "true" or "false".
"""
        
        logger.debug(f"Thread analysis prompt for tweet {tweet.tweet_id}:\n{prompt}")
        logger.info(f"Using LLM settings for thread analysis: Service={llm_settings_to_use.service_preference}, Model={llm_settings_to_use.model_name_override or 'default'}")

        response_text = await self.llm_service.generate_text(
            prompt=prompt,
            service_preference=llm_settings_to_use.service_preference,
            model_name=llm_settings_to_use.model_name_override,
            max_tokens=llm_settings_to_use.max_tokens, # Usually very short response needed
            temperature=llm_settings_to_use.temperature
        )

        if response_text:
            response_text = response_text.strip().lower()
            logger.debug(f"LLM response for thread analysis of tweet {tweet.tweet_id}: '{response_text}'")
            if response_text == "true":
                return True
            elif response_text == "false":
                return False
            else:
                logger.warning(f"LLM for thread analysis (tweet {tweet.tweet_id}) returned non-boolean: '{response_text}'. Assuming not a thread.")
                return False
        
        logger.warning(f"LLM did not return a response for thread analysis of tweet {tweet.tweet_id}. Assuming not a thread.")
        return False

if __name__ == '__main__':
    import asyncio
    # Example Usage:
    # This requires config/settings.json with LLM API keys.

    async def test_analyzer():
        cfg_loader = ConfigLoader()
        llm = LLMService(config_loader=cfg_loader)
        analyzer = TweetAnalyzer(llm_service=llm)

        # Example tweets
        tweet1_standalone = ScrapedTweet(tweet_id="s1", text_content="Just enjoyed a great cup of coffee! #morning")
        tweet2_thread_indicator_text = ScrapedTweet(tweet_id="t1", text_content="My thoughts on the new AI model (1/5): It's truly groundbreaking...")
        tweet3_thread_emoji = ScrapedTweet(tweet_id="t2", text_content="Let's dive deep into this topic. 🧵 First point...")
        tweet4_ambiguous = ScrapedTweet(tweet_id="a1", text_content="This is an interesting development that deserves more discussion.")
        
        tweets_to_test = [tweet1_standalone, tweet2_thread_indicator_text, tweet3_thread_emoji, tweet4_ambiguous]

        # Define LLM settings for the test (or let it use defaults from config)
        test_llm_settings = LLMSettings(service_preference="gemini", max_tokens=10, temperature=0.1) # Example

        for i, tweet_obj in enumerate(tweets_to_test):
            logger.info(f"\n--- Analyzing tweet {i+1} (ID: {tweet_obj.tweet_id}) ---")
            logger.info(f"Text: {tweet_obj.text_content}")
            is_thread = await analyzer.check_if_thread_with_llm(tweet_obj, custom_llm_settings=test_llm_settings)
            logger.info(f"LLM determined as thread: {is_thread}")
            # Update the tweet object (in a real scenario)
            tweet_obj.is_confirmed_thread = is_thread 
            logger.info(f"Updated tweet object: {tweet_obj.model_dump_json(indent=2, exclude_none=True)}")
            
    # To run this test, ensure LLM (e.g., Gemini) is configured in settings.json
    # asyncio.run(test_analyzer())
    # The main guard should be at the top level of the script execution block
    logger.info("To run the analyzer test, uncomment 'asyncio.run(test_analyzer())' in the main guard and ensure LLM services are configured.")
