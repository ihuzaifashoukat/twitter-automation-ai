# Advanced Twitter Automation AI

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![Issues](https://img.shields.io/github/issues/ihuzaifashoukat/twitter-automation-ai)](https://github.com/ihuzaifashoukat/twitter-automation-ai/issues)
[![Forks](https://img.shields.io/github/forks/ihuzaifashoukat/twitter-automation-ai)](https://github.com/ihuzaifashoukat/twitter-automation-ai/network/members)
[![Stars](https://img.shields.io/github/stars/ihuzaifashoukat/twitter-automation-ai)](https://github.com/ihuzaifashoukat/twitter-automation-ai/stargazers)
[![Contributors](https://img.shields.io/github/contributors/ihuzaifashoukat/twitter-automation-ai)](https://github.com/ihuzaifashoukat/twitter-automation-ai/graphs/contributors)

**Advanced Twitter Automation AI** is a modular Python-based framework designed for automating a wide range of Twitter (now X.com) interactions. It supports multiple accounts and leverages Selenium for robust browser automation, with optional integration of Large Language Models (LLMs) like OpenAI's GPT and Google's Gemini for intelligent content generation, analysis, and engagement.

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

## Technology Stack

*   **Programming Language:** Python 3.9+
*   **Browser Automation:** Selenium, WebDriver Manager
*   **HTTP Requests:** Requests
*   **Data Validation:** Pydantic
*   **LLM Integration:** Langchain (for Google GenAI), OpenAI SDK
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
    *   **Overrides:** You can specify per-account overrides for various settings like `target_keywords_override`, `competitor_profiles_override`, `llm_settings_override`, and `action_config_override`. If an override is not present, the global defaults from `config/settings.json` will be used.

*   **Example `config/accounts.json` entry:**
    ```json
    [
      {
        "account_id": "tech_blogger_alpha",
        "is_active": true,
        "cookie_file_path": "config/tech_blogger_alpha_cookies.json",
        "target_keywords_override": ["AI ethics", "future of work", "data privacy"],
        "llm_settings_override": {
          "service_preference": "openai",
          "model_name_override": "gpt-4o"
        },
        "action_config_override": {
          "enable_keyword_replies": true,
          "max_replies_per_keyword_run": 3
        }
      }
      // ... more accounts
    ]
    ```
    *(Refer to the example in the original README section for a more detailed structure if needed, or adapt based on current `data_models.py`.)*

*   **Obtaining Cookies:** Use browser developer tools (e.g., "EditThisCookie" extension) to export cookies for `x.com` after logging in. Save them as a JSON array of cookie objects if using `cookie_file_path`.

### 5. Configure Global Settings (`config/settings.json`)

This file contains global configurations for the application.

*   **Key Sections:**
    *   `api_keys`: Store API keys for LLM services (e.g., `openai_api_key`, `gemini_api_key`).
    *   `twitter_automation`:
        *   `action_config`: Default behaviors for automation actions (e.g., `max_posts_per_run`, `min_likes_for_repost`).
        *   `response_interval_seconds`: Default delay between actions.
        *   `media_directory`: Path to store downloaded media.
    *   `logging`: Configuration for the logger.
    *   `browser_settings`: Settings for Selenium WebDriver (e.g., `headless` mode).

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