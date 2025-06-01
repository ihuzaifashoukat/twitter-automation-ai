# Advanced Twitter Automation AI

This project provides a modular framework for automating various Twitter interactions, including scraping, posting, replying, and engaging with content, supporting multiple accounts.

## Project Structure

```
twitter-automation-ai/
├── config/
│   ├── accounts.json       # Configuration for multiple Twitter accounts (cookies, API keys if needed)
│   └── settings.json       # Global settings (API keys, automation parameters, logging)
├── src/
│   ├── core/               # Core modules (browser management, LLM service, config loading)
│   │   ├── browser_manager.py
│   │   ├── config_loader.py
│   │   └── llm_service.py
│   ├── features/           # Modules for specific Twitter features (scraping, publishing, engagement)
│   │   ├── scraper.py
│   │   ├── publisher.py
│   │   └── engagement.py
│   ├── utils/              # Utility modules (logging, file handling, etc.)
│   │   ├── logger.py
│   │   ├── file_handler.py
│   │   ├── progress.py
│   │   └── scroller.py
│   ├── data_models.py      # Pydantic models for data structures
│   ├── main.py             # Main orchestrator script to run the automation
│   ├── __init__.py
│   ├── agent.py            # Old script (to be removed or archived)
│   ├── app.py              # Old script (to be removed or archived)
│   ├── tweet.py            # Old script (to be removed or archived)
│   └── twitter_scraper.py  # Old script (to be removed or archived)
├── .env                    # Environment variables (e.g., API keys, if not in settings.json)
├── requirements.txt        # Python dependencies
├── processed_tweets_log.csv # Log of processed tweets (path configurable in settings.json)
├── media_files/            # Directory for downloaded media (path configurable in settings.json)
└── README.md
```

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd twitter-automation-ai
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Accounts:**
    *   Edit `config/accounts.json`. This file should be an array of account objects.
    *   For each account, you need to provide cookie information. The `BrowserManager` is set up to load cookies from a JSON file specified by `cookie_file_path` within each account object, or directly as a list of cookie objects under the `cookies` key.
    *   **Example `config/accounts.json` entry demonstrating per-account overrides:**
        ```json
        [
          {
            "account_id": "tech_news_aggregator_account",
            "is_active": true,
            "cookie_file_path": "tech_news_cookies.json", // Place in 'config/' or provide absolute path
            "target_keywords_override": ["AI breakthroughs", "quantum computing", "future of tech"],
            "competitor_profiles_override": ["https://x.com/TechCrunch", "https://x.com/verge"],
            "news_sites_override": ["https://www.wired.com/category/science/ai", "https://arstechnica.com/information-technology/"],
            "research_paper_sites_override": ["https://arxiv.org/list/cs.AI/new", "https://distill.pub"],
            "llm_settings_override": { // Account-specific general LLM preference
              "service_preference": "openai",
              "model_name_override": "gpt-4o",
              "max_tokens": 180,
              "temperature": 0.75
            },
            "action_config_override": { // Account-specific overrides for automation behaviors
              "enable_competitor_reposts": true,
              "max_posts_per_competitor_run": 2,
              "min_likes_for_repost_candidate": 5,
              "enable_keyword_replies": true,
              "max_replies_per_keyword_run": 1,
              "enable_thread_analysis": true,
              "llm_settings_for_post": { // LLM settings specifically for posts by this account
                "service_preference": "openai",
                "model_name_override": "gpt-4o",
                "max_tokens": 200,
                "temperature": 0.7
              },
               "llm_settings_for_thread_analysis": {
                 "service_preference": "gemini", // Use Gemini for thread analysis for this account
                 "model_name_override": "gemini-1.5-flash-latest",
                 "max_tokens": 50,
                 "temperature": 0.1
               }
            }
          },
          {
            "account_id": "general_commentator_account",
            "is_active": true,
            "cookie_file_path": "general_cookies.json",
            // This account uses fewer overrides. For any setting not specified here
            // (e.g., target_keywords_override, competitor_profiles_override, general llm_settings_override),
            // it will use the global defaults defined in 'config/settings.json'.
            "cookies": [ // Alternatively, provide cookies directly instead of cookie_file_path
              {"name": "auth_token", "value": "your_auth_token_for_general", "domain": ".x.com"},
              {"name": "ct0", "value": "your_ct0_token_for_general", "domain": ".x.com"}
            ]
          },
          {
            "account_id": "inactive_test_account", // Example of an inactive account
            "is_active": false,
            "cookie_file_path": "config/inactive_account_cookies.json"
            // This account will be skipped by the orchestrator.
          }
        ]
        ```
            "account_id": "inactive_test_account", // Example of an inactive account
            "is_active": false,
            "cookie_file_path": "config/inactive_account_cookies.json"
            // This account will be skipped by the orchestrator.
          }
        ]
        ```
    *   **Important Note on Content Sources & Action Configuration:**
        *   Lists like `target_keywords`, `competitor_profiles`, `news_sites`, and `research_paper_sites` **must now be defined per account** in `config/accounts.json` if you want those features to be active for that account. There are no longer global defaults for these lists in `config/settings.json`.
        *   The `action_config` (which controls *how* actions are performed) can be defined globally in `config/settings.json` (under `twitter_automation.action_config`). An account can then have its own `action_config` object in `config/accounts.json` to override these global action settings. If an account does not have an `action_config`, it will use the global one.
    *   **To get cookies:** You can use browser developer tools (e.g., EditThisCookie extension) to export cookies for `x.com` after logging in. Save them in the specified JSON file format (an array of cookie objects, each with `name`, `value`, `domain`, etc.) if using `cookie_file_path`.

5.  **Configure Global Settings (`config/settings.json`):**
    *   This file now primarily contains:
        *   API keys for LLM services (`api_keys`).
        *   Global default `action_config` under `twitter_automation` (which defines *how* actions run by default).
        *   Other general `twitter_automation` settings like `response_interval_seconds`, `media_directory`.
        *   `logging` and `browser_settings`.
    *   **Note:** Global lists for `competitor_profiles`, `news_sites`, `research_paper_sites`, and `target_keywords` have been removed from this file. These must be defined per-account in `config/accounts.json`.

6.  **Environment Variables (Optional):**
    *   If you prefer, some API keys (like `GEMINI_API_KEY`) can be loaded from a `.env` file at the project root. The `LLMService` and `ConfigLoader` can be adapted to prioritize environment variables. `python-dotenv` is included in `requirements.txt`.
    *   Create a `.env` file in the project root:
        ```
        GEMINI_API_KEY="your_gemini_api_key"
        # Add other keys as needed
        ```

## Running the Application

Execute the main orchestrator script:

```bash
python src/main.py
```

The orchestrator will loop through the active accounts defined in `config/accounts.json` and perform actions based on the configurations in `config/settings.json`.

## Development Notes

*   **Logging:** Logs are output to the console. Configuration is in `config/settings.json` and handled by `src/utils/logger.py`.
*   **Selenium Selectors:** Twitter's (X.com) UI changes frequently. Selenium XPath selectors in `scraper.py` and `publisher.py` might need updates if the site structure changes.
*   **Error Handling:** The current implementation has basic error handling. Robustness can be improved with more specific exception handling and retry mechanisms.
*   **Adding New Features:**
    *   Define data structures in `src/data_models.py`.
    *   Create new feature modules in `src/features/`.
    *   Integrate into the `TwitterOrchestrator` in `src/main.py`.

## TODO / Future Enhancements

*   GUI or web interface for managing accounts and settings.
*   Advanced error handling and retry logic for network issues or UI changes.
*   Support for login via username/password in `BrowserManager` (requires careful handling of credentials).
*   Integration with proxy services for multi-account management.
*   More detailed per-account activity logging.
