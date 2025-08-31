Configuration Reference

Overview

- Summarizes key fields in `config/settings.json` and `config/accounts.json`.
- The app is tolerant of optional fields. Unknown keys are ignored by Pydantic models unless explicitly used.

settings.json

- api_keys
  - openai_api_key, gemini_api_key, azure_openai_api_key, azure_openai_endpoint, azure_openai_deployment, azure_api_version
- twitter_automation
  - response_interval_seconds: Base delay between actions.
  - media_directory: Folder for downloaded media.
  - processed_tweets_file: CSV for processed action keys.
  - analysis_config
    - enable_relevance_filter: { competitor_reposts, likes, keyword_replies }
    - thresholds: { competitor_reposts_min, likes_min, keyword_replies_min? }
  - engagement_decision
    - enabled, use_sentiment
    - thresholds: { quote_min, retweet_min, repost_min }
  - action_config
    - min_delay_between_actions_seconds, max_delay_between_actions_seconds
    - enable_competitor_reposts, max_posts_per_competitor_run, repost_only_tweets_with_media,
      min_likes_for_repost_candidate, min_retweets_for_repost_candidate,
      competitor_post_interaction_type, prompt_for_quote_tweet_from_competitor
    - enable_keyword_replies, max_replies_per_keyword_run, reply_only_to_recent_tweets_hours, avoid_replying_to_own_tweets
    - enable_keyword_retweets, max_retweets_per_keyword_run
    - enable_content_curation_posts, max_curated_posts_per_run
    - enable_liking_tweets, max_likes_per_run, like_tweets_from_keywords, like_tweets_from_feed
    - enable_thread_analysis
    - llm_settings_for_post, llm_settings_for_reply, llm_settings_for_thread_analysis
- logging: level, format, (optional file/console handlers)
- browser_settings
  - type: chrome|firefox, headless, user_agent_generation, custom_user_agent
  - proxy: global proxy URL (overridden per account)
  - proxy_pools: { name: [ "http://user:${ENV}@host:port", ... ] }
  - proxy_pool_strategy: hash|round_robin
  - proxy_pool_state_file: path for round-robin counters
  - window_size, driver_options, timeouts
  - use_undetected_chromedriver: bool (Chrome only)
  - enable_stealth: bool (Chrome only)
  - cookie_domain_url: base URL for cookie domain navigation (e.g., https://x.com)
  - chrome_driver_path / gecko_driver_path (optional): use a specific local driver binary. The app prefers local drivers if found.

accounts.json (per account)

- account_id: string
- is_active: bool
- cookies: [ cookie objects ] (optional)
- cookie_file_path: string (recommended)
- proxy: URL or "pool:<pool_name>"
- post_to_community: bool, community_id: string?, community_name: string?
- target_keywords or target_keywords_override: [strings]
- competitor_profiles or competitor_profiles_override: [profile URLs] (required for rewrite-based posting)
- news_sites(_override): [URLs] (optional)
- research_paper_sites(_override): [URLs] (optional)
- llm_settings_override: { service_preference, model_name_override, max_tokens, temperature }
- action_config_override: ActionConfig subset to override defaults, including:
  - enable_competitor_reposts, max_posts_per_competitor_run, repost_only_tweets_with_media,
    min_likes_for_repost_candidate, min_retweets_for_repost_candidate
  - enable_keyword_replies, max_replies_per_keyword_run, reply_only_to_recent_tweets_hours, avoid_replying_to_own_tweets
  - enable_content_curation_posts, max_curated_posts_per_run
  - enable_liking_tweets, max_likes_per_run
  - enable_thread_analysis
  - Relevance filters: enable_relevance_filter_(competitor_reposts|likes|keyword_replies) and relevance_threshold_*
  - Decision logic: enable_engagement_decision, use_sentiment_in_decision,
    decision_quote_min, decision_retweet_min, decision_repost_min
  - LLM action settings: llm_settings_for_post / reply / thread_analysis
  - Keyword engagement: enable_keyword_retweets, max_retweets_per_keyword_run

Notes

- Unknown fields are generally ignored; keep to the provided keys for predictable behavior.
- For pools with env vars, ensure your shell exports them before running (`export RESI_PASS=...`).
- Cookies must match `cookie_domain_url` domain; the app navigates there before injection.
- Community posting: the app opens the “Choose audience” menu and selects by `community_id` (preferred) or visible `community_name`. It scrolls virtualized lists and uses JS-click fallbacks when needed.
  - If selection still fails, confirm the account is a member of the community and that it appears under “My Communities”.
  - UI can change; open an issue with a DOM snapshot if selectors need tuning.
