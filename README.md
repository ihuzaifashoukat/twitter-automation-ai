
# Advanced Twitter Automation AI

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![Issues](https://img.shields.io/github/issues/ihuzaifashoukat/twitter-automation-ai)](https://github.com/ihuzaifashoukat/twitter-automation-ai/issues)
[![Forks](https://img.shields.io/github/forks/ihuzaifashoukat/twitter-automation-ai)](https://github.com/ihuzaifashoukat/twitter-automation-ai/network/members)
[![Stars](https://img.shields.io/github/stars/ihuzaifashoukat/twitter-automation-ai)](https://github.com/ihuzaifashoukat/twitter-automation-ai/stargazers)
[![Contributors](https://img.shields.io/github/contributors/ihuzaifashoukat/twitter-automation-ai)](https://github.com/ihuzaifashoukat/twitter-automation-ai/graphs/contributors)

**Advanced Twitter Automation AI** is a modular Python framework designed for scalable and configurable automation on X (Twitter).  
It supports multi-account management, browser automation with Selenium, stealth operation, LLM-based content generation and analysis, proxy control, and structured logging per account.

---

## Table of Contents

- [Features](#features)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Setup and Configuration](#setup-and-configuration)
- [Running the Application](#running-the-application)
- [Community Posting](#community-posting)
- [Keyword Engagement](#keyword-engagement)
- [Troubleshooting](#troubleshooting)
- [LLM Prompting](#llm-prompting)
- [Browser and Stealth](#browser-and-stealth)
- [Proxies](#proxies)
- [Cookies](#cookies)
- [Metrics and Logs](#metrics-and-logs)
- [Configuration Reference](#configuration-reference)
- [Development Notes](#development-notes)
- [Contributing](#contributing)
- [Code of Conduct](#code-of-conduct)
- [License](#license)
- [TODO / Future Enhancements](#todo--future-enhancements)

---

## Features

- **Multi-Account Automation** – Manage and automate multiple X accounts simultaneously.  
- **Content Scraping** – Collect tweets, engagement data, and user info by keyword or profile.  
- **Publishing Automation** – Post tweets, replies, and media with configurable triggers.  
- **LLM Integration** – OpenAI, Azure, and Gemini support for generation, summarization, and sentiment analysis.  
- **Engagement Automation** – Automate likes, retweets, replies, and engagement decisions using thresholds.  
- **Configurable Automation** – JSON-based per-account settings with global fallbacks.  
- **Browser Automation** – Selenium with optional undetected Chrome and stealth capabilities.  
- **Community Posting** – Post to X communities by ID or name.  
- **Proxy Management** – Individual or pooled proxies with hash or round-robin strategies.  
- **Structured Prompts** – JSON schema-first prompting for LLMs.  
- **Metrics and Logging** – Per-account JSON summaries and detailed JSONL logs.  
- **Modular Architecture** – Easily extend with new automation features.

---

## Technology Stack

- **Language:** Python 3.9+  
- **Automation:** Selenium, WebDriver Manager  
- **Networking:** Requests, Fake Headers  
- **Validation:** Pydantic  
- **LLM Integration:** LangChain, OpenAI SDK, Gemini SDK  
- **Stealth Layer:** undetected-chromedriver, selenium-stealth  
- **Configuration:** JSON, python-dotenv  

---

## Project Structure

```

twitter-automation-ai/
├── config/
│   ├── accounts.json
│   └── settings.json
├── src/
│   ├── core/
│   │   ├── browser_manager.py
│   │   ├── config_loader.py
│   │   └── llm_service.py
│   ├── features/
│   │   ├── scraper.py
│   │   ├── publisher.py
│   │   └── engagement.py
│   ├── utils/
│   │   ├── logger.py
│   │   ├── file_handler.py
│   │   ├── progress.py
│   │   └── scroller.py
│   ├── data_models.py
│   ├── main.py
│   └── **init**.py
├── .env
├── requirements.txt
├── .gitignore
├── LICENSE
├── CODE_OF_CONDUCT.md
├── CONTRIBUTING.md
└── README.md

````

---

## Prerequisites

- Python 3.9 or newer  
- Google Chrome or Firefox installed  
- Internet access for Selenium WebDriver

---

## Setup and Configuration

### 1. Clone the Repository

```bash
git clone https://github.com/ihuzaifashoukat/twitter-automation-ai
cd twitter-automation-ai
````

### 2. Create a Virtual Environment

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Accounts

Edit `config/accounts.json` to add your Twitter accounts, cookies, proxies, and optional community settings.

### 5. Configure Global Settings

Edit `config/settings.json` for LLM API keys, automation parameters, and browser options.

### 6. Environment Variables (Optional)

Add sensitive keys to a `.env` file in the project root:

```env
OPENAI_API_KEY="your_openai_api_key"
GEMINI_API_KEY="your_gemini_api_key"
```

---

## Running the Application

Execute the main orchestrator:

```bash
python src/main.py
```

The script iterates through all active accounts, applying the configured automation settings.

---

## Community Posting

To post into a community instead of a public timeline, enable `post_to_community` in `config/accounts.json` and provide either:

* `community_id`: the preferred identifier
* `community_name`: fallback visible name in the audience picker

Ensure the account has joined the community before posting.

---

## Keyword Engagement

Keyword-based actions are controlled through global or per-account configurations:

* **Replies**: `enable_keyword_replies`, `max_replies_per_keyword_run`
* **Likes**: `enable_liking_tweets`, `max_likes_per_run`
* **Retweets**: `enable_keyword_retweets`, `max_retweets_per_keyword_run`

Relevance filters and thresholds are optional and configurable.

---

## Troubleshooting

* **Click Interception:** The app auto-scrolls and retries using JS-click fallbacks.
* **Community Not Found:** Verify `community_id` or `community_name` and membership status.
* **WebDriver Issues:** Ensure drivers are installed or present in PATH.
* **API Errors:** Reduce request frequency or switch providers (OpenAI, Gemini, Azure).

---

## LLM Prompting

Structured JSON-based prompting with few-shot examples and schema constraints ensures consistent and parsable outputs.
OpenAI JSON mode is used when supported.

---

## Browser and Stealth

* Set `browser_settings.type` to `"chrome"` or `"firefox"`.
* For stealth, enable `use_undetected_chromedriver` and `enable_stealth`.
* Headless mode is supported.
* Randomized user agents improve anti-detection behavior.

---

## Proxies

* Each account can define its own `proxy`.
* Use `"pool:<name>"` to select from a configured pool.
* Rotation strategies include `hash` and `round_robin`.
* Environment variables can be interpolated inside proxy strings.

---

## Cookies

Provide a JSON file containing `x.com` cookies, referenced by `cookie_file_path` in each account configuration.

Example:

```json
[
  {
    "name": "auth_token",
    "value": "your_cookie_value",
    "domain": ".x.com"
  }
]
```

---

## Metrics and Logs

* **Metrics:** `data/metrics/<account_id>.json`
* **Logs:** `logs/accounts/<account_id>.jsonl`

Each log entry includes timestamps, actions, and statuses for transparency.

---

## Configuration Reference

A detailed configuration schema for `settings.json` and `accounts.json` is available in
`docs/CONFIG_REFERENCE.md`.

---

## Development Notes

* **Logging:** Controlled via `config/settings.json`, implemented in `src/utils/logger.py`.
* **Selectors:** Twitter’s DOM may change; update selectors in `scraper.py` or `publisher.py` as needed.
* **Extensibility:** New features can be added as independent modules in `src/features/`.

---

## Contributing

Contributions are welcome.
Read [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines and best practices.

---

## Code of Conduct

This project adheres to a [Code of Conduct](CODE_OF_CONDUCT.md) to maintain a respectful community.

---

## License

This project is licensed under the MIT License.
See [LICENSE](LICENSE) for details.

---

## TODO / Future Enhancements

* Web or GUI interface for account and settings management
* Enhanced retry and error handling
* Deeper analytics and dashboards
* Integration with third-party proxy services
* Advanced AI-driven engagement strategies

```

```

