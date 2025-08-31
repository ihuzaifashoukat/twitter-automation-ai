# Advanced Twitter Automation AI

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![Issues](https://img.shields.io/github/issues/ihuzaifashoukat/twitter-automation-ai)](https://github.com/ihuzaifashoukat/twitter-automation-ai/issues)
[![Forks](https://img.shields.io/github/forks/ihuzaifashoukat/twitter-automation-ai)](https://github.com/ihuzaifashoukat/twitter-automation-ai/network/members)
[![Stars](https://img.shields.io/github/stars/ihuzaifashoukat/twitter-automation-ai)](https://github.com/ihuzaifashoukat/twitter-automation-ai/stargazers)
[![Contributors](https://img.shields.io/github/contributors/ihuzaifashoukat/twitter-automation-ai)](https://github.com/ihuzaifashoukat/twitter-automation-ai/graphs/contributors)

**Advanced Twitter Automation AI** is a modular Python-based framework for automating X (Twitter) at scale. It supports multiple accounts, robust Selenium automation (with optional undetected Chrome + stealth), per‑account proxies and rotation, structured LLM generation/analysis (OpenAI, Azure OpenAI, Gemini), community posting, and per‑account metrics/logs.

## Table of Contents

- [Advanced Twitter Automation AI](#advanced-twitter-automation-ai)
  - [Table of Contents](#table-of-contents)
  - [Features](#features)
  - [Technology Stack](#technology-stack)
  - [Project Structure](#project-structure)
  - [Prerequisites](#prerequisites)
  - [Setup and Configuration](#setup-and-configuration)
    - [1. Clone Repository](#1-clone-repository)
    - [2. Create Virtual Environment](#2-create-virtual-environment)
    - [3. Install Dependencies](#3-install-dependencies)
    - [4. Configure Accounts (`config/accounts.json`)](#4-configure-accounts-configaccountsjson)
    - [5. Configure Global Settings (`config/settings.json`)](#5-configure-global-settings-configsettingsjson)
    - [6. Environment Variables (`.env`) (Optional)](#6-environment-variables-env-optional)
  - [Running the Application](#running-the-application)
  - [Development Notes](#development-notes)
  - [Contributing](#contributing)
  - [Code of Conduct](#code-of-conduct)
  - [License](#license)
  - [TODO / Future Enhancements](#todo--future-enhancements)

## Features

*   **Multi-Account Management:** Seamlessly manage and automate actions for multiple Twitter accounts.
*   **Content Scraping:**
    *   Scrape tweets based on keywords, user profiles, and news/research sites.
    *   Extract tweet content, user information, and engagement metrics.
*   **Content Publishing:**
    *   Post new tweets, including text and media.
    *   Reply to tweets based on various triggers.
    *   Repost (retweet) content from competitor profiles or based on engagement metrics.
*   **LLM Integration:**
    *   Utilize OpenAI (GPT models) and Google Gemini for:
        *   Generating tweet content and replies.
        *   Analyzing tweet threads and sentiment.
        *   Summarizing articles for posting.
    *   Flexible LLM preference settings at global and per-account levels.
*   **Engagement Automation:**
    *   Engage with tweets through likes, replies, and reposts.
    *   Analyze competitor activity and engage strategically.
*   **Configurable Automation:**
    *   Fine-grained control over automation parameters via JSON configuration files.
    *   Per-account overrides for keywords, target profiles, LLM settings, and action behaviors.
*   **Browser Automation:** Uses Selenium for interacting with Twitter, handling dynamic content and complex UI elements.
*   **Modular Design:** Easily extendable with new features and functionalities.
*   **Logging:** Comprehensive logging for monitoring and debugging.
*   **Community Posting:** Switch audience and post into configured communities (by ID or name).
*   **Stealth Mode (Chrome):** Optional undetected-chromedriver + selenium-stealth to reduce fingerprinting.
*   **Proxies:** Per-account proxies, named proxy pools, and rotation strategies (hash/round-robin) with env interpolation.
*   **LLM Structured Prompts:** Strict JSON prompting with few-shots, system prompts, and robust extraction.
*   **Metrics:** Per-account JSON summaries and JSONL event logs for observability.

## Technology Stack

*   **Programming Language:** Python 3.9+
*   **Browser Automation:** Selenium, WebDriver Manager
*   **HTTP Requests:** Requests
*   **Data Validation:** Pydantic
*   **LLM Integration:** Langchain (for Google GenAI), OpenAI SDK
*   **Stealth:** undetected-chromedriver, selenium-stealth (optional)
*   **Configuration:** JSON, python-dotenv
*   **Web Interaction:** Fake Headers (for mimicking browser headers)

## Project Structure

The project is organized as follows:

```
twitter-automation-ai/
├── config/
│   ├── accounts.json       # Configuration for multiple Twitter accounts
│   └── settings.json       # Global settings (API keys, automation parameters)
├── src/
│   ├── core/               # Core modules (browser, LLM, config)
│   │   ├── browser_manager.py
│   │   ├── config_loader.py
│   │   └── llm_service.py
│   ├── features/           # Modules for Twitter features (scraper, publisher, etc.)
│   │   ├── scraper.py
│   │   ├── publisher.py
│   │   └── engagement.py
│   ├── utils/              # Utility modules (logger, file handler, etc.)
│   │   ├── logger.py
│   │   ├── file_handler.py
│   │   ├── progress.py
│   │   └── scroller.py
│   ├── data_models.py      # Pydantic models for data structures
│   ├── main.py             # Main orchestrator script
│   └── __init__.py
├── .env                    # Environment variables (optional, for API keys)
├── requirements.txt        # Python dependencies
├── .gitignore              # Specifies intentionally untracked files
├── LICENSE                 # Project license
├── CODE_OF_CONDUCT.md      # Contributor Code of Conduct
├── CONTRIBUTING.md         # Guidelines for contributing
└── README.md               # This file
```

## Prerequisites

*   Python 3.9 or higher.
*   A modern web browser (e.g., Chrome, Firefox) compatible with Selenium.

## Setup and Configuration

Follow these steps to set up and run the project:

### Presets (Beginner-Friendly)

Quick-start templates are available in `presets/`.

- Settings presets: `presets/settings/*.json` (defaults, Chrome undetected, proxies hash/round-robin)
- Accounts presets: `presets/accounts/*.json` (growth, brand_safe, replies_first, engagement_light, community_posting)
- How to apply:
  - cp `presets/settings/beginner-chrome-undetected.json` `config/settings.json`
  - cp `presets/accounts/growth.json` `config/accounts.json`
  - Edit placeholders for API keys, cookie paths, and community IDs.
  - See `presets/README.md` and `data/README.md` (dummy cookies/proxies).

### 1. Clone Repository

```bash
git clone https://github.com/ihuzaifashoukat/twitter-automation-ai
cd twitter-automation-ai
```

### 2. Create Virtual Environment

It's highly recommended to use a virtual environment:

```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

### 4. Configure Accounts (`config/accounts.json`)

This file manages individual Twitter account configurations. It should be an array of account objects.

*   **Key Fields per Account:**
    *   `account_id`: A unique identifier for the account.
    *   `is_active`: Boolean, set to `true` to enable automation for this account.
    *   `cookie_file_path`: Path to a JSON file containing cookies for the account (e.g., `config/my_account_cookies.json`).
    *   `cookies`: Alternatively, an array of cookie objects can be provided directly.
    *   `proxy` (optional): Per-account proxy URL. Examples: `http://user:pass@host:port`, `socks5://host:port`.
    *   `post_to_community` (optional): When `true`, switch the audience to a community before posting.
    *   `community_id` (optional): Community ID used to select the audience (preferred).
    *   `community_name` (optional): Fallback visible name in the audience picker if ID selection fails.
    *   **Overrides:** You can specify per-account overrides for various settings like `target_keywords_override`, `competitor_profiles_override`, `llm_settings_override`, and `action_config_override`. If an override is not present, the global defaults from `config/settings.json` will be used.

*   **Example `config/accounts.json` entry:**
    ```json
    // Minimal example: ONLY add the community fields you need; keep your existing structure as-is.
    // Below shows adding community + (optional) proxy to one of your existing account objects:
    {
      "account_id": "your_existing_account_id",
      "is_active": true,
      "cookie_file_path": "config/your_existing_cookie_file.json",
      // ... all your existing fields remain unchanged ...
      "proxy": "http://127.0.0.1:8888",            // optional
      "post_to_community": true,                    // optional
      "community_id": "1737236915810627584",      // preferred when known
      "community_name": "One Piece"                // fallback by visible name
    }
    ```
    *(Refer to the example in the original README section for a more detailed structure if needed, or adapt based on current `data_models.py`.)*

*   **Obtaining Cookies:** Use browser developer tools (e.g., "EditThisCookie" extension) to export cookies for `x.com` after logging in. Save them as a JSON array of cookie objects if using `cookie_file_path`.
*   **Per-Account Proxy:** If set, the proxy overrides the global `browser_settings.proxy` for that account. Chrome uses `--proxy-server`; Firefox is configured via profile preferences (proxy auth prompts are not handled automatically).
*   **Community Posting:** When `post_to_community` is true, the publisher clicks the "Choose audience" button in the composer and selects your community using `community_id` (preferred) or `community_name` as a fallback, then posts.
*   Important: We do not require changing your existing `accounts.json` structure. Simply add the optional fields (`post_to_community`, `community_id`, `community_name`, and/or `proxy`) to the appropriate account objects.
*   For rewrite-based posting to communities or personal profiles, ensure each account has competitor sources configured via `competitor_profiles` (or `competitor_profiles_override` in your current structure). The scraper uses these as input for rewriting and posting.

### 5. Configure Global Settings (`config/settings.json`)

This file contains global configurations for the application.

*   **Key Sections:**
    *   `api_keys`: Store API keys for LLM services (e.g., `openai_api_key`, `gemini_api_key`).
    *   `twitter_automation`:
        *   `action_config`: Default behaviors for automation actions (e.g., `max_posts_per_run`, `min_likes_for_repost`).
        *   `response_interval_seconds`: Default delay between actions.
        *   `media_directory`: Path to store downloaded media.
        *   `analysis_config`: Enable/disable relevance filters per pipeline and thresholds.
          - `enable_relevance_filter.competitor_reposts` (bool), `thresholds.competitor_reposts_min` (0–1)
          - `enable_relevance_filter.likes` (bool), `thresholds.likes_min` (0–1)
        *   `engagement_decision`: If `enabled: true`, automatically chooses between repost/retweet/quote/like based on relevance and sentiment.
          - `use_sentiment`: include sentiment in decision
          - `thresholds.quote_min|retweet_min|repost_min`: relevance cutoffs (0–1)
    *   `logging`: Configuration for the logger.
*   `browser_settings`: Settings for Selenium WebDriver (e.g., `headless` mode).
    - `type`: `chrome` or `firefox`. For best anti-detection, use Chrome with `use_undetected_chromedriver`.
    - `use_undetected_chromedriver` (Chrome only): When `true`, uses `undetected-chromedriver` for stealthier automation.
    - `enable_stealth` (Chrome only): When `true` and `selenium-stealth` is installed, applies additional anti-detection tweaks.
    - `user_agent_generation`: `random` or `custom` with `custom_user_agent` string.
    - `proxy`: Global proxy (can be overridden per account).
    - `driver_options`: Extra Chrome/Firefox CLI options.
    - `page_load_timeout_seconds`, `script_timeout_seconds`, `window_size`.

LLM prompt engineering

- LLM prompts now use stronger, schema-first instructions for structured JSON with optional few-shot examples and hard character limits.
- `LLMService.generate_text` accepts an optional `system_prompt` and `messages` for OpenAI/Azure; Gemini concatenates system+user.
- `LLMService.generate_structured` adds `few_shots`, `system_prompt`, and `hard_character_limit` to guide safer, parsable outputs.
    *   `proxy_pools`: Named pools for per-account proxies. Use `"pool:<name>"` in account `proxy` to select from a pool.
    *   `proxy_pool_strategy`: `hash` (stable per-account) or `round_robin` (rotates across runs/accounts).
    *   `proxy_pool_state_file`: Persist file for round-robin counters (default `data/proxy_pools_state.json`).

*   **Important Note:** Content source lists like `target_keywords`, `competitor_profiles`, etc., are primarily managed per-account in `config/accounts.json`. The global `action_config` in `settings.json` defines default *how* actions run, which can be overridden per account.

### 6. Environment Variables (`.env`) (Optional)

For sensitive data like API keys, you can use a `.env` file in the project root. `python-dotenv` is included in `requirements.txt` to load these variables.

*   Create a `.env` file:
    ```env
    OPENAI_API_KEY="your_openai_api_key"
    GEMINI_API_KEY="your_gemini_api_key"
    # Add other sensitive variables as needed
    ```
    The application is designed to prioritize environment variables for API keys if available.

## Running the Application

Execute the main orchestrator script from the project root:

```bash
python src/main.py
```

The orchestrator will iterate through active accounts in `config/accounts.json` and perform actions based on their respective configurations and global settings.

## Community Posting

To post into a community instead of your public timeline, set the following on the account object in `config/accounts.json`:

- `post_to_community: true`
- Provide at least one of:
  - `community_id`: preferred (appears in URLs like `/i/communities/<id>`)
  - `community_name`: fallback by the visible label in the audience picker

How selection works:
- The app opens the “Choose audience” control, locates the audience menu container (dialog or `data-testid="HoverCard"`), and attempts to click your community.
- It scrolls the virtualized list to reveal off-screen items and uses JS-click fallbacks to avoid overlay interception.
- After selection, it posts using the chosen audience.

If it fails to select your community:
- Verify the account has joined the community and it appears under “My Communities”.
- Provide a DOM snapshot from the audience menu in a GitHub issue so selectors can be tuned.

## Keyword Engagement

Controls live under `twitter_automation.action_config` (globally) and per-account `action_config_override`:

- Replies: `enable_keyword_replies`, `max_replies_per_keyword_run`, optional recency `reply_only_to_recent_tweets_hours`.
- Likes: `enable_liking_tweets`, `max_likes_per_run`, `like_tweets_from_keywords` (defaults to account `target_keywords` when omitted).
- Retweets (new): `enable_keyword_retweets`, `max_retweets_per_keyword_run`.

Relevance filters (optional):
- `enable_relevance_filter_keyword_replies`, `relevance_threshold_keyword_replies`
- `enable_relevance_filter_likes`, `relevance_threshold_likes`

## Troubleshooting

- ElementClickInterceptedException or “not clickable”:
  - The app automatically scrolls into view, waits for the composer mask to disappear, and uses JS-click or Ctrl+Enter fallbacks.
  - If it persists, consider adding small delays or switching to Chrome (`browser_settings.type: "chrome"`).

- Community not selected:
  - Ensure `post_to_community: true` and set `community_id` (best) or `community_name`.
  - The audience list is virtualized; the app scrolls within the menu to reveal items. If your UI differs, open an issue with a DOM snippet.

- WebDriver downloads blocked or offline:
  - The app prefers local drivers (`chromedriver`, `geckodriver`) if found in PATH or via `chrome_driver_path`/`gecko_driver_path`. Install via your OS package manager or ensure they’re in PATH.

- Gemini errors (429/500):
  - Use `gemini-1.5-flash-latest`, reduce calls, or configure OpenAI/Azure.

## LLM Prompting

- Structured analysis and generation use strict schema-first prompts with robust JSON extraction. OpenAI JSON mode is attempted when available.
- Internally supports system prompts and few-shot examples for more controllable outputs.
- Content generation for posts composes final text (with optional hashtags) within 280 chars.

## Browser & Stealth

- Chrome: set `browser_settings.type` to `"chrome"` and enable `use_undetected_chromedriver`. Optional `enable_stealth` applies extra anti-detection tweaks.
- Firefox: standard Selenium with proxy prefs; auth prompts are not auto-handled.
- Headless: Chrome uses `--headless=new` for better parity. User-Agent randomized by default.

## Proxies

- Per-account `proxy` overrides global. Use `"pool:<name>"` to select from `browser_settings.proxy_pools`.
- Rotation strategies: `hash` (stable per-account) or `round_robin` (uses `data/proxy_pools_state.json`).
- Env interpolation: `${ENV_VAR}` inside proxy strings is expanded at runtime.

## Cookies

- Point `cookie_file_path` to a JSON array of cookies for `x.com`. The app navigates to `browser_settings.cookie_domain_url` before injecting cookies.
- Example file: `data/cookies/dummy_cookies_example.json`.

## Metrics & Logs

- Summary per account: `data/metrics/<account_id>.json` (counters for posts, replies, retweets, quote_tweets, likes, errors; last run timestamps)
- Structured events per account: `logs/accounts/<account_id>.jsonl` (JSON lines of each action attempt with metadata)

## Configuration Reference

See `docs/CONFIG_REFERENCE.md` for a concise schema of `config/settings.json` and `config/accounts.json`, including per-account `action_config_override` fields and decision thresholds.

## Development Notes

*   **Logging:** Detailed logs are output to the console. Configuration is in `config/settings.json` and managed by `src/utils/logger.py`.
*   **Selenium Selectors:** Twitter's (X.com) UI is subject to change. XPath and CSS selectors in `src/features/scraper.py` and `src/features/publisher.py` may require updates if the site structure changes.
*   **Error Handling:** The project includes basic error handling. Enhancements with more specific exception management and retry mechanisms are potential areas for improvement.
*   **Extensibility:** To add new features:
    1.  Define necessary data structures in `src/data_models.py`.
    2.  Create new feature modules within the `src/features/` directory.
    3.  Integrate the new module into the `TwitterOrchestrator` in `src/main.py`.

## Contributing

Contributions are welcome! Please read our [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute, report bugs, or suggest enhancements.

## Code of Conduct

To ensure a welcoming and inclusive environment, this project adheres to a [Code of Conduct](CODE_OF_CONDUCT.md). Please review and follow it in all your interactions with the project.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## TODO / Future Enhancements

*   GUI or web interface for managing accounts, settings, and monitoring.
*   Advanced error handling, including robust retry logic for network issues or UI changes.
*   Integration with proxy services for enhanced multi-account management and anonymity.
*   More detailed per-account activity logging and analytics.
*   Improved AI-driven content analysis and decision-making.
